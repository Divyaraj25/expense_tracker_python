from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, set_access_cookies, set_refresh_cookies, unset_jwt_cookies
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import redis_client, login_manager

auth_bp = Blueprint('auth', __name__)

@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith('/api/'):
        return jsonify({'message': 'Unauthorized'}), 401
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('auth.login', next=request.path))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    
    user_data = User.find_by_username(username)
    if not user_data or not User.verify_password(user_data['password'], password):
        if request.is_json:
            return jsonify({'message': 'Invalid credentials'}), 401
        flash('Invalid username or password', 'danger')
        return render_template('auth/login.html', username=username)
    
    # Create user object and log them in
    user = User(user_data)
    login_user(user)
    
    # Create JWT tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    if request.is_json:
        response = jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        })
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response, 200
    
    next_page = request.args.get('next')
    flash('You have been logged in!', 'success')
    return redirect(next_page or url_for('main.dashboard'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    # Validation
    errors = {}
    if not username or len(username) < 3:
        errors['username'] = 'Username must be at least 3 characters long'
    if not email or '@' not in email:
        errors['email'] = 'Please enter a valid email address'
    if not password or len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters long'
    if password != confirm_password:
        errors['confirm_password'] = 'Passwords do not match'
    
    if User.find_by_username(username):
        errors['username'] = 'Username already exists'
    if User.find_by_email(email):
        errors['email'] = 'Email already registered'
    
    if errors:
        if request.is_json:
            return jsonify({'message': 'Validation failed', 'errors': errors}), 400
        return render_template('auth/register.html', 
                             username=username, 
                             email=email,
                             errors=errors)
    
    # Create new user
    user_id = User.create(username, email, password)
    user_data = User.find_by_id(user_id)
    user = User(user_data)
    
    # Log the user in
    login_user(user)
    
    if request.is_json:
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
    
    flash('Registration successful! You are now logged in.', 'success')
    return redirect(url_for('main.dashboard'))

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    response = jsonify({'message': 'Token refreshed'})
    set_access_cookies(response, new_token)
    return response, 200

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    response = redirect(url_for('auth.login'))
    
    # Clear JWT cookies if they exist
    if request.cookies.get('access_token_cookie'):
        unset_jwt_cookies(response)
    
    flash('You have been logged out.', 'info')
    return response