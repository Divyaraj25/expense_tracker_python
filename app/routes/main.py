from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.utils.calculations import calculate_total_balance, calculate_income_vs_expense
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.budget import Budget
from app.models.user import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/api/check-session')
def check_session():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if user:
            return jsonify({
                'logged_in': True,
                'user': {
                    'id': str(user['_id']),
                    'username': user['username'],
                    'email': user['email']
                }
            }), 200
        return jsonify({'logged_in': False, 'message': 'User not found'}), 404
    except Exception as e:
        return jsonify({'logged_in': False, 'message': str(e)}), 401

@main_bp.route('/')
@jwt_required()
def dashboard():
    current_user = get_jwt_identity()
    
    # Get recent transactions
    recent_transactions = Transaction.get_user_transactions(current_user, limit=5)
    
    # Get accounts
    accounts = Account.get_user_accounts(current_user)
    
    # Get budgets
    budgets = Budget.get_user_budgets(current_user)
    
    # Calculate totals
    total_balance = calculate_total_balance(current_user)
    income_expense = calculate_income_vs_expense(current_user)
    
    return render_template('dashboard.html', 
                         transactions=recent_transactions,
                         accounts=accounts,
                         budgets=budgets,
                         total_balance=total_balance,
                         income_expense=income_expense)

@main_bp.route('/transactions')
@jwt_required()
def transactions_page():
    return render_template('transactions.html')

@main_bp.route('/accounts')
@jwt_required()
def accounts_page():
    return render_template('accounts.html')

@main_bp.route('/budgets')
@jwt_required()
def budgets_page():
    return render_template('budgets.html')

@main_bp.route('/charts')
@jwt_required()
def charts_page():
    return render_template('charts.html')

@main_bp.route('/game')
@jwt_required()
def game():
    return render_template('game.html')