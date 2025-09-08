from datetime import datetime, timedelta
import pytz
from app import mongo
from bson import ObjectId
from typing import Dict, List, Optional, Union, Any

# Set Indian timezone
IST = pytz.timezone('Asia/Kolkata')

class Budget:
    PERIODS = ['daily', 'weekly', 'monthly', 'yearly']
    
    @classmethod
    def create_budget(cls, user_id, category, amount, period, start_date, end_date=None, note=None):
        now = datetime.now(IST)
        
        # Convert start_date to datetime object in IST
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=IST)
        else:
            start_dt = start_date.astimezone(IST) if start_date.tzinfo else start_date.replace(tzinfo=IST)
        
        # Handle end_date based on period if not provided
        if not end_date and period != 'custom':
            if period == 'daily':
                end_dt = (start_dt + timedelta(days=1)).replace(hour=23, minute=59, second=59)
            elif period == 'weekly':
                end_dt = (start_dt + timedelta(weeks=1)).replace(hour=23, minute=59, second=59)
            elif period == 'monthly':
                next_month = start_dt.replace(day=28) + timedelta(days=4)
                end_dt = (next_month - timedelta(days=next_month.day)).replace(hour=23, minute=59, second=59)
            elif period == 'yearly':
                end_dt = start_dt.replace(year=start_dt.year + 1, month=12, day=31, hour=23, minute=59, second=59)
        else:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=IST) if end_date else None
            
        # Ensure end_date is at the end of the day
        if end_dt:
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        
        # Create budget with initial values
        budget = {
            'user_id': ObjectId(user_id),
            'category': category,
            'amount': float(amount),
            'period': period,
            'start_date': start_dt,
            'end_date': end_dt,
            'note': note,
            'created_at': now,
            'updated_at': now,
            'spent': 0.0,
            'remaining': float(amount),
            'transactions': []
        }
        
        # Add existing transactions to the budget
        cls._add_existing_transactions(budget, user_id, category, start_dt, end_dt)
        
        # Update remaining amount
        budget['remaining'] = budget['amount'] - budget['spent']
        result = mongo.db.budgets.insert_one(budget)
        return str(result.inserted_id)
    
    @classmethod
    def _add_existing_transactions(cls, budget: Dict[str, Any], user_id: str, category: str, 
                                 start_date: datetime, end_date: datetime) -> None:
        """
        Add existing transactions to the budget that fall within the date range
        and match the category.
        """
        query = {
            'user_id': ObjectId(user_id),
            'category': category,
            'type': 'expense',  # Only include expense transactions
            'date': {
                '$gte': start_date,
                '$lte': end_date or datetime.max.replace(tzinfo=IST)
            }
        }
        
        # Find all matching transactions
        transactions = list(mongo.db.transactions.find(query))
        
        # Add transactions to budget and calculate total spent
        total_spent = 0.0
        for tx in transactions:
            if tx['_id'] not in [t.get('_id') for t in budget['transactions']]:
                budget['transactions'].append({
                    'transaction_id': str(tx['_id']),
                    'amount': float(tx['amount']),
                    'date': tx['date'],
                    'note': tx.get('note', '')
                })
                total_spent += float(tx['amount'])
        
        # Update budget's spent amount
        budget['spent'] = round(total_spent, 2)
        
        # Ensure remaining can't be negative
        budget['remaining'] = max(0, budget['amount'] - budget['spent'])
    
    @staticmethod
    def get_user_budgets(user_id):
        now = datetime.now(IST)
        budgets = list(mongo.db.budgets.find({
            'user_id': ObjectId(user_id),
            'start_date': {'$lte': now},
            '$or': [
                {'end_date': None},
                {'end_date': {'$gte': now}}
            ]
        }).sort([('start_date', -1)]))
        
        # Convert Decimal128 to float for all numeric fields
        for budget in budgets:
            for key, value in budget.items():
                if isinstance(value, float):
                    budget[key] = value
                elif key == '_id':
                    budget[key] = str(value)
        
        return budgets
    
    @staticmethod
    def get_budget_by_id(budget_id):
        budget = mongo.db.budgets.find_one({'_id': ObjectId(budget_id)})
        if budget:
            # Convert Decimal128 to float for numeric fields
            for key, value in budget.items():
                if isinstance(value, float):
                    budget[key] = value
                elif key == '_id':
                    budget[key] = str(value)
        return budget
    
    @staticmethod
    def get_budget_by_category(user_id, category, period=None, date=None):
        date = date or datetime.now(IST)
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=IST)
            
        query = {
            'user_id': ObjectId(user_id), 
            'category': category,
            'start_date': {'$lte': date},
            '$or': [
                {'end_date': None},
                {'end_date': {'$gte': date}}
            ]
        }
        if period:
            query['period'] = period
            
        # For monthly budgets, check if the transaction date falls within the budget period
        if period == 'monthly':
            query['$expr'] = {
                '$and': [
                    {'$eq': [{'$month': '$start_date'}, date.month]},
                    {'$eq': [{'$year': '$start_date'}, date.year]}
                ]
            }
            
        budget = mongo.db.budgets.find_one(query)
        if budget:
            # Convert Decimal128 to float for numeric fields
            for key, value in budget.items():
                if isinstance(value, float):
                    budget[key] = value
                elif key == '_id':
                    budget[key] = str(value)
        return budget
    
    @staticmethod
    def update_budget(budget_id, update_data):
        update_data['updated_at'] = datetime.now(IST)
        
        # Handle date updates
        if 'start_date' in update_data and isinstance(update_data['start_date'], str):
            update_data['start_date'] = datetime.strptime(update_data['start_date'], '%Y-%m-%d').replace(tzinfo=IST)
        if 'end_date' in update_data and update_data['end_date'] and isinstance(update_data['end_date'], str):
            update_data['end_date'] = datetime.strptime(update_data['end_date'], '%Y-%m-%d').replace(tzinfo=IST)
            
        if 'amount' in update_data:
            update_data['amount'] = float(update_data['amount'])
            # Recalculate remaining amount
            budget = mongo.db.budgets.find_one({'_id': ObjectId(budget_id)})
            if budget:
                spent = budget.get('spent', 0.0)
                update_data['remaining'] = float(update_data['amount']) - spent
        
        return mongo.db.budgets.update_one(
            {'_id': ObjectId(budget_id)},
            {'$set': update_data}
        )
        
    @classmethod
    def update_budget_with_transaction(
        cls,
        budget_id: str,
        transaction_data: Dict[str, any],
        is_new: bool = True
    ) -> bool:
        """
        Update budget when a transaction is added/updated/deleted
        
        Args:
            budget_id: ID of the budget to update
            transaction_data: Dictionary containing transaction details
            is_new: Whether this is a new transaction (True) or an update/deletion (False)
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Convert string amount to float if needed
            amount = transaction_data.get('amount')
            if not isinstance(amount, float):
                amount = float(amount)
                
            # Get the transaction date or use current time
            transaction_date = transaction_data.get('date', datetime.now(IST))
            if isinstance(transaction_date, str):
                transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').replace(tzinfo=IST)
            
            # Get the budget
            budget = mongo.db.budgets.find_one({
                '_id': ObjectId(budget_id)
            })
            
            if not budget:
                print(f"Budget not found: {budget_id}")
                return False
                
            # Initialize spent and transactions if they don't exist
            current_spent = budget.get('spent', 0.0)
            transactions = budget.get('transactions', [])
            
            # Find the transaction if it exists
            transaction_id = str(transaction_data.get('_id') or transaction_data.get('id', ''))
            existing_transaction = next(
                (t for t in transactions if str(t.get('id')) == transaction_id), 
                None
            )
            
            # Calculate new spent amount
            if is_new and not existing_transaction:
                # Add new transaction
                new_spent = current_spent + amount
                transaction_update = {
                    'id': ObjectId(transaction_id) if transaction_id else ObjectId(),
                    'amount': amount,
                    'date': transaction_date,
                    'note': transaction_data.get('note', '')
                }
                update_operation = {'$push': {'transactions': transaction_update}}
                
            elif not is_new and existing_transaction:
                # Remove existing transaction amount
                old_amount = existing_transaction.get('amount', 0.0)
                new_spent = current_spent - old_amount
                
                # If we're not deleting, add the new amount
                if transaction_data.get('_deleted') is not True:
                    new_spent += amount
                    
                    # Update the transaction
                    update_operation = {
                        '$set': {
                            'transactions.$.amount': amount,
                            'transactions.$.date': transaction_date,
                            'transactions.$.note': transaction_data.get('note', '')
                        }
                    }
                else:
                    # Remove the transaction
                    update_operation = {
                        '$pull': {
                            'transactions': {'id': ObjectId(transaction_id)}
                        }
                    }
            else:
                print(f"Transaction update case not handled: is_new={is_new}, exists={existing_transaction is not None}")
                return False
            
            # Calculate remaining amount
            budget_amount = budget.get('amount', 0.0)
            remaining = budget_amount - new_spent
            
            # Update the budget
            update_operation['$set'] = update_operation.get('$set', {})
            update_operation['$set'].update({
                'spent': new_spent,
                'remaining': remaining,
                'updated_at': datetime.now(IST)
            })
            
            result = mongo.db.budgets.update_one(
                {'_id': ObjectId(budget_id)},
                update_operation
            )
            
            if result.modified_count > 0:
                print(f"Updated budget {budget_id} - Spent: {new_spent}, Remaining: {remaining}")
                return True
            return False
            
        except Exception as e:
            print(f"Error updating budget: {str(e)}")
            return False
    
    @staticmethod
    def delete_budget(budget_id):
        return mongo.db.budgets.delete_one({'_id': ObjectId(budget_id)})