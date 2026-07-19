from flask import Blueprint, current_app, jsonify, render_template
from app.auth import admin_required

bp = Blueprint('sync', __name__, url_prefix='/sync', template_folder='templates')

@bp.route('/')
@bp.route('/status')
@admin_required
def sync_status():
    status = current_app.sync_service.get_status()
    return render_template('sync/index.html', status=status)

@bp.route('/api/status')
@admin_required
def sync_api_status():
    return jsonify(current_app.sync_service.get_status())

@bp.route('/now', methods=['POST'])
@admin_required
def sync_now():
    return jsonify(current_app.sync_service.sync_now())
