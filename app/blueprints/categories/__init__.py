from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.category import Category
from app.models.product import Product
from app.auth import admin_required

bp = Blueprint('categories', __name__, url_prefix='/categories', template_folder='templates')

@bp.route('/')
@admin_required
def list_categories():
    db = get_db()
    categories = Category.get_all(db)
    return render_template('categories/list.html', categories=categories)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_category():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        db = get_db()
        Category.create(db, name, description)
        flash('Category created successfully', 'success')
        return redirect(url_for('categories.list_categories'))
    
    return render_template('categories/create.html')

@bp.route('/<category_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    db = get_db()
    category = Category.get_by_id(db, category_id)
    
    if not category:
        flash('Category not found', 'error')
        return redirect(url_for('categories.list_categories'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        Category.update(db, category_id, name, description)
        flash('Category updated successfully', 'success')
        return redirect(url_for('categories.list_categories'))
    
    return render_template('categories/edit.html', category=category)

@bp.route('/<category_id>/delete', methods=['POST'])
@admin_required
def delete_category(category_id):
    db = get_db()
    category = Category.get_by_id(db, category_id)
    
    if not category:
        flash('Category not found', 'error')
    else:
        products = Product.get_by_category(db, category_id)
        if products:
            flash(f'Cannot delete category: {len(products)} active products are still using it.', 'error')
        else:
            Category.soft_delete(db, category_id)
            flash('Category deleted successfully', 'success')
    
    return redirect(url_for('categories.list_categories'))