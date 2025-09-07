from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.account import Account
from app.utils.validators import validate_date, validate_amount
from datetime import datetime
import pytz
from bson import ObjectId
from typing import Dict, Any, Optional

# Constants
TIMEZONE = pytz.timezone('Asia/Kolkata')

def _update_account_balances(transaction_data: Dict[str, Any], reverse: bool = False) -> None:
    """Update account balances based on transaction data.
    
    Args:
        transaction_data: The transaction data
        reverse: If True, reverses the effect on account balances
    """
    amount = transaction_data['amount']
    if reverse:
        amount = -amount
        
    if transaction_data['type'] == 'expense' and transaction_data.get('account_from'):
        Account.update_account_balance(str(transaction_data['account_from']), -amount)
    elif transaction_data['type'] == 'income' and transaction_data.get('account_to'):
        Account.update_account_balance(str(transaction_data['account_to']), amount)
    elif (transaction_data['type'] == 'transfer' and 
          transaction_data.get('account_from') and 
          transaction_data.get('account_to')):
        Account.update_account_balance(str(transaction_data['account_from']), -amount)
        Account.update_account_balance(str(transaction_data['account_to']), amount)

transactions_bp = Blueprint('transactions', __name__)

def _format_transaction_dates(transaction):
    """Helper function to format transaction dates for response"""
    formatted = {
        'id': str(transaction['_id']),
        'type': transaction['type'],
        'amount': transaction['amount'],
        'category': transaction['category'],
        'description': transaction['description'],
        'account_from': str(transaction.get('account_from')) if transaction.get('account_from') else None,
        'account_to': str(transaction.get('account_to')) if transaction.get('account_to') else None,
    }
    
    # Format date fields with timezone
    if transaction.get('date'):
        dt = None
        # Ensure we have a timezone-aware datetime object in IST
        if isinstance(transaction['date'], str):
            try:
                # Parse the ISO format string and ensure it's timezone aware
                dt = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    # If no timezone info, assume it's in UTC and convert to IST
                    dt = pytz.utc.localize(dt).astimezone(TIMEZONE)
                else:
                    # Convert to IST if it's in a different timezone
                    dt = dt.astimezone(TIMEZONE)
            except (ValueError, AttributeError) as e:
                print(f"Error parsing date: {e}")
                dt = datetime.now(TIMEZONE)
        elif isinstance(transaction['date'], datetime):
            dt = transaction['date']
            if dt.tzinfo is None:
                # If no timezone info, assume it's in UTC and convert to IST
                dt = pytz.utc.localize(dt).astimezone(TIMEZONE)
            else:
                # Convert to IST if it's in a different timezone
                dt = dt.astimezone(TIMEZONE)
        
        if dt:
            # Format all dates in IST
            formatted.update({
                'date': dt.isoformat(),  # ISO format for frontend
                'date_str': dt.strftime('%Y-%m-%d'),
                'time_str': dt.strftime('%H:%M'),
                'date_full': dt.strftime('%A, %B %d, %Y'),
                'time': dt.strftime('%I:%M %p'),
                'week_number': dt.strftime('%U'),
                'timezone': 'IST',
            })
    
    if transaction.get('created_at'):
        if isinstance(transaction['created_at'], str):
            try:
                dt = datetime.fromisoformat(transaction['created_at'].replace('Z', '+00:00'))
                if not dt.tzinfo:
                    dt = TIMEZONE.localize(dt)
                transaction['created_at'] = dt
            except (ValueError, AttributeError):
                pass
        
        if isinstance(transaction['created_at'], datetime):
            tz_aware_created = transaction['created_at'].astimezone(TIMEZONE)
            formatted['created_at'] = tz_aware_created.strftime('%Y-%m-%d %I:%M %p')
    
    return formatted

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
                # Make the datetime timezone aware
                transaction_date = TIMEZONE.localize(transaction_date)
            except ValueError as e:
                return jsonify({'message': f'Invalid date or time format. Use YYYY-MM-DD and HH:MM. Error: {str(e)}'}), 400

        try:
            time_str = datetime.now(TIMEZONE).strftime('%H:%M')
            
            # Create the transaction
            result = Transaction.create_transaction(
                user_id=current_user,
                type=transaction_type,
                amount=amount,
                category=category,
                description=description,
                account_from=account_from,
                account_to=account_to,
                date=transaction_date,
                time_str=time_str
            )
            
            # Get the created transaction data
            transaction_data = {
                'type': transaction_type,
                'amount': amount,
                'account_from': account_from,
                'account_to': account_to
            }
            
            # Update account balances
            _update_account_balances(transaction_data)
            
            return jsonify({
                'message': 'Transaction created', 
                'id': str(result.inserted_id)
            }), 201
        except Exception as e:
            return jsonify({'message': str(e)}), 500

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
            
            return jsonify({
                'message': 'Transaction updated',
                'transaction': _format_transaction_dates(updated_transaction)
            }), 200
        
        elif request.method == 'DELETE':
            # Reverse the transaction effect on accounts
            _update_account_balances(transaction, reverse=True)
            
            # Delete the transaction
            Transaction.delete_transaction(transaction_id)
            return jsonify({'message': 'Transaction deleted'}), 200
    
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@transactions_bp.route('/categories')
@jwt_required()
def get_categories():
    return jsonify(Transaction.DEFAULT_CATEGORIES), 200