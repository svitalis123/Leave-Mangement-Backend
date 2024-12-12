# routes/admin_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, LeaveType, LeaveRequest
from auth import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_all_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_approved': user.is_approved,
        'created_at': user.created_at
    } for user in users]), 200

@admin_bp.route('/users/pending', methods=['GET'])
@jwt_required()
@admin_required()
def get_pending_users():
    users = User.query.filter_by(is_approved=False).all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at
    } for user in users]), 200

@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@jwt_required()
@admin_required()
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    
    # TODO: Send email notification
    return jsonify({"msg": "User approved successfully"}), 200

@admin_bp.route('/users/<int:user_id>/reject', methods=['POST'])
@jwt_required()
@admin_required()
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    # TODO: Send email notification
    return jsonify({"msg": "User rejected successfully"}), 200