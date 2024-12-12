# routes/employee_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import db, LeaveRequest, LeaveBalance
from auth import approved_user_required

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/leave-request', methods=['POST'])
@approved_user_required()
def request_leave():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate leave balance
    balance = LeaveBalance.query.filter_by(
        user_id=user_id,
        leave_type_id=data['leave_type_id']
    ).first()
    
    if not balance or balance.balance <= 0:
        return jsonify({"msg": "Insufficient leave balance"}), 400
    
    leave_request = LeaveRequest(
        user_id=user_id,
        leave_type_id=data['leave_type_id'],
        start_date=data['start_date'],
        end_date=data['end_date'],
        reason=data.get('reason'),
        status='pending'
    )
    
    db.session.add(leave_request)
    db.session.commit()
    
    return jsonify({"msg": "Leave request submitted"}), 201

@employee_bp.route('/leave-balance', methods=['GET'])
@approved_user_required()
def get_leave_balance():
    user_id = get_jwt_identity()
    balances = LeaveBalance.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'type': balance.leave_type.name,
        'balance': balance.balance
    } for balance in balances]), 200