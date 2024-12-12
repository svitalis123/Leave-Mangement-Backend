# app/utils/decorators.py
from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from app.models.models import User

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_user_id = get_jwt_identity()
            current_app.logger.debug(f"JWT identity: {current_user_id}")
            
            # Convert string ID back to integer
            user_id = int(current_user_id)
            user = User.query.get(user_id)
            
            if not user or user.role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Admin decorator error: {str(e)}")
            return jsonify({'error': 'Authorization error'}), 401
    return decorated_function