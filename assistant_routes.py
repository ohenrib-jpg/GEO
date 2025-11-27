# Flask/assistant_routes.py - VERSION SIMPLIFIÉE
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_assistant_blueprint(db_manager):
    assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/assistant')
    
    @assistant_bp.route('/chat', methods=['POST'])
    def assistant_chat():
        """Endpoint chat simple pour l'assistant"""
        try:
            data = request.json
            user_message = data.get('message', '').strip()
            page_type = data.get('page', 'generic')
            
            if not user_message:
                return jsonify({
                    'success': False, 
                    'error': 'Message vide',
                    'response': 'Veuillez poser une question.'
                })
            
            # Utiliser le client Mistral EXISTANT de l'app
            llama_client = current_app.config.get('LLAMA_CLIENT')
            if not llama_client:
                return jsonify({
                    'success': False,
                    'error': 'Client Mistral non configuré',
                    'response': 'Service temporairement indisponible.'
                })
            
            # Contexte basé sur la page
            context = {
                'page_type': page_type,
                'timestamp': datetime.now().isoformat()
            }
            
            # Générer la réponse
            result = llama_client.generate_chat_response(user_message, context)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur endpoint chat: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'response': "Désolé, une erreur s'est produite. Veuillez réessayer."
            })

    @assistant_bp.route('/status', methods=['GET'])
    def assistant_status():
        """Statut du serveur Mistral"""
        try:
            llama_client = current_app.config.get('LLAMA_CLIENT')
            if llama_client:
                connected, message = llama_client.test_connection()
                return jsonify({
                    'success': True,
                    'connected': connected,
                    'message': message
                })
            else:
                return jsonify({
                    'success': False,
                    'connected': False,
                    'message': 'Client non initialisé'
                })
                
        except Exception as e:
            logger.error(f"❌ Erreur statut: {e}")
            return jsonify({
                'success': False,
                'connected': False,
                'message': str(e)
            })

    return assistant_bp