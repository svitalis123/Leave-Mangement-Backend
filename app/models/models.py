# app/models/models.py
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    role = db.Column(db.String, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    leave_requests = db.relationship('LeaveRequest', backref='user', lazy=True)
    leave_balances = db.relationship('LeaveBalance', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_approved': self.is_approved,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class LeaveType(db.Model):
    __tablename__ = 'leavetypes'
    
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    default_allocation = db.Column(db.Integer)  # New field
    requires_balance = db.Column(db.Boolean, default=True)  # New field
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    leave_requests = db.relationship('LeaveRequest', backref='leave_type', lazy=True)
    leave_balances = db.relationship('LeaveBalance', backref='leave_type', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'default_allocation': self.default_allocation,
            'requires_balance': self.requires_balance,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class LeaveRequest(db.Model):
    __tablename__ = 'leaverequests'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.BigInteger, db.ForeignKey('leavetypes.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String, nullable=False)
    reason = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'status': self.status,
            'reason': self.reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class LeaveBalance(db.Model):
    __tablename__ = 'leavebalances'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.BigInteger, db.ForeignKey('leavetypes.id'), nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name,
            'balance': self.balance,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }