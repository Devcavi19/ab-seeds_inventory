from flask import Blueprint, current_app, jsonify, render_template, request
from app.auth import admin_required
import json, os

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

@bp.route('/recover-wal', methods=['POST'])
@admin_required
def recover_wal():
    """Emergency WAL recovery endpoint.

    Call this when sync fails with "unable to checkpoint synced portion of WAL".
    It:
      1. Attempts a Turso-level checkpoint via the sync connection.
      2. Falls back to a raw SQLite PRAGMA wal_checkpoint(TRUNCATE) if (1) fails.
      3. Resets the stale `revert_since_wal_watermark` in local.db-info to 0
         so the next sync_now() can proceed cleanly.
    """
    import sqlite3 as _sqlite3

    steps = []
    errors = []

    # Step 1: Turso checkpoint
    sync_conn = getattr(current_app.sync_service, 'conn', None)
    if sync_conn is not None:
        try:
            sync_conn.checkpoint()
            steps.append('turso_checkpoint: ok')
        except Exception as exc:
            steps.append(f'turso_checkpoint: skipped ({exc})')
    else:
        steps.append('turso_checkpoint: no conn')

    # Step 2: Raw SQLite WAL truncate checkpoint (always safe when app has the lock)
    db_path = current_app.config['DATABASE_PATH']
    try:
        raw = _sqlite3.connect(db_path, timeout=5)
        result = raw.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
        raw.close()
        steps.append(f'sqlite_wal_checkpoint(TRUNCATE): busy={result[0]} log={result[1]} done={result[2]}')
    except Exception as exc:
        errors.append(f'sqlite_wal_checkpoint: {exc}')

    # Step 3: Patch revert_since_wal_watermark → 0 in local.db-info
    info_path = db_path + '-info'
    if os.path.exists(info_path):
        try:
            with open(info_path) as f:
                info = json.load(f)
            old = info.get('revert_since_wal_watermark')
            if old and old != 0:
                info['revert_since_wal_watermark'] = 0
                info['revert_since_wal_salt'] = None
                with open(info_path, 'w') as f:
                    json.dump(info, f)
                steps.append(f'patched revert_since_wal_watermark: {old} → 0')
            else:
                steps.append(f'revert_since_wal_watermark already clean ({old})')
        except Exception as exc:
            errors.append(f'patch_db_info: {exc}')
    else:
        steps.append('local.db-info not found, skipped patch')

    status = 'error' if errors else 'ok'
    return jsonify({'status': status, 'steps': steps, 'errors': errors})
