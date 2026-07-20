from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    if test_config is None:
        app.config.from_object('app.config.DevConfig')
    else:
        app.config.from_mapping(test_config)
        
    from . import extensions
    extensions.init_db(app)

    # Sync service: optional background sync of the local SQLite file against
    # a Turso remote (embedded replica). No-op unless TURSO_DATABASE_URL /
    # TURSO_AUTH_TOKEN are configured and libsql-experimental is installed.
    from app.services.sync_service import SyncService
    app.sync_service = SyncService(
        database_path=app.config['DATABASE_PATH'],
        sync_url=app.config.get('TURSO_DATABASE_URL'),
        auth_token=app.config.get('TURSO_AUTH_TOKEN'),
    )

    # Run migrations unconditionally
    extensions.init_migrations(app)

    @app.before_request
    def start_background_services():
        if not getattr(app, '_background_services_started', False):
            app.sync_service.start()
            app._background_services_started = True

    # Register blueprints
    from app.blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.management import bp as management_bp
    app.register_blueprint(management_bp)
    
    from app.blueprints.categories import bp as categories_bp
    app.register_blueprint(categories_bp)
    
    from app.blueprints.products import bp as products_bp
    app.register_blueprint(products_bp)
    
    from app.blueprints.suppliers import bp as suppliers_bp
    app.register_blueprint(suppliers_bp)
    
    from app.blueprints.customers import bp as customers_bp
    app.register_blueprint(customers_bp)
    
    from app.blueprints.stock import bp as stock_bp
    app.register_blueprint(stock_bp)
    
    from app.blueprints.purchases import bp as purchases_bp
    app.register_blueprint(purchases_bp)

    from app.blueprints.sales import bp as sales_bp
    app.register_blueprint(sales_bp)

    from app.blueprints.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.blueprints.reports import bp as reports_bp
    app.register_blueprint(reports_bp)

    from app.blueprints.sync import bp as sync_bp
    app.register_blueprint(sync_bp)

    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}

    @app.template_filter('format_datetime')
    def format_datetime_filter(value):
        if not value:
            return ""
        from datetime import datetime, timezone, timedelta
        try:
            # Parse ISO 8601 string
            dt = datetime.fromisoformat(value)
            # Add UTC+8 (PST) if naive, or adjust if aware
            pst = timezone(timedelta(hours=8))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(pst)
            return dt.strftime("%m/%d/%Y %I:%M %p")
        except ValueError:
            return value

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})
        
    return app