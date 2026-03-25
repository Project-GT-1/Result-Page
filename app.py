from flask import Flask
from flask_cors import CORS
from models.database import db
from routes.results import results_bp
from routes.admin import admin_bp
from routes.analytics import analytics_bp
import os

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Config
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(BASE_DIR, 'results.db')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB max upload

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(results_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    # Create tables
    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health():
        return {'status': 'ok'}, 200

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
