from app import create_app
from flaskwebgui import FlaskUI


def build_ui(app):
    return FlaskUI(app=app, server="flask", width=1280, height=800, fullscreen=False)


if __name__ == '__main__':
    app = create_app()
    ui = build_ui(app)
    ui.run()
