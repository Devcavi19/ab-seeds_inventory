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

    import os
    is_master_process = os.environ.get('WERKZEUG_RUN_MAIN') != 'true' and app.debug
    
    if not is_master_process:
        # Sync service: optional background sync of the local SQLite file against
        # a Turso remote (embedded replica). No-op unless TURSO_DATABASE_URL /
        # TURSO_AUTH_TOKEN are configured and libsql-experimental is installed.
        from app.services.sync_service import SyncService
        app.sync_service = SyncService(
            database_path=app.config['DATABASE_PATH'],
            sync_url=app.config.get('TURSO_DATABASE_URL'),
            auth_token=app.config.get('TURSO_AUTH_TOKEN'),
        )

        # Run migrations
        extensions.init_migrations(app)
        
        # Start background sync
        app.sync_service.start()
    else:
        # Dummy service for the master process which just watches files
        class DummySync:
            conn = None
        app.sync_service = DummySync()

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

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})
        
    return app