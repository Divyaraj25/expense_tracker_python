from datetime import datetime
from app import mongo
from bson import ObjectId

class Transaction:
    DEFAULT_CATEGORIES = {
        'expense': ['Food', 'Transport', 'Entertainment', 'Utilities', 'Rent', 'Shopping', 'Healthcare', 'Education'],
        'income': ['Salary', 'Freelance', 'Investment', 'Gift', 'Bonus'],
        'transfer': ['Between Accounts']
    }
    
    @staticmethod
    def create_transaction(user_id, type, amount, category, description, account_from=None, account_to=None, date=None):
        transaction = {
            'user_id': ObjectId(user_id),
            'type': type,
            'amount': float(amount),
            'category': category,
            'description': description,
            'account_from': ObjectId(account_from) if account_from else None,
            'account_to': ObjectId(account_to) if account_to else None,
            'date': date or datetime.now(),
            'created_at': datetime.now()
        }
        return mongo.db.transactions.insert_one(transaction)
    
    @staticmethod
    def get_user_transactions(user_id, limit=50, skip=0, filters=None):
        query = {'user_id': ObjectId(user_id)}
        if filters:
            if 'type' in filters:
                query['type'] = filters['type']
            if 'category' in filters:
                query['category'] = filters['category']
            if 'start_date' in filters and 'end_date' in filters:
                query['date'] = {'$gte': filters['start_date'], '$lte': filters['end_date']}
        
        return list(mongo.db.transactions.find(query).sort('date', -1).limit(limit).skip(skip))
    
    @staticmethod
    def get_transaction_by_id(transaction_id):
        return mongo.db.transactions.find_one({'_id': ObjectId(transaction_id)})
    
    @staticmethod
    def update_transaction(transaction_id, update_data):
        return mongo.db.transactions.update_one({'_id': ObjectId(transaction_id)}, {'$set': update_data})
    
    @staticmethod
    def delete_transaction(transaction_id):
        return mongo.db.transactions.delete_one({'_id': ObjectId(transaction_id)})
    
    @staticmethod
    def get_transactions_by_type(user_id, type, start_date=None, end_date=None):
        query = {'user_id': ObjectId(user_id), 'type': type}
        if start_date and end_date:
            query['date'] = {'$gte': start_date, '$lte': end_date}
        return list(mongo.db.transactions.find(query))
    
    @staticmethod
    def get_transactions_by_category(user_id, category, start_date=None, end_date=None):
        query = {'user_id': ObjectId(user_id), 'category': category}
        if start_date and end_date:
            query['date'] = {'$gte': start_date, '$lte': end_date}
        return list(mongo.db.transactions.find(query))