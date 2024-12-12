# app/routes/admin.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.models import User, LeaveType, LeaveRequest, LeaveBalance
from app import db
from app.utils.decorators import admin_required
import traceback
from datetime import datetime
from app.utils.email import send_email

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_users():
    print("Starting get_pending_users function")
    try:
        pending_users = User.query.filter_by(is_approved=False).all()
        print(f"Found {len(pending_users)} pending users")
        
        users_data = []
        for user in pending_users:
            print(f"Processing user: {user.username}")
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            users_data.append(user_data)
        
        print("Successfully prepared response")
        return jsonify(users_data), 200
    except Exception as e:
        print(f"Error in get_pending_users: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@jwt_required()
@admin_required
def approve_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        
        if user.is_approved:
            return jsonify({'message': 'User is already approved'}), 400
        
        user.is_approved = True
        db.session.commit()

         # Send approval email
        send_email(
            user.email,
            'Account Approved',
            'Your account has been approved. You can now login to the system.'
        )
        
        
        return jsonify({
            'message': 'User approved successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_approved': user.is_approved
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in approve_user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/leave-types', methods=['POST'])
@jwt_required()
@admin_required
def create_leave_type():
    try:
        data = request.get_json()
        
        if 'name' not in data:
            return jsonify({'error': 'Leave type name is required'}), 400
            
        leave_type = LeaveType(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(leave_type)
        db.session.commit()
        
        return jsonify({
            'message': 'Leave type created successfully',
            'leave_type': leave_type.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

@admin_bp.route('/leave-types', methods=['GET'])
@jwt_required()
@admin_required
def get_leave_types():
    try:
        leave_types = LeaveType.query.all()
        return jsonify([lt.to_dict() for lt in leave_types]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        print(f"Error in get_all_users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/leave-types/<int:type_id>/allocation', methods=['PUT'])
@jwt_required()
@admin_required
def update_leave_allocation(type_id):
    try:
        data = request.get_json()
        if 'default_allocation' not in data:
            return jsonify({'error': 'Default allocation is required'}), 400

        leave_type = LeaveType.query.get_or_404(type_id)
        if leave_type.name in ['Maternity Leave', 'Sick Leave']:
            return jsonify({'error': 'Cannot modify allocation for this leave type'}), 400

        leave_type.default_allocation = data['default_allocation']
        db.session.commit()

        return jsonify({
            'message': 'Leave allocation updated successfully',
            'leave_type': leave_type.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/leave-balance/set', methods=['POST'])
@jwt_required()
@admin_required
def set_leave_balance():
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['user_id', 'leave_type_id', 'balance']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        balance = LeaveBalance.query.filter_by(
            user_id=data['user_id'],
            leave_type_id=data['leave_type_id']
        ).first()
        
        if balance:
            balance.balance = data['balance']
        else:
            balance = LeaveBalance(
                user_id=data['user_id'],
                leave_type_id=data['leave_type_id'],
                balance=data['balance']
            )
            db.session.add(balance)
            
        db.session.commit()
        
        return jsonify({
            'message': 'Leave balance set successfully',
            'balance': balance.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    


@admin_bp.route('/leave-requests', methods=['GET'])
@jwt_required()
@admin_required
def get_all_leave_requests():
    try:
        status = request.args.get('status')
        query = LeaveRequest.query
        
        if status:
            query = query.filter_by(status=status)
            
        leave_requests = query.all()
        return jsonify([lr.to_dict() for lr in leave_requests]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@admin_bp.route('/leave-requests/<int:request_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_leave_request(request_id):
    try:
        leave_request = LeaveRequest.query.get_or_404(request_id)
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
            
        if data['status'] not in ['approved', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
            
        leave_request.status = data['status']
        leave_request.updated_at = datetime.utcnow()
        
        if data['status'] == 'approved':
            # Update leave balance
            balance = LeaveBalance.query.filter_by(
                user_id=leave_request.user_id,
                leave_type_id=leave_request.leave_type_id
            ).first()
            
            if balance:
                days_requested = (leave_request.end_date - leave_request.start_date).days + 1
                if balance.balance < days_requested:
                    return jsonify({'error': 'Insufficient leave balance'}), 400
                balance.balance -= days_requested
        
        db.session.commit()
        
        # Send email notification
        user = User.query.get(leave_request.user_id)
        send_email(
            user.email,
            'Leave Request Update',
            f'Your leave request for {leave_request.start_date} to {leave_request.end_date} has been {data["status"]}'
        )
        
        return jsonify({
            'message': 'Leave request updated successfully',
            'leave_request': leave_request.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/leave-types/setup-defaults', methods=['POST'])
@jwt_required()
@admin_required
def setup_default_leave_types():
    try:
        # Create default leave types if they don't exist
        default_types = [
            {
                'name': 'Annual Leave',
                'description': 'Regular annual leave',
                'default_allocation': 30,
                'requires_balance': True
            },
            {
                'name': 'Maternity Leave',
                'description': 'Three months maternity leave',
                'default_allocation': 90,  # 3 months in days
                'requires_balance': False
            },
            {
                'name': 'Sick Leave',
                'description': 'Medical leave',
                'default_allocation': None,
                'requires_balance': False
            }
        ]

        for leave_type_data in default_types:
            existing = LeaveType.query.filter_by(name=leave_type_data['name']).first()
            if not existing:
                leave_type = LeaveType(**leave_type_data)
                db.session.add(leave_type)

        db.session.commit()
        return jsonify({'message': 'Default leave types set up successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/test-db', methods=['GET'])
@jwt_required()
@admin_required
def test_db():
    try:
        # Test database connection
        user_count = User.query.count()
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful',
            'user_count': user_count
        }), 200
    except Exception as e:
        print(f"Database test error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500