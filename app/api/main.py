from flask import Blueprint, jsonify
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def api_info():
    """API information endpoint."""
    return jsonify({
        'name': 'Flask API',
        'version': '1.0.0',
        'description': 'A Flask API with blueprints and schema validation',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'auth': {
                'login': 'POST /api/auth/login',
                'register': 'POST /api/auth/register',
                'refresh': 'POST /api/auth/refresh',
                'me': 'GET /api/auth/me'
            },
            'users': {
                'list': 'GET /api/users/',
                'get': 'GET /api/users/<id>',
                'update': 'PUT /api/users/<id>',
                'delete': 'DELETE /api/users/<id>'
            },
            'employees': {
                'list': 'GET /api/employees/',
                'create': 'POST /api/employees/',
                'get': 'GET /api/employees/<id>',
                'update': 'PUT /api/employees/<id>',
                'delete': 'DELETE /api/employees/<id>',
                'add_project': 'POST /api/employees/<id>/projects',
                'remove_project': 'DELETE /api/employees/<id>/projects/<project_id>',
                'deactivate': 'POST /api/employees/<id>/deactivate',
                'reactivate': 'POST /api/employees/<id>/reactivate'
            },
            'health': 'GET /health'
        }
    }), 200

@main_bp.route('/status', methods=['GET'])
def status():
    """API status endpoint."""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'API is running normally'
    }), 200 