from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if not user:
        user = User(username='admin', email='admin@example.com', role='admin', full_name='Admin User')
        user.set_password('admin')
        db.session.add(user)
        db.session.commit()
        print("Created admin user")
    else:
        user.set_password('admin')
        db.session.commit()
        print("Updated admin password to 'admin'")
