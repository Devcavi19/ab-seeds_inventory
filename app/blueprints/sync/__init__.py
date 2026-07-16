from flask import Blueprint, current_app, jsonify
from app.auth import admin_required

bp = Blueprint('sync', __name__, url_prefix='/sync', template_folder='templates')


@bp.route('/status')
@admin_required
def sync_status():
    return jsonify(current_app.sync_service.get_status())


@bp.route('/now', methods=['POST'])
@admin_required
def sync_now():
    return jsonify(current_app.sync_service.sync_now())
