from datetime import datetime
from app import mongo
from bson import ObjectId

class Account:
    @staticmethod
    def create_account(user_id, name, type, balance=0, bank_name=None, last_four=None, details=None):
        account = {
            'user_id': ObjectId(user_id),
            'name': name,
            'type': type,
            'balance': float(balance),
            'bank_name': bank_name,
            'last_four': last_four,
            'details': details,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        return mongo.db.accounts.insert_one(account)
    
    @staticmethod
    def get_user_accounts(user_id):
        return list(mongo.db.accounts.find({'user_id': ObjectId(user_id)}))
    
    @staticmethod
    def get_account_by_id(account_id):
        return mongo.db.accounts.find_one({'_id': ObjectId(account_id)})
    
    @staticmethod
    def update_account_balance(account_id, amount):
        return mongo.db.accounts.update_one(
            {'_id': ObjectId(account_id)},
            {'$inc': {'balance': float(amount)}, '$set': {'updated_at': datetime.now()}}
        )
    
    @staticmethod
    def update_account(account_id, update_data):
        update_data['updated_at'] = datetime.now()
        return mongo.db.accounts.update_one(
            {'_id': ObjectId(account_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def delete_account(account_id):
        return mongo.db.accounts.delete_one({'_id': ObjectId(account_id)})