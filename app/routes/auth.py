# app/routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from app.models.models import User
from app import db
from app.utils.email import send_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Check existing username/email
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            role='employee'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()

        # Notify admins about new registration
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            send_email(
                admin.email,
                'New User Registration',
                f'New user {user.username} has registered and needs approval.'
            )
        
        return jsonify({'message': 'Registration successful, awaiting admin approval'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register/admin', methods=['POST'])
def register_admin():
    try:
        data = request.get_json()
        admin_secret = request.headers.get('Admin-Secret')
        
        if not admin_secret or admin_secret != current_app.config.get('ADMIN_SECRET_KEY', 'your-super-secret-admin-key'):
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Validate input
        if not all(key in data for key in ['username', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create admin user
        admin = User(
            username=data['username'],
            email=data['email'],
            role='admin',
            is_approved=True
        )
        admin.set_password(data['password'])
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Admin user created successfully',
            'user': {
                'username': admin.username,
                'email': admin.email,
                'role': admin.role
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in register_admin: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
            
        if not user.is_approved:
            return jsonify({'error': 'Account not approved yet'}), 403
        
        # Create token with string ID
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_approved': user.is_approved
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500