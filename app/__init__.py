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
    
    # Run migrations
    extensions.init_migrations(app)

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

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})
        
    return app