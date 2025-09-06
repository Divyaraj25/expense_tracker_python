from datetime import datetime, timedelta
from app.models.transaction import Transaction
from app.models.account import Account

def calculate_total_balance(user_id):
    accounts = Account.get_user_accounts(user_id)
    return sum(account['balance'] for account in accounts)

def calculate_income_vs_expense(user_id, start_date=None, end_date=None):
    income = Transaction.get_transactions_by_type(user_id, 'income', start_date, end_date)
    expense = Transaction.get_transactions_by_type(user_id, 'expense', start_date, end_date)
    
    total_income = sum(t['amount'] for t in income)
    total_expense = sum(t['amount'] for t in expense)
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_flow': total_income - total_expense
    }

def calculate_category_totals(user_id, type, start_date=None, end_date=None):
    transactions = Transaction.get_transactions_by_type(user_id, type, start_date, end_date)
    category_totals = {}
    
    for transaction in transactions:
        category = transaction['category']
        amount = transaction['amount']
        category_totals[category] = category_totals.get(category, 0) + amount
    
    return category_totals

def calculate_budget_progress(user_id, budget):
    now = datetime.now()
    
    # Get transactions for the budget category in the current period
    if budget['period'] == 'daily':
        start_date = datetime(now.year, now.month, now.day)
        end_date = start_date + timedelta(days=1)
    elif budget['period'] == 'weekly':
        start_date = now - timedelta(days=now.weekday())
        start_date = datetime(start_date.year, start_date.month, start_date.day)
        end_date = start_date + timedelta(weeks=1)
    elif budget['period'] == 'monthly':
        start_date = datetime(now.year, now.month, 1)
        end_date = datetime(now.year, now.month + 1, 1) if now.month < 12 else datetime(now.year + 1, 1, 1)
    else:  # yearly
        start_date = datetime(now.year, 1, 1)
        end_date = datetime(now.year + 1, 1, 1)
    
    transactions = Transaction.get_transactions_by_category(user_id, budget['category'], start_date, end_date)
    spent = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    
    return {
        'spent': spent,
        'budget': budget['amount'],
        'remaining': budget['amount'] - spent,
        'percentage': (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0
    }

def calculate_account_balances(user_id):
    accounts = Account.get_user_accounts(user_id)
    return {str(account['_id']): account['balance'] for account in accounts}