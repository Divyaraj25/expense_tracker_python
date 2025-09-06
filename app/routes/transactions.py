from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.account import Account
from app.utils.validators import validate_date, validate_amount

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def handle_transactions():
    current_user = get_jwt_identity()
    
    if request.method == 'GET':
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
        if start_date and end_date:
            if validate_date(start_date) and validate_date(end_date):
                filters['start_date'] = start_date
                filters['end_date'] = end_date
        
        transactions = Transaction.get_user_transactions(current_user, limit, skip, filters)
        return jsonify([{
            'id': str(t['_id']),
            'type': t['type'],
            'amount': t['amount'],
            'category': t['category'],
            'description': t['description'],
            'date': t['date'].isoformat() if 'date' in t else None,
            'account_from': str(t.get('account_from')) if t.get('account_from') else None,
            'account_to': str(t.get('account_to')) if t.get('account_to') else None,
            'created_at': t['created_at'].isoformat() if 'created_at' in t else None
        } for t in transactions]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        type = data.get('type')
        amount = data.get('amount')
        category = data.get('category')
        description = data.get('description')
        account_from = data.get('account_from')
        account_to = data.get('account_to')
        date = data.get('date')
        
        # Validation
        if not all([type, amount, category, description]):
            return jsonify({'message': 'Missing required fields'}), 400
            
        if not validate_amount(amount):
            return jsonify({'message': 'Invalid amount'}), 400
            
        if date and not validate_date(date):
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        # Create transaction
        transaction = Transaction.create_transaction(
            current_user, type, amount, category, description, account_from, account_to, date
        )
        
        # Update account balances if needed
        if type == 'expense' and account_from:
            Account.update_account_balance(account_from, -float(amount))
        elif type == 'income' and account_to:
            Account.update_account_balance(account_to, float(amount))
        elif type == 'transfer' and account_from and account_to:
            Account.update_account_balance(account_from, -float(amount))
            Account.update_account_balance(account_to, float(amount))
        
        return jsonify({'message': 'Transaction created', 'id': str(transaction.inserted_id)}), 201

@transactions_bp.route('/<transaction_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_transaction(transaction_id):
    current_user = get_jwt_identity()
    
    transaction = Transaction.get_transaction_by_id(transaction_id)
    if not transaction or str(transaction['user_id']) != current_user:
        return jsonify({'message': 'Transaction not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': str(transaction['_id']),
            'type': transaction['type'],
            'amount': transaction['amount'],
            'category': transaction['category'],
            'description': transaction['description'],
            'date': transaction['date'].isoformat() if 'date' in transaction else None,
            'account_from': str(transaction.get('account_from')) if transaction.get('account_from') else None,
            'account_to': str(transaction.get('account_to')) if transaction.get('account_to') else None,
            'created_at': transaction['created_at'].isoformat() if 'created_at' in transaction else None
        }), 200
    
    elif request.method == 'PUT':
        data = request.get_json()
        update_data = {}
        
        if 'amount' in data:
            if not validate_amount(data['amount']):
                return jsonify({'message': 'Invalid amount'}), 400
            update_data['amount'] = float(data['amount'])
        
        if 'category' in data:
            update_data['category'] = data['category']
            
        if 'description' in data:
            update_data['description'] = data['description']
            
        if 'date' in data:
            if not validate_date(data['date']):
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
            update_data['date'] = data['date']
        
        Transaction.update_transaction(transaction_id, update_data)
        return jsonify({'message': 'Transaction updated'}), 200
    
    elif request.method == 'DELETE':
        # Reverse the transaction effect on accounts
        if transaction['type'] == 'expense' and transaction.get('account_from'):
            Account.update_account_balance(str(transaction['account_from']), transaction['amount'])
        elif transaction['type'] == 'income' and transaction.get('account_to'):
            Account.update_account_balance(str(transaction['account_to']), -transaction['amount'])
        elif transaction['type'] == 'transfer' and transaction.get('account_from') and transaction.get('account_to'):
            Account.update_account_balance(str(transaction['account_from']), transaction['amount'])
            Account.update_account_balance(str(transaction['account_to']), -transaction['amount'])
        
        Transaction.delete_transaction(transaction_id)
        return jsonify({'message': 'Transaction deleted'}), 200

@transactions_bp.route('/categories')
@jwt_required()
def get_categories():
    return jsonify(Transaction.DEFAULT_CATEGORIES), 200