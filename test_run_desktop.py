import os
import tempfile

from app import create_app
from flaskwebgui import FlaskUI

import run_desktop


def _build_test_app():
    # Mirrors tests/conftest.py's `app` fixture test-config shape. A literal
    # ':memory:' DATABASE_PATH is not used here because app/extensions.py's
    # get_db() calls os.makedirs(os.path.dirname(DATABASE_PATH)) before
    # connecting, and os.path.dirname(':memory:') is '' -- os.makedirs('')
    # raises FileNotFoundError. That's a pre-existing quirk of get_db()
    # unrelated to build_ui(), so a real temp file path is used instead,
    # matching what the rest of the test suite already relies on.
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    app = create_app({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'TURSO_DATABASE_URL': None,
        'TURSO_AUTH_TOKEN': None,
        'SECRET_KEY': 'test-secret-key',
    })
    return app


def test_build_ui_returns_flaskui_instance_wrapping_app():
    app = _build_test_app()

    ui = run_desktop.build_ui(app)

    assert isinstance(ui, FlaskUI)
    assert ui.app is app


def test_build_ui_is_not_fullscreen():
    app = _build_test_app()

    ui = run_desktop.build_ui(app)

    assert not ui.fullscreen
