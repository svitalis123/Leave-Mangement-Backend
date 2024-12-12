from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS  # Add this import
from config import Config
from flask_mail import Mail
import logging

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for all routes
    CORS(app, resources={
        r"/*": {
            "origins": "*",  # Allow all origins
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allow all methods
            "allow_headers": ["Content-Type", "Authorization"]  # Allow these headers
        }
    })

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # JWT configuration and error handlers
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        app.logger.error(f"Invalid token error: {error}")
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        app.logger.error(f"Unauthorized error: {error}")
        return jsonify({'error': 'Authorization header required'}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.employee import employee_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(employee_bp, url_prefix='/employee')

    return app