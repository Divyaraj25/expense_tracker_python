from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.budget import Budget
from app.utils.validators import validate_date, validate_amount
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
import pytz
from bson import ObjectId

TIMEZONE = pytz.timezone('Asia/Kolkata')

def _update_account_balances(transaction_data: Dict[str, Any], reverse: bool = False) -> None:
    """Update account balances based on transaction data.
    
    Args:
        transaction_data: The transaction data
        reverse: If True, reverses the effect on account balances
    """
    if not transaction_data or 'type' not in transaction_data:
        return
        
    amount = float(transaction_data.get('amount', 0))
    if amount <= 0:
        return
        
    # For reversing a transaction, we just flip the sign of the amount
    amount = -amount if reverse else amount
    
    # Handle different transaction types
    try:
        if transaction_data['type'] == 'expense' and 'account_from' in transaction_data:
            Account.update_balance(transaction_data['account_from'], -amount)  # Decrease source account
        elif transaction_data['type'] == 'income' and 'account_to' in transaction_data:
            Account.update_balance(transaction_data['account_to'], amount)  # Increase destination account
        elif transaction_data['type'] == 'transfer' and all(k in transaction_data for k in ['account_from', 'account_to']):
            Account.update_balance(transaction_data['account_from'], -amount)  # Decrease source
            Account.update_balance(transaction_data['account_to'], amount)  # Increase destination
    except Exception as e:
        current_app.logger.error(f"Error updating account balances: {str(e)}")
        # Don't raise the exception to avoid failing the transaction operation
        pass

def _format_transaction_dates(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to format transaction dates for response"""
    if not transaction:
        return transaction
        
    # Create a copy to avoid modifying the original
    formatted = dict(transaction)
    
    # Format date and time
    if 'date' in formatted and formatted['date']:
        if isinstance(formatted['date'], str):
            try:
                # If it's already a string in ISO format, parse it first
                formatted['date'] = datetime.fromisoformat(formatted['date'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                # If parsing fails, leave it as is
                pass
        
        if isinstance(formatted['date'], datetime):
            # Convert to IST
            ist = pytz.timezone('Asia/Kolkata')
            if formatted['date'].tzinfo is None:
                # If naive datetime, assume it's in UTC
                formatted['date'] = pytz.utc.localize(formatted['date'])
            # Convert to IST
            formatted['date'] = formatted['date'].astimezone(ist)
            
            # Format date and time for the frontend
            formatted['date_str'] = formatted['date'].strftime('%Y-%m-%d')
            formatted['time_str'] = formatted['date'].strftime('%H:%M')
            
            # Add the full date and time in a human-readable format
            formatted['date_full'] = formatted['date'].strftime('%b %d, %Y')
            formatted['time'] = formatted['date'].strftime('%I:%M %p')
            
            # Also include a formatted datetime string
            formatted['formatted_date'] = f"{formatted['date_full']} at {formatted['time']}"
    
    # Convert ObjectId to string for JSON serialization
    if '_id' in formatted:
        formatted['id'] = str(formatted.pop('_id'))
    if 'user_id' in formatted:
        formatted['user_id'] = str(formatted['user_id'])
    if 'account_from' in formatted and formatted['account_from'] and isinstance(formatted['account_from'], ObjectId):
        formatted['account_from'] = str(formatted['account_from'])
    if 'account_to' in formatted and formatted['account_to'] and isinstance(formatted['account_to'], ObjectId):
        formatted['account_to'] = str(formatted['account_to'])
    
    return formatted

def _update_budget_for_transaction(
    transaction: Dict[str, Any], 
    old_transaction: Optional[Dict[str, Any]] = None,
    is_deleted: bool = False
) -> None:
    """
    Update the relevant budget when a transaction is created, updated, or deleted.
    
    Args:
        transaction: The transaction data
        old_transaction: The old transaction data (for updates)
        is_deleted: Whether this is a delete operation
    """
    try:
        from app import mongo
        
        # Get the transaction date (use current time if not provided)
        transaction_date = transaction.get('date')
        if not transaction_date:
            transaction_date = datetime.now(pytz.timezone('Asia/Kolkata'))
        elif isinstance(transaction_date, str):
            # Parse string date if needed
            try:
                transaction_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                transaction_date = datetime.now(pytz.timezone('Asia/Kolkata'))
        
        # Only process expense transactions for budget updates
        if transaction.get('type') != 'expense':
            return
            
        category = transaction.get('category')
        if not category:
            return
            
        user_id = transaction.get('user_id')
        if not user_id:
            return
            
        # For updates, if the category or date changed, we need to update both old and new budgets
        if old_transaction and old_transaction.get('type') == 'expense':
            old_category = old_transaction.get('category')
            old_date = old_transaction.get('date')
            
            if old_category != category or old_date != transaction_date:
                # Remove from old budget
                old_budget = mongo.db.budgets.find_one({
                    'user_id': ObjectId(user_id),
                    'category': old_category,
                    'start_date': {'$lte': old_date},
                    '$or': [
                        {'end_date': None},
                        {'end_date': {'$gte': old_date}}
                    ]
                })
                
                if old_budget:
                    Budget.update_budget_with_transaction(
                        str(old_budget['_id']),
                        {
                            '_id': transaction.get('_id') or transaction.get('id'),
                            'amount': old_transaction.get('amount', 0),
                            'category': old_category,
                            'date': old_date,
                            'description': old_transaction.get('description', ''),
                            '_deleted': True
                        },
                        is_new=False
                    )
        
        # Find the relevant budget for this transaction
        # First try to find a budget for the specific category and date
        budget = mongo.db.budgets.find_one({
            'user_id': ObjectId(user_id),
            'category': category,
            'start_date': {'$lte': transaction_date},
            '$or': [
                {'end_date': None},
                {'end_date': {'$gte': transaction_date}}
            ]
        })
        
        if not budget:
            # If no budget found for this category, try to find a general budget (no category)
            budget = mongo.db.budgets.find_one({
                'user_id': ObjectId(user_id),
                'category': None,
                'start_date': {'$lte': transaction_date},
                '$or': [
                    {'end_date': None},
                    {'end_date': {'$gte': transaction_date}}
                ]
            })
        
        if budget:
            # Update the budget with this transaction
            Budget.update_budget_with_transaction(
                str(budget['_id']),
                {
                    '_id': transaction.get('_id') or transaction.get('id'),
                    'amount': transaction.get('amount', 0),
                    'category': category,
                    'date': transaction_date,
                    'description': transaction.get('description', ''),
                    '_deleted': is_deleted
                },
                is_new=not old_transaction and not is_deleted
            )
            
    except Exception as e:
        current_app.logger.error(f"Error updating budget for transaction: {str(e)}")
        # Don't raise the exception to avoid failing the transaction operation
        pass

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def handle_transactions():
    current_user = get_jwt_identity()
    
    if request.method == 'GET':
        try:
            limit = int(request.args.get('limit', 50))
            skip = int(request.args.get('skip', 0))
            type_filter = request.args.get('type')
            category_filter = request.args.get('category')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            filters = {}
            if type_filter:
                filters['type'] = type_filter
            if category_filter:
                filters['category'] = category_filter
            if start_date and end_date and validate_date(start_date) and validate_date(end_date):
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                filters['date'] = {
                    '$gte': TIMEZONE.localize(start_dt),
                    '$lte': TIMEZONE.localize(end_dt)
                }
            
            transactions = Transaction.get_user_transactions(current_user, limit, skip, filters)
            return jsonify([_format_transaction_dates(t) for t in transactions]), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 400
    
    elif request.method == 'POST':
        data = request.get_json()
        transaction_type = data.get('type')
        amount = data.get('amount')
        category = data.get('category')
        description = data.get('description')
        account_from = data.get('account_from')
        account_to = data.get('account_to')
        date_str = data.get('date')

        # Validate required fields
        if not all([transaction_type, amount, category, description]):
            return jsonify({'message': 'Missing required fields'}), 400

        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError('Amount must be greater than 0')
        except (ValueError, TypeError):
            return jsonify({'message': 'Invalid amount'}), 400

        # Validate type
        if transaction_type not in ['income', 'expense', 'transfer']:
            return jsonify({'message': 'Invalid transaction type'}), 400

        # Validate accounts based on type
        if transaction_type == 'expense' and not account_from:
            return jsonify({'message': 'Source account is required for expenses'}), 400
        if transaction_type == 'income' and not account_to:
            return jsonify({'message': 'Destination account is required for income'}), 400
        if transaction_type == 'transfer' and (not account_from or not account_to):
            return jsonify({'message': 'Both source and destination accounts are required for transfers'}), 400

        # Parse and validate date and time
        time_str = data.get('time')
        if not time_str:
            # Default to current time if not provided
            time_str = datetime.now(TIMEZONE).strftime('%H:%M')
            
        transaction_date = None
        if date_str:
            try:
                # Parse date and combine with time
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                time_obj = datetime.strptime(time_str, '%H:%M').time()
                transaction_date = datetime.combine(date_obj, time_obj)
                # Make the datetime timezone aware (IST)
                transaction_date = TIMEZONE.localize(transaction_date)
                # Convert to UTC for storage
                transaction_date = transaction_date.astimezone(pytz.UTC)
            except ValueError as e:
                return jsonify({'message': f'Invalid date or time format. Use YYYY-MM-DD and HH:MM. Error: {str(e)}'}), 400

        try:
            # Prepare transaction data
            transaction_data = {
                'user_id': current_user,
                'type': transaction_type,
                'amount': amount,
                'category': category,
                'description': description,
                'date': transaction_date or datetime.now(pytz.UTC)
            }
            
            # Add account references based on transaction type
            if transaction_type == 'expense':
                transaction_data['account_from'] = account_from
            elif transaction_type == 'income':
                transaction_data['account_to'] = account_to
            else:  # transfer
                transaction_data['account_from'] = account_from
                transaction_data['account_to'] = account_to
            
            # Create the transaction
            result = Transaction.create_transaction(**transaction_data)

            # Get the created transaction
            transaction = Transaction.get_transaction_by_id(result.inserted_id)
            
            # Update account balances
            _update_account_balances({
                'type': transaction_type,
                'amount': amount,
                'account_from': account_from,
                'account_to': account_to,
                'date': transaction_date or datetime.now(TIMEZONE)
            })
            
            # Update budget for this transaction
            _update_budget_for_transaction({
                '_id': result.inserted_id,
                'user_id': current_user,
                'type': transaction_type,
                'amount': amount,
                'category': category,
                'description': description,
                'date': transaction_date or datetime.now(TIMEZONE)
            })

            return jsonify(_format_transaction_dates(transaction)), 201
        except Exception as e:
            return jsonify({'message': str(e)}), 400

@transactions_bp.route('/<transaction_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_transaction(transaction_id):
    current_user = get_jwt_identity()
    
    try:
        transaction = Transaction.get_transaction_by_id(transaction_id)
        if not transaction or str(transaction['user_id']) != current_user:
            return jsonify({'message': 'Transaction not found'}), 404
        
        if request.method == 'GET':
            return jsonify(_format_transaction_dates(transaction)), 200
        
        elif request.method == 'PUT':
            data = request.get_json()
            update_data = {}
            
            # Validate and update amount
            if 'amount' in data:
                try:
                    update_data['amount'] = float(data['amount'])
                    if update_data['amount'] <= 0:
                        raise ValueError('Amount must be positive')
                except (ValueError, TypeError):
                    return jsonify({'message': 'Invalid amount'}), 400
            
            # Update category if provided
            if 'category' in data:
                update_data['category'] = data['category']
                
            # Update description if provided
            if 'description' in data:
                update_data['description'] = data['description']
                
            # Handle date and time updates
            if 'date' in data or 'time' in data:
                # Get current date and time from transaction or request
                transaction_date = transaction['date']
                
                # If date is provided, update it
                if 'date' in data and data['date']:
                    try:
                        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
                        # Create a new datetime with the updated date but keep the original time
                        transaction_date = TIMEZONE.localize(
                            datetime.combine(new_date, transaction_date.time())
                        )
                    except ValueError:
                        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
                
                # If time is provided, update it
                if 'time' in data and data['time']:
                    try:
                        time_obj = datetime.strptime(data['time'], '%H:%M').time()
                        # Update the time part while keeping the date part
                        transaction_date = transaction_date.replace(
                            hour=time_obj.hour,
                            minute=time_obj.minute,
                            second=0,
                            microsecond=0
                        )
                    except ValueError:
                        return jsonify({'message': 'Invalid time format. Use HH:MM'}), 400
                
                # Make sure the datetime is timezone aware
                if not transaction_date.tzinfo:
                    transaction_date = TIMEZONE.localize(transaction_date)
                    
                update_data['date'] = transaction_date
            
            # Update type if provided
            if 'type' in data and data['type'] in ['income', 'expense', 'transfer']:
                update_data['type'] = data['type']
            
            # Update accounts if provided
            if 'account_from' in data:
                update_data['account_from'] = ObjectId(data['account_from']) if data['account_from'] else None
            if 'account_to' in data:
                update_data['account_to'] = ObjectId(data['account_to']) if data['account_to'] else None
            
            # Add updated_at timestamp
            update_data['updated_at'] = datetime.now(TIMEZONE)
            
            # First reverse the old transaction effect
            _update_account_balances(transaction, reverse=True)
            
            # Perform the update
            Transaction.update_transaction(transaction_id, update_data)
            
            # Get the updated transaction with all fields
            updated_transaction = Transaction.get_transaction_by_id(transaction_id)
            
            # Apply the new transaction effect
            _update_account_balances(updated_transaction)
            
            # Update budget if this is an expense
            if updated_transaction['type'] == 'expense':
                budget = Budget.get_budget_by_category(current_user, updated_transaction['category'], date=updated_transaction['date'])
                if budget:
                    Budget.update_budget_with_transaction(
                        str(budget['_id']),
                        {
                            'amount': updated_transaction['amount'],
                            'category': updated_transaction['category'],
                            'date': updated_transaction['date'],
                            'description': updated_transaction['description'],
                            '_id': str(updated_transaction['_id'])
                        }
                    )
            
            return jsonify({
                'message': 'Transaction updated',
                'transaction': _format_transaction_dates(updated_transaction)
            }), 200
        
        elif request.method == 'DELETE':
            # Delete the transaction
            Transaction.delete_transaction(transaction_id)
            
            # Update account balances by reversing the transaction
            _update_account_balances({
                'type': transaction['type'],
                'amount': float(transaction['amount']),
                'account_from': transaction.get('account_from'),
                'account_to': transaction.get('account_to'),
                'date': transaction['date']
            }, reverse=True)
            
            # Update budget if this was an expense
            if transaction['type'] == 'expense':
                budget = Budget.get_budget_by_category(
                    current_user, 
                    transaction['category'],
                    date=transaction['date']
                )
                if budget:
                    Budget.update_budget_with_transaction(
                        str(budget['_id']),
                        {
                            'amount': float(transaction['amount']),
                            'category': transaction['category'],
                            'date': transaction['date'],
                            'description': transaction['description'],
                            '_id': str(transaction['_id'])
                        },
                        is_new=False  # This will remove the transaction from the budget
                    )
        
            return jsonify({'message': 'Transaction deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@transactions_bp.route('/categories')
@jwt_required()
def get_categories():
    return jsonify(Transaction.DEFAULT_CATEGORIES), 200