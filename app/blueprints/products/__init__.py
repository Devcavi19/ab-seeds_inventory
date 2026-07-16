from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.product import Product
from app.models.category import Category
from app.auth import admin_required
from werkzeug.utils import secure_filename
import os

bp = Blueprint('products', __name__, url_prefix='/products', template_folder='templates')

@bp.route('/')
@admin_required
def list_products():
    db = get_db()
    search_query = request.args.get('search', '')
    category_id = request.args.get('category_id')
    
    categories = Category.get_all(db)
    
    if search_query:
        products = Product.search(db, search_query)
    elif category_id:
        products = Product.get_by_category(db, category_id)
    else:
        products = Product.get_all(db)
    
    # Get category names for display
    category_map = {cat['id']: cat['name'] for cat in categories}
    
    return render_template('products/list.html', products=products, categories=categories, 
                         category_map=category_map, search_query=search_query, 
                         selected_category_id=category_id)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_product():
    db = get_db()
    categories = Category.get_all(db)
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        category_id = request.form['category_id']
        
        # Handle file upload
        image_file = request.files.get('image')
        
        Product.create(db, name, description, price, stock_quantity, category_id, image_file)
        flash('Product created successfully', 'success')
        return redirect(url_for('products.list_products'))
    
    return render_template('products/create.html', categories=categories)

@bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    product = Product.get_by_id(db, product_id)
    categories = Category.get_all(db)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('products.list_products'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        category_id = request.form['category_id']
        
        # Handle file upload
        image_file = request.files.get('image')
        
        Product.update(db, product_id, name, description, price, stock_quantity, category_id, image_file)
        flash('Product updated successfully', 'success')
        return redirect(url_for('products.list_products'))
    
    return render_template('products/edit.html', product=product, categories=categories)

@bp.route('/<product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    db = get_db()
    product = Product.get_by_id(db, product_id)
    
    if not product:
        flash('Product not found', 'error')
    else:
        Product.soft_delete(db, product_id)
        flash('Product deleted successfully', 'success')
    
    return redirect(url_for('products.list_products'))