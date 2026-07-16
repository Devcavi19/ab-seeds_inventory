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

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})
        
    return app