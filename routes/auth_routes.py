# routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from models import db, User
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "Email already registered"}), 400
    
    # Check if this is the first user (make them admin)
    is_first_user = User.query.count() == 0
    
    user = User(
        username=data['username'],
        email=data['email'],
        role='admin' if is_first_user else 'employee',
        is_approved=is_first_user  # First user is automatically approved
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "msg": "Registration successful",
        "is_admin": is_first_user,
        "needs_approval": not is_first_user
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({"msg": "Invalid credentials"}), 401
    
    if not user.is_approved:
        return jsonify({"msg": "Account pending approval"}), 403
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }), 200