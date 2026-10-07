from flask import Flask
from flask_login import LoginManager
from app.models import db, User

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'bugflow_enterprise_secret_2026'
    
    # PostgreSQL credentials
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/bugflow_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.developer import developer_bp
    from app.routes.tester import tester_bp
    from app.routes.admin import admin_bp
    from app.routes.sprint import sprint_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(developer_bp)
    app.register_blueprint(tester_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sprint_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    return app