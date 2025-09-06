from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.calculations import calculate_income_vs_expense, calculate_category_totals
from datetime import datetime, timedelta

charts_bp = Blueprint('charts', __name__)

@charts_bp.route('/income-vs-expense')
@jwt_required()
def income_vs_expense_chart():
    current_user = get_jwt_identity()
    
    # Get timeframe (default to last 30 days)
    timeframe = request.args.get('timeframe', '30d')
    
    if timeframe == '7d':
        start_date = datetime.now() - timedelta(days=7)
    elif timeframe == '30d':
        start_date = datetime.now() - timedelta(days=30)
    elif timeframe == '90d':
        start_date = datetime.now() - timedelta(days=90)
    elif timeframe == '1y':
        start_date = datetime.now() - timedelta(days=365)
    else:
        start_date = None
    
    end_date = datetime.now()
    
    data = calculate_income_vs_expense(current_user, start_date, end_date)
    return jsonify(data), 200

@charts_bp.route('/expense-by-category')
@jwt_required()
def expense_by_category_chart():
    current_user = get_jwt_identity()
    
    # Get timeframe (default to last 30 days)
    timeframe = request.args.get('timeframe', '30d')
    
    if timeframe == '7d':
        start_date = datetime.now() - timedelta(days=7)
    elif timeframe == '30d':
        start_date = datetime.now() - timedelta(days=30)
    elif timeframe == '90d':
        start_date = datetime.now() - timedelta(days=90)
    elif timeframe == '1y':
        start_date = datetime.now() - timedelta(days=365)
    else:
        start_date = None
    
    end_date = datetime.now()
    
    data = calculate_category_totals(current_user, 'expense', start_date, end_date)
    return jsonify(data), 200

@charts_bp.route('/income-by-category')
@jwt_required()
def income_by_category_chart():
    current_user = get_jwt_identity()
    
    # Get timeframe (default to last 30 days)
    timeframe = request.args.get('timeframe', '30d')
    
    if timeframe == '7d':
        start_date = datetime.now() - timedelta(days=7)
    elif timeframe == '30d':
        start_date = datetime.now() - timedelta(days=30)
    elif timeframe == '90d':
        start_date = datetime.now() - timedelta(days=90)
    elif timeframe == '1y':
        start_date = datetime.now() - timedelta(days=365)
    else:
        start_date = None
    
    end_date = datetime.now()
    
    data = calculate_category_totals(current_user, 'income', start_date, end_date)
    return jsonify(data), 200

@charts_bp.route('/account-balances')
@jwt_required()
def account_balances_chart():
    current_user = get_jwt_identity()
    
    from app.models.account import Account
    accounts = Account.get_user_accounts(current_user)
    
    data = {
        'labels': [account['name'] for account in accounts],
        'balances': [account['balance'] for account in accounts]
    }
    
    return jsonify(data), 200