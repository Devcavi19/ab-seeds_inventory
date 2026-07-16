from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.stock import Stock
from app.models.product import Product
from app.auth import admin_required

bp = Blueprint('stock', __name__, url_prefix='/stock', template_folder='templates')

@bp.route('/')
@admin_required
def list_stock():
    db = get_db()
    stocks = Stock.get_all(db)
    return render_template('stock/list.html', stocks=stocks)

@bp.route('/<product_id>/create', methods=['GET', 'POST'])
@admin_required
def create_stock(product_id):
    db = get_db()
    product = Product.get_by_id(db, product_id)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('stock.list_stock'))
    
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        lot_number = request.form['lot_number']
        expiry_date = request.form['expiry_date']
        location = request.form['location']
        
        Stock.upsert(db, product_id, quantity, lot_number, expiry_date, location)
        flash('Stock created successfully', 'success')
        return redirect(url_for('stock.list_stock'))
    
    return render_template('stock/create.html', product=product)

@bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_stock(product_id):
    db = get_db()
    stock = Stock.get_by_product_id(db, product_id)
    product = Product.get_by_id(db, product_id)
    
    if not stock or not product:
        flash('Stock or product not found', 'error')
        return redirect(url_for('stock.list_stock'))
    
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        lot_number = request.form['lot_number']
        expiry_date = request.form['expiry_date']
        location = request.form['location']
        
        Stock.upsert(db, product_id, quantity, lot_number, expiry_date, location)
        flash('Stock updated successfully', 'success')
        return redirect(url_for('stock.list_stock'))
    
    return render_template('stock/edit.html', stock=stock, product=product)

@bp.route('/<product_id>/adjust', methods=['GET', 'POST'])
@admin_required
def adjust_stock(product_id):
    db = get_db()
    stock = Stock.get_by_product_id(db, product_id)
    product = Product.get_by_id(db, product_id)
    
    if not stock or not product:
        flash('Stock or product not found', 'error')
        return redirect(url_for('stock.list_stock'))
    
    if request.method == 'POST':
        adjustment = int(request.form['adjustment'])
        reason = request.form.get('reason', '')
        
        Stock.adjust_quantity(db, product_id, adjustment)
        flash(f'Stock adjusted successfully: {adjustment} units', 'success')
        return redirect(url_for('stock.list_stock'))
    
    return render_template('stock/adjust.html', stock=stock, product=product)

@bp.route('/low')
@admin_required
def low_stock():
    db = get_db()
    low_stocks = Stock.get_low_stock(db, 20)  # Threshold of 20
    return render_template('stock/low.html', stocks=low_stocks)