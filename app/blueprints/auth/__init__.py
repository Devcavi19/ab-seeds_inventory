from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.extensions import get_db
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = User.get_by_username(db, username)
        
        if user and user['is_active'] and User.verify_password(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_full_name'] = user['full_name']
            # Redirect to management users if admin, otherwise to a simple welcome page
            if user['role'] == 'admin':
                return redirect(url_for('management.users'))
            else:
                return redirect(url_for('auth.login'))
            
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))