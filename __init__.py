from .websdr_routes import websdr_bp

def create_app():
    app = Flask(__name__)
    
    # Enregistrer les blueprints
    app.register_blueprint(websdr_bp, url_prefix='/api')
    # ... autres blueprints
    
    return app