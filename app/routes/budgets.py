from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.budget import Budget
from app.utils.calculations import calculate_budget_progress
from app.utils.validators import validate_amount, validate_date

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def handle_budgets():
    current_user = get_jwt_identity()
    
    if request.method == 'GET':
        budgets = Budget.get_user_budgets(current_user)
        
        # Calculate progress for each budget
        budgets_with_progress = []
        for budget in budgets:
            progress = calculate_budget_progress(current_user, budget)
            budgets_with_progress.append({
                'id': str(budget['_id']),
                'category': budget['category'],
                'amount': budget['amount'],
                'period': budget['period'],
                'start_date': budget['start_date'].isoformat() if 'start_date' in budget else None,
                'end_date': budget['end_date'].isoformat() if 'end_date' in budget else None,
                'progress': progress,
                'created_at': budget['created_at'].isoformat() if 'created_at' in budget else None,
                'updated_at': budget['updated_at'].isoformat() if 'updated_at' in budget else None
            })
        
        return jsonify(budgets_with_progress), 200
    
    elif request.method == 'POST':
        data = request.get_json()
        category = data.get('category')
        amount = data.get('amount')
        period = data.get('period')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not all([category, amount, period, start_date]):
            return jsonify({'message': 'Missing required fields'}), 400
            
        if not validate_amount(amount):
            return jsonify({'message': 'Invalid amount'}), 400
            
        if not validate_date(start_date):
            return jsonify({'message': 'Invalid start date format. Use YYYY-MM-DD'}), 400
            
        if end_date and not validate_date(end_date):
            return jsonify({'message': 'Invalid end date format. Use YYYY-MM-DD'}), 400
            
        if period not in Budget.PERIODS:
            return jsonify({'message': 'Invalid period'}), 400
        
        budget = Budget.create_budget(
            current_user, category, amount, period, start_date, end_date
        )
        
        return jsonify({'message': 'Budget created', 'id': str(budget.inserted_id)}), 201

@budgets_bp.route('/<budget_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_budget(budget_id):
    current_user = get_jwt_identity()
    
    budget = Budget.get_budget_by_id(budget_id)
    if not budget or str(budget['user_id']) != current_user:
        return jsonify({'message': 'Budget not found'}), 404
    
    if request.method == 'GET':
        progress = calculate_budget_progress(current_user, budget)
        return jsonify({
            'id': str(budget['_id']),
            'category': budget['category'],
            'amount': budget['amount'],
            'period': budget['period'],
            'start_date': budget['start_date'].isoformat() if 'start_date' in budget else None,
            'end_date': budget['end_date'].isoformat() if 'end_date' in budget else None,
            'progress': progress,
            'created_at': budget['created_at'].isoformat() if 'created_at' in budget else None,
            'updated_at': budget['updated_at'].isoformat() if 'updated_at' in budget else None
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
            
        if 'period' in data:
            if data['period'] not in Budget.PERIODS:
                return jsonify({'message': 'Invalid period'}), 400
            update_data['period'] = data['period']
            
        if 'start_date' in data:
            if not validate_date(data['start_date']):
                return jsonify({'message': 'Invalid start date format. Use YYYY-MM-DD'}), 400
            update_data['start_date'] = data['start_date']
            
        if 'end_date' in data:
            if data['end_date'] and not validate_date(data['end_date']):
                return jsonify({'message': 'Invalid end date format. Use YYYY-MM-DD'}), 400
            update_data['end_date'] = data['end_date']
        
        Budget.update_budget(budget_id, update_data)
        return jsonify({'message': 'Budget updated'}), 200
    
    elif request.method == 'DELETE':
        Budget.delete_budget(budget_id)
        return jsonify({'message': 'Budget deleted'}), 200