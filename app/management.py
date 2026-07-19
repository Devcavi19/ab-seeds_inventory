from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.user import User
from app.auth import admin_required

bp = Blueprint('management', __name__, url_prefix='/management')

@bp.route('/users')
@admin_required
def users():
    db = get_db()
    users_list = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    
    # Convert tuples to dicts
    columns = [column[1] for column in db.execute("PRAGMA table_info(users)").fetchall()]
    users_dicts = [dict(zip(columns, row)) for row in users_list]
    
    return render_template('management/users.html', users=users_dicts)

@bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']
        
        db = get_db()
        
        # Check if username already exists
        existing_user = User.get_by_username(db, username)
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('management.create_user'))
        
        User.create(db, username, password, full_name, role)
        flash('User created successfully', 'success')
        return redirect(url_for('management.users'))
    
    return render_template('management/create_user.html')

@bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    db = get_db()
    user = User.get_by_id(db, user_id)
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('management.users'))
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        role = request.form['role']
        is_active = request.form.get('is_active') == 'on'
        
        # Update user
        db.execute(
            "UPDATE users SET full_name = ?, role = ?, is_active = ? WHERE id = ?",
            [full_name, role, is_active, user_id]
        )
        db.commit()
        
        flash('User updated successfully', 'success')
        return redirect(url_for('management.users'))
    
    return render_template('management/edit_user.html', user=user)

@bp.route('/users/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    db = get_db()
    user = User.get_by_id(db, user_id)
    
    if not user:
        flash('User not found', 'error')
    else:
        db.execute("DELETE FROM users WHERE id = ?", [user_id])
        db.commit()
        flash('User deleted successfully', 'success')
    
    return redirect(url_for('management.users'))