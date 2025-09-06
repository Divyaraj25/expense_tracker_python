from datetime import datetime
from app import mongo
from bson import ObjectId

class Budget:
    PERIODS = ['daily', 'weekly', 'monthly', 'yearly']
    
    @staticmethod
    def create_budget(user_id, category, amount, period, start_date, end_date=None):
        budget = {
            'user_id': ObjectId(user_id),
            'category': category,
            'amount': float(amount),
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        return mongo.db.budgets.insert_one(budget)
    
    @staticmethod
    def get_user_budgets(user_id):
        return list(mongo.db.budgets.find({'user_id': ObjectId(user_id)}))
    
    @staticmethod
    def get_budget_by_id(budget_id):
        return mongo.db.budgets.find_one({'_id': ObjectId(budget_id)})
    
    @staticmethod
    def get_budget_by_category(user_id, category, period=None):
        query = {'user_id': ObjectId(user_id), 'category': category}
        if period:
            query['period'] = period
        return mongo.db.budgets.find_one(query)
    
    @staticmethod
    def update_budget(budget_id, update_data):
        update_data['updated_at'] = datetime.now()
        return mongo.db.budgets.update_one(
            {'_id': ObjectId(budget_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete_budget(budget_id):
        return mongo.db.budgets.delete_one({'_id': ObjectId(budget_id)})