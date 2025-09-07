import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '1f2e3d4c5b6a7980a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6'
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/expense_tracker_db'
    MONGO_URI = MONGODB_URI  # Add this line for Flask-PyMongo compatibility
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or '9b8a7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_REFRESH_COOKIE_PATH = '/auth/refresh'
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = True  # Set to True in production with HTTPS