"""
WebPulse Application Factory
Configures and initializes Flask, extensions, blueprints, and security policies.
"""
import os
from datetime import datetime
from flask import Flask
from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf


import mimetypes
mimetypes.add_type('application/javascript', '.jsx')
mimetypes.add_type('application/javascript', '.js')


def create_app(config_name: str = None) -> Flask:
    """Create and configure an instance of the WebPulse Flask application."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_class)

    # Initialize configuration hooks (storage directories, etc.)
    config_class.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.errors import errors_bp
    from app.projects import projects_bp
    from app.analysis import analysis_bp
    from app.performance import performance_bp
    from app.recommendations import recommendations_bp
    from app.reports import reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(reports_bp)

    # Register Context Processors
    @app.context_processor
    def inject_global_variables():
        return {
            'current_year': datetime.now().year,
            'app_name': 'WebPulse',
            'app_tagline': 'Website Performance Analyzer & Optimization Lab',
            'analyzer_version': '1.0.0-dev'
        }

    # Security Headers
    @app.after_request
    def set_security_headers(response):
        from flask import request
        if request.path.endswith('.jsx') or request.path.endswith('.js'):
            response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    return app

