from flask import Flask, render_template, request, redirect, url_for, current_app
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity
from flask_login import LoginManager, current_user
import redis
import traceback
from functools import wraps
from config import Config
from bson import ObjectId

# Constants
AUTH_LOGIN_ENDPOINT = 'auth.login'
API_PREFIX = '/api/'
AUTH_PREFIX = '/auth/'
STATIC_ENDPOINT = 'static'
FAVICON_PATH = '/favicon.ico'

mongo = PyMongo()
jwt = JWTManager()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
redis_client = None

def setup_jwt(app):
    """Configure JWT settings and error handlers."""
    def redirect_to_login(callback=None):
        """Helper function to redirect to login page."""
        return redirect(url_for(AUTH_LOGIN_ENDPOINT))
    
    jwt.unauthorized_loader(redirect_to_login)
    jwt.invalid_token_loader(redirect_to_login)
    jwt.expired_token_loader(lambda *args: redirect_to_login())
    
    return app

def register_blueprints(app):
    """Register all blueprints with the Flask application."""
    from app.auth.routes import auth_bp
    from app.routes.main import main_bp
    from app.routes.transactions import transactions_bp
    from app.routes.accounts import accounts_bp
    from app.routes.budgets import budgets_bp
    from app.routes.charts import charts_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix=AUTH_PREFIX)
    
    # Protected routes (require authentication)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp, url_prefix=f'{API_PREFIX}transactions')
    app.register_blueprint(accounts_bp, url_prefix=f'{API_PREFIX}accounts')
    app.register_blueprint(budgets_bp, url_prefix=f'{API_PREFIX}budgets')
    app.register_blueprint(charts_bp, url_prefix=f'{API_PREFIX}charts')
    
    return app

def create_api_error_response(message, status_code, error=None, include_trace=False, app=None):
    """Helper function to format API error responses."""
    response = {'message': message}
    if error:
        response['error'] = str(error)
    if include_trace and app and app.debug:
        response['trace'] = traceback.format_exc()
    return response, status_code

def handle_api_error(error, status_code, default_message, template_name=None):
    """Handle API errors with appropriate response format."""
    if request.path.startswith(API_PREFIX):
        return create_api_error_response(
            default_message,
            status_code,
            error,
            include_trace=(status_code == 500)
        )
    if template_name:
        error_trace = traceback.format_exc() if status_code == 500 and current_app.debug else None
        return render_template(f'errors/{template_name}.html', error=error_trace), status_code
    return redirect(url_for(AUTH_LOGIN_ENDPOINT))

def setup_error_handlers(app):
    """Set up error handlers for the Flask application."""
    # Register error handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return handle_api_error(error, 400, 'Bad request', '400')
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return handle_api_error(error, 401, 'Unauthorized')
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return handle_api_error(error, 403, 'Forbidden', '403')
    
    @app.errorhandler(404)
    def not_found_error(error):
        return handle_api_error(error, 404, 'Resource not found', '404')
    
    @app.errorhandler(500)
    def internal_error(error):
        return handle_api_error(error, 500, 'Internal server error', '500')
    
    return app
    
def is_public_route(app):
    """Check if the current route is public and doesn't require authentication."""
    public_paths = {
        '/',
        f'{API_PREFIX}docs',
        FAVICON_PATH
    }
    
    # Check static and auth routes
    if (request.endpoint == STATIC_ENDPOINT or 
        request.path.startswith(AUTH_PREFIX)):
        return True
    
    # Check public paths
    if any(request.path == path or 
           (path.endswith('/') and request.path.startswith(path)) 
           for path in public_paths):
        return True
        
    # Check view exemption
    view = app.view_functions.get(request.endpoint)
    return (view and hasattr(view, 'view_class') and 
            hasattr(view.view_class, '__is_exempt__'))

def handle_unauthorized():
    """Handle unauthorized access attempts."""
    if request.path.startswith(API_PREFIX):
        return api_error_response('Unauthorized', 401, 'Invalid or expired token')
    return redirect(url_for(AUTH_LOGIN_ENDPOINT, next=request.url))

def setup_request_handlers(app):
    """Set up request handlers including authentication and error handling."""
    @app.before_request
    def check_authentication():
        if not is_public_route(app):
            try:
                verify_jwt_in_request(optional=True)
                if not get_jwt_identity():
                    return handle_unauthorized()
            except Exception:
                return handle_unauthorized()
    
    return app

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    mongo.init_app(app)
    jwt.init_app(app)
    login_manager.init_app(app)
    
    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(user_data)
        except (TypeError, ValueError) as e:
            current_app.logger.error(f"Error loading user {user_id}: {e}")
            return None
        except Exception as e:
            current_app.logger.error(f"Unexpected error loading user {user_id}: {e}")
            return None
        return None
    
    global redis_client
    redis_client = redis.Redis.from_url(app.config['REDIS_URL'])
    
    # Configure JWT
    setup_jwt(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup request handlers
    setup_request_handlers(app)
    
    return app