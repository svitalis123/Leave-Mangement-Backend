# app/routes/employee.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import User, LeaveRequest, LeaveBalance, LeaveType, Notification
from app import db
from datetime import datetime

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/leave-requests', methods=['POST'])
@jwt_required()
def create_leave_request():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['leave_type_id', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        if start_date > end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400

        leave_type = LeaveType.query.get_or_404(data['leave_type_id'])
        days_requested = (end_date - start_date).days + 1

        # Check balance only for leave types that require it
        if leave_type.requires_balance:
            balance = LeaveBalance.query.filter_by(
                user_id=current_user_id,
                leave_type_id=data['leave_type_id']
            ).first()
            
            if not balance:
                return jsonify({'error': 'No leave balance found for this leave type'}), 400
                
            if balance.balance < days_requested:
                return jsonify({'error': 'Insufficient leave balance'}), 400

        leave_request = LeaveRequest(
            user_id=current_user_id,
            leave_type_id=data['leave_type_id'],
            start_date=start_date,
            end_date=end_date,
            reason=data.get('reason', ''),
            status='pending'
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        return jsonify({
            'message': 'Leave request created successfully',
            'leave_request': leave_request.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/leave-requests', methods=['GET'])
@jwt_required()
def get_my_leave_requests():
    try:
        current_user_id = get_jwt_identity()
        status = request.args.get('status')
        
        query = LeaveRequest.query.filter_by(user_id=current_user_id)
        if status:
            query = query.filter_by(status=status)
            
        leave_requests = query.all()
        return jsonify([lr.to_dict() for lr in leave_requests]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/leave-balance', methods=['GET'])
@jwt_required()
def get_my_leave_balance():
    try:
        current_user_id = get_jwt_identity()
        balances = LeaveBalance.query.filter_by(user_id=current_user_id).all()
        return jsonify([balance.to_dict() for balance in balances]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_my_notifications():
    try:
        current_user_id = get_jwt_identity()
        notifications = Notification.query.filter_by(
            user_id=current_user_id,
            is_read=False
        ).all()
        return jsonify([notif.to_dict() for notif in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    try:
        current_user_id = get_jwt_identity()
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first_or_404()
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500