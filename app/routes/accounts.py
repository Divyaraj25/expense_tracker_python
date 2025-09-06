from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.account import Account
from app.utils.validators import validate_amount

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def handle_accounts():
    current_user = get_jwt_identity()
    
    if request.method == 'GET':
        accounts = Account.get_user_accounts(current_user)
        return jsonify([{
            'id': str(a['_id']),
            'name': a['name'],
            'type': a['type'],
            'balance': a['balance'],
            'bank_name': a.get('bank_name'),
            'last_four': a.get('last_four'),
            'details': a.get('details'),
            'created_at': a['created_at'].isoformat() if 'created_at' in a else None,
            'updated_at': a['updated_at'].isoformat() if 'updated_at' in a else None
        } for a in accounts]), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        type = data.get('type')
        balance = data.get('balance', 0)
        bank_name = data.get('bank_name')
        last_four = data.get('last_four')
        details = data.get('details')
        
        if not all([name, type]):
            return jsonify({'message': 'Missing required fields'}), 400
            
        if not validate_amount(balance):
            return jsonify({'message': 'Invalid balance amount'}), 400
        
        account = Account.create_account(
            current_user, name, type, balance, bank_name, last_four, details
        )
        
        return jsonify({'message': 'Account created', 'id': str(account.inserted_id)}), 201

@accounts_bp.route('/<account_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_account(account_id):
    current_user = get_jwt_identity()
    
    account = Account.get_account_by_id(account_id)
    if not account or str(account['user_id']) != current_user:
        return jsonify({'message': 'Account not found'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': str(account['_id']),
            'name': account['name'],
            'type': account['type'],
            'balance': account['balance'],
            'bank_name': account.get('bank_name'),
            'last_four': account.get('last_four'),
            'details': account.get('details'),
            'created_at': account['created_at'].isoformat() if 'created_at' in account else None,
            'updated_at': account['updated_at'].isoformat() if 'updated_at' in account else None
        }), 200
    
    elif request.method == 'PUT':
        data = request.get_json()
        update_data = {}
        
        if 'name' in data:
            update_data['name'] = data['name']
            
        if 'type' in data:
            update_data['type'] = data['type']
            
        if 'bank_name' in data:
            update_data['bank_name'] = data['bank_name']
            
        if 'last_four' in data:
            update_data['last_four'] = data['last_four']
            
        if 'details' in data:
            update_data['details'] = data['details']
        
        Account.update_account(account_id, update_data)
        return jsonify({'message': 'Account updated'}), 200
    
    elif request.method == 'DELETE':
        # Check if account has transactions
        from app.models.transaction import Transaction
        transactions = Transaction.get_user_transactions(current_user, filters={'account_from': account_id})
        transactions.extend(Transaction.get_user_transactions(current_user, filters={'account_to': account_id}))
        
        if transactions:
            return jsonify({'message': 'Cannot delete account with transactions'}), 400
        
        Account.delete_account(account_id)
        return jsonify({'message': 'Account deleted'}), 200