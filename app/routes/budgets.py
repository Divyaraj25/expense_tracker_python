from datetime import datetime, timedelta
import pytz
from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from typing import Dict, List, Any, Optional, Union, Any
from app import mongo
from app.models.budget import Budget
from app.utils.validators import validate_amount, validate_date

def convert_floats(obj):
    """Convert numeric types to float recursively"""
    if isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats(x) for x in obj]
    elif isinstance(obj, (int, float)):
        return float(obj)
    return obj

def _get_budget_period_dates(period: str, start_date: datetime) -> tuple[datetime, datetime]:
    """Calculate start and end dates for a budget period.
    
    Args:
        period: The budget period ('daily', 'weekly', 'monthly', 'yearly')
        start_date: The base date to calculate the period from
        
    Returns:
        tuple: (period_start, period_end) datetime objects
    """
    if period == 'daily':
        period_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)
    elif period == 'weekly':
        period_start = start_date - timedelta(days=start_date.weekday())
        period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(weeks=1)
    elif period == 'monthly':
        period_start = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if period_start.month == 12:
            period_end = period_start.replace(year=period_start.year + 1, month=1)
        else:
            period_end = period_start.replace(month=period_start.month + 1)
    elif period == 'yearly':
        period_start = start_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start.replace(year=period_start.year + 1)
    else:
        # Default to monthly if period is invalid
        period_start = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start.replace(month=period_start.month + 1)
    
    return period_start, period_end

# Constants
IST = pytz.timezone('Asia/Kolkata')
UTC_ISO_FORMAT = '+00:00'  # Reusable constant for UTC timezone offset

budgets_bp = Blueprint('budgets', __name__)

# Budget tips
BUDGET_TIPS = [
    {
        'id': 1,
        'tip': '💡 Set realistic budgets based on your past spending patterns',
        'category': 'general'
    },
    {
        'id': 2,
        'tip': '🍽️ Track food expenses daily to avoid overspending on dining out',
        'category': 'food'
    },
    {
        'id': 3,
        'tip': '🚗 Use public transport or carpool to save on transportation costs',
        'category': 'transport'
    },
    {
        'id': 4,
        'tip': '💰 Save at least 20% of your income for future goals',
        'category': 'savings'
    },
    {
        'id': 5,
        'tip': '📱 Use expense tracking apps to monitor your spending in real-time',
        'category': 'general'
    }
]

@budgets_bp.route('/tips', methods=['GET'])
def get_budget_tips():
    """Get random budget tips"""
    import random
    # Get a random tip
    random_tip = random.choice(BUDGET_TIPS)
    
    # Set cache control headers (1 hour)
    response = make_response(jsonify({
        'tip': random_tip['tip'],
        'category': random_tip['category'],
        'total_tips': len(BUDGET_TIPS)
    }))
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@budgets_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def handle_budgets():
    try:
        current_user = get_jwt_identity()
        
        if request.method == 'GET':
            return _handle_get_budgets(current_user)
            
        elif request.method == 'POST':
            return _handle_post_budget(current_user)
            
    except Exception as e:
        current_app.logger.error(f'Unexpected error in handle_budgets: {str(e)}', exc_info=True)
        return jsonify({'error': 'An unexpected error occurred while processing your request'}), 500

def _handle_get_budgets(current_user):
    """Handle GET request for budgets with comprehensive error handling"""
    try:
        # Get filter parameters
        period = request.args.get('period')
        category = request.args.get('category')
        show_all = request.args.get('show_all', 'false').lower() == 'true'
        
        # Get current date in UTC for filtering
        today_utc = datetime.now(pytz.UTC)
        today_ist = today_utc.astimezone(IST).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Build query based on filters
        query = {'user_id': ObjectId(current_user)}
        
        if category:
            query['category'] = category
            
        if period == 'today':
            # Include budgets that are active today or in the future
            query['start_date'] = {'$lte': today_utc}
            query['$or'] = [
                {'end_date': None},
                {'end_date': {'$gte': today_ist.astimezone(pytz.UTC)}}
            ]
        elif period == 'this_week':
            start_of_week = today_ist - timedelta(days=today_ist.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            query['start_date'] = {'$lte': end_of_week.astimezone(pytz.UTC)}
            query['$or'] = [
                {'end_date': None},
                {'end_date': {'$gte': start_of_week.astimezone(pytz.UTC)}}
            ]
        elif period == 'this_month':
            start_of_month = today_ist.replace(day=1)
            next_month = today_ist.replace(day=28) + timedelta(days=4)
            end_of_month = next_month - timedelta(days=next_month.day)
            
            query['start_date'] = {'$lte': end_of_month.astimezone(pytz.UTC)}
            query['$or'] = [
                {'end_date': None},
                {'end_date': {'$gte': start_of_month.astimezone(pytz.UTC)}}
            ]
        elif period == 'future':
            # For future budgets
            query['start_date'] = {'$gt': today_utc}
            budgets = list(mongo.db.budgets.find(query).sort('start_date', -1))
        
        # Find budgets based on show_all flag
        if show_all:
            # Get all budgets matching the filters
            budgets = list(mongo.db.budgets.find(query).sort('start_date', -1))
        else:
            # Only get active budgets (current date is between start_date and end_date)
            query['start_date'] = {'$lte': today_utc}
            query['$or'] = [
                {'end_date': None},
                {'end_date': {'$gte': today_ist.astimezone(pytz.UTC)}}
            ]
            budgets = list(mongo.db.budgets.find(query).sort('start_date', -1))
        
        # Format response
        budgets_with_progress = []
        for budget in budgets:
            try:
                # Calculate period start and end dates based on the period type
                period_start, period_end = _get_budget_period_dates(
                    budget.get('period', 'monthly'),
                    budget.get('start_date', datetime.now(IST))
                )
                
                # Get transactions for this budget period
                query = {
                    'user_id': ObjectId(current_user),
                    'category': budget['category'],
                    'date': {
                        '$gte': period_start,
                        '$lte': period_end
                    },
                    'type': 'expense'
                }
                
                transactions = list(mongo.db.transactions.find(query))
                
                # Calculate total spent and remaining
                total_spent = float(budget.get('spent', 0))  # Use pre-calculated spent amount
                budget_amount = float(budget.get('amount', 0))
                remaining = float(budget.get('remaining', max(0, budget_amount - total_spent)))
                
                # Calculate progress percentage
                progress_percent = 0.0
                if budget_amount > 0:
                    progress_percent = min(100, (total_spent / budget_amount) * 100)
                
                # Format dates for display
                try:
                    start_date = budget.get('start_date')
                    end_date = budget.get('end_date')
                    
                    period_start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else 'N/A'
                    period_end_str = end_date.strftime('%Y-%m-%d') if end_date and hasattr(end_date, 'strftime') else 'N/A'
                except Exception as e:
                    current_app.logger.warning(f"Error formatting dates for budget {budget.get('_id', 'unknown')}: {str(e)}")
                    period_start_str = 'N/A'
                    period_end_str = 'N/A'
                
                # Create formatted budget object
                formatted_budget = {
                    'id': str(budget['_id']),  # Ensure ID is a string
                    'category': budget.get('category', ''),
                    'amount': budget_amount,
                    'period': budget.get('period', 'monthly'),
                    'start_date': period_start_str,
                    'end_date': period_end_str,
                    'spent': total_spent,
                    'remaining': remaining,
                    'progress_percent': round(progress_percent, 1),
                    'is_over_budget': total_spent > budget_amount,
                    'transactions_count': len(transactions),
                    'note': budget.get('note', '')
                }
                
                # Add any additional fields that might be needed
                if 'notifications' in budget:
                    formatted_budget['notifications'] = budget['notifications']
                if 'is_active' in budget:
                    formatted_budget['is_active'] = budget['is_active']
                
                budgets_with_progress.append(formatted_budget)
                
            except Exception as e:
                current_app.logger.error(f"Error processing budget {budget.get('_id', 'unknown')}: {str(e)}", exc_info=True)
                # Skip this budget but continue with others
        
        # Convert all numeric types to float in the final response
        try:
            budgets_with_progress = convert_floats(budgets_with_progress)
        except Exception as e:
            current_app.logger.warning(f"Error converting floats in budget response: {str(e)}")
            # Continue with the original data if conversion fails
        
        return jsonify(budgets_with_progress), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching budgets: {str(e)}', exc_info=True)
        return jsonify({'error': 'Failed to fetch budgets. Please try again later.'}), 500

def _handle_post_budget(current_user):
    """Handle POST request for creating a new budget with comprehensive error handling"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        # Validate required fields
        required_fields = ['category', 'amount', 'period']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields,
                'required': required_fields
            }), 400
            
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format. Must be a number.'}), 400
            
        # Validate period
        valid_periods = ['daily', 'weekly', 'monthly', 'yearly', 'custom']
        if data['period'] not in valid_periods:
            return jsonify({
                'error': 'Invalid period',
                'valid_periods': valid_periods
            }), 400
        
        # Helper function to parse and normalize date to UTC
        def parse_date(date_str, is_end_date=False):
            if not date_str:
                return None
            try:
                # Parse the input date string (expected to be in IST)
                dt = datetime.fromisoformat(date_str.replace('Z', UTC_ISO_FORMAT))
                if dt.tzinfo is None:
                    # If no timezone, assume it's IST
                    dt = IST.localize(dt)
                # Convert to UTC for storage
                dt = dt.astimezone(pytz.UTC)  
                # Set time to start or end of day in UTC
                if is_end_date:
                    dt = dt.replace(hour=23, minute=59, second=59)
                    dt_utc = dt_utc.replace(hour=23, minute=59, second=59)
                else:
                    dt_utc = dt_utc.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                return dt_utc
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid date format: {date_str}")
        
        # Handle start date
        try:
            start_date = parse_date(data.get('start_date')) or datetime.now(IST).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        except ValueError as e:
            return jsonify({
                'error': 'Invalid start_date format',
                'details': 'Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)'
            }), 400
        
        # Handle end date
        end_date = None
        if 'end_date' in data and data['end_date']:
            try:
                end_date = parse_date(data['end_date'], is_end_date=True)
            except ValueError as e:
                return jsonify({
                    'error': 'Invalid end_date format',
                    'details': 'Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)'
                }), 400
        
        # Create the budget using the Budget model
        try:
            budget_id = Budget.create_budget(
                user_id=current_user,
                category=data['category'],
                amount=amount,
                period=data['period'],
                start_date=start_date,
                end_date=end_date,
                note=data.get('note', '')
            )
            
            if not budget_id:
                return jsonify({'error': 'Failed to create budget'}), 500
                
            # Get the created budget to return
            try:
                budget = mongo.db.budgets.find_one({
                    '_id': ObjectId(budget_id),
                    'user_id': ObjectId(current_user)
                })
                
                if not budget:
                    return jsonify({'error': 'Failed to retrieve created budget'}), 500
                
                # Helper function to convert datetime from UTC to IST for display
                def to_ist(dt):
                    if not dt:
                        return None
                    if isinstance(dt, str):
                        dt = datetime.fromisoformat(dt.replace('Z', UTC_ISO_FORMAT))
                    if dt.tzinfo is None:
                        dt = pytz.utc.localize(dt)
                    # Convert to IST for display
                    return dt.astimezone(IST)

                # Format the budget for the response (converting all dates to IST for display)
                def format_date_for_display(dt):
                    if not dt:
                        return None
                    if isinstance(dt, str):
                        dt = datetime.fromisoformat(dt.replace('Z', UTC_ISO_FORMAT))
                    if dt.tzinfo is None:
                        dt = pytz.utc.localize(dt)
                    # Convert to IST for display
                    return dt.astimezone(IST).strftime('%Y-%m-%dT%H:%M:%S%z')
                
                formatted_budget = {
                    'id': str(budget['_id']),  # Add 'id' field as string for frontend
                    'user_id': str(budget['user_id']),
                    'category': budget.get('category', ''),
                    'amount': float(budget.get('amount', 0)),
                    'period': budget.get('period', 'monthly'),
                    'start_date': format_date_for_display(budget.get('start_date')),
                    'end_date': format_date_for_display(budget.get('end_date')),
                    'note': budget.get('note', ''),
                    'spent': float(budget.get('spent', 0)),
                    'remaining': float(budget.get('remaining', 0)),
                    'transactions': [{
                        **tx,
                        'date': format_date_for_display(tx.get('date'))
                    } for tx in budget.get('transactions', [])],
                    'is_active': budget.get('is_active', True),
                    'created_at': format_date_for_display(budget.get('created_at')),
                    'updated_at': budget.get('updated_at')
                }
                
                return jsonify({
                    'message': 'Budget created successfully',
                    'budget': formatted_budget
                }), 201
                
            except Exception as e:
                current_app.logger.error(f'Error retrieving created budget: {str(e)}', exc_info=True)
                return jsonify({'error': 'Budget created but failed to retrieve details'}), 201
                
        except Exception as e:
            current_app.logger.error(f'Error creating budget: {str(e)}', exc_info=True)
            return jsonify({'error': 'Failed to create budget due to server error'}), 500
            
    except Exception as e:
        current_app.logger.error(f'Error processing budget creation request: {str(e)}', exc_info=True)
        return jsonify({'error': 'Failed to process budget creation request'}), 500
        
@budgets_bp.route('/<string:budget_id>', methods=['PUT'])
@jwt_required()
def handle_budget(budget_id):
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Check if budget exists and belongs to user
        budget = mongo.db.budgets.find_one({
            '_id': ObjectId(budget_id),
            'user_id': ObjectId(current_user)
        })
        
        if not budget:
            return jsonify({'error': 'Budget not found'}), 404
            
        # Prepare update data
        update_data = {}
        
        # Handle category update
        if 'category' in data:
            update_data['category'] = data['category']
            
        # Handle amount update
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({'error': 'Amount must be greater than 0'}), 400
                update_data['amount'] = amount
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid amount format'}), 400
                
        # Handle period update
        if 'period' in data:
            if data['period'] not in ['daily', 'weekly', 'monthly', 'yearly', 'custom']:
                return jsonify({'error': 'Invalid period'}), 400
            update_data['period'] = data['period']
            
        # Handle start date update
        start_date = budget.get('start_date')
        if 'start_date' in data and data['start_date']:
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
                if start_date.tzinfo is None:
                    start_date = pytz.utc.localize(start_date)
                start_date = start_date.astimezone(IST)
                update_data['start_date'] = start_date
            except (ValueError, AttributeError):
                return jsonify({'error': 'Invalid start_date format'}), 400
                
        # Handle end date update
        end_date = budget.get('end_date')
        if 'end_date' in data:
            if data['end_date']:
                try:
                    end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
                    if end_date.tzinfo is None:
                        end_date = pytz.utc.localize(end_date)
                    end_date = end_date.astimezone(IST).replace(hour=23, minute=59, second=59)
                    update_data['end_date'] = end_date
                except (ValueError, AttributeError):
                    return jsonify({'error': 'Invalid end_date format'}), 400
            else:
                end_date = None
                update_data['end_date'] = None
                
        # Handle note update
        if 'note' in data:
            update_data['note'] = data['note']
            
        # Update the budget with the new data
        update_data['updated_at'] = datetime.now(IST)
        
        # Update the budget document
        result = mongo.db.budgets.update_one(
            {'_id': ObjectId(budget_id), 'user_id': ObjectId(current_user)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Budget not found or not updated'}), 404
            
        # If dates or category changed, we need to recalculate the budget
        if 'start_date' in update_data or 'end_date' in update_data or 'category' in update_data:
            # Get the updated budget to calculate new values
            updated_budget = mongo.db.budgets.find_one({
                '_id': ObjectId(budget_id),
                'user_id': ObjectId(current_user)
            })
            
            if updated_budget:
                # Recalculate spent amount based on transactions
                total_spent = 0
                for tx in updated_budget.get('transactions', []):
                    total_spent += tx.get('amount', 0)
                
                # Update the budget with new calculated values
                result = mongo.db.budgets.update_one(
                    {'_id': ObjectId(budget_id)},
                    {'$set': {
                        'spent': round(total_spent, 2),
                        'remaining': max(0, (update_data.get('amount', updated_budget.get('amount', 0)) - total_spent)),
                        'updated_at': datetime.now(IST)
                    }}
                )
                
                if result.matched_count == 0:
                    return jsonify({'error': 'Failed to update budget calculations'}), 500
        
        # Get the updated budget to return
        updated_budget = mongo.db.budgets.find_one({
            '_id': ObjectId(budget_id),
            'user_id': ObjectId(current_user)
        })
        
        # Convert ObjectId to string for JSON serialization
        updated_budget['_id'] = str(updated_budget['_id'])
        updated_budget['user_id'] = str(updated_budget['user_id'])
        
        return jsonify({
            'message': 'Budget updated successfully',
            'budget': updated_budget
        })
        
    except Exception as e:
        current_app.logger.error(f'Error updating budget: {str(e)}', exc_info=True)
        return jsonify({'error': f'Failed to update budget: {str(e)}'}), 500
@budgets_bp.route('/tips', methods=['GET'])
def get_tips():
    return jsonify({
        'tips': [
            'Create a budget to track your expenses',
            'Set a realistic budget amount',
            'Prioritize your expenses',
            'Use the 50/30/20 rule',
            'Review and adjust your budget regularly'
        ]
    }), 200