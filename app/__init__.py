import os
from flask import Flask, render_template
from flask_login import LoginManager
from dotenv import load_dotenv

# Load env variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.settings.Config')
    
    # Create upload subdirectories — wrapped in try/except for read-only filesystems (e.g. Vercel)
    upload_folder = app.config['UPLOAD_FOLDER']
    for sub in ['', 'resume', 'audio', 'reports']:
        try:
            os.makedirs(os.path.join(upload_folder, sub), exist_ok=True)
        except OSError:
            pass

    # Initialize Database
    from app.models.database import db, User
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register Blueprints
    from app.routes import auth_bp, resume_bp, interview_bp, dashboard_bp, analytics_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(interview_bp, url_prefix='/interview')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    
    # Root Landing Page
    @app.route('/')
    def landing():
        return render_template('landing.html')
        
    # Register Error Handlers
    from app.error_handlers import register_error_handlers
    register_error_handlers(app)
        
    # Global HTTP Context Processor to check settings / theme
    @app.context_processor
    def inject_global_settings():
        from app.models.database import Setting
        from flask_login import current_user
        
        dark_mode = True
        if current_user.is_authenticated:
            set_item = Setting.query.filter_by(user_id=current_user.id).first()
            if set_item:
                dark_mode = set_item.dark_mode
        return dict(dark_mode=dark_mode)

    # Initialize tables (non-blocking — failure won't crash the app startup)
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization error (non-fatal): {e}")
            
    return app
