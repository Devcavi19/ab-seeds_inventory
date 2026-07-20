from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.stock import Stock
from app.models.product import Product
from app.auth import admin_required
from app.utils.csv_export import generate_csv_response

bp = Blueprint('stock', __name__, url_prefix='/stock', template_folder='templates')

@bp.route('/')
@admin_required
def list_stock():
    db = get_db()
    stocks = Stock.get_all(db)
    # Enrich each stock entry with its product name
    enriched = []
    for stock in stocks:
        product = Product.get_by_id(db, stock['product_id'])
        stock = dict(stock)
        stock['product_name'] = product['name'] if product else stock['product_id']
        enriched.append(stock)
    return render_template('stock/list.html', stocks=enriched)

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
    enriched = []
    for stock in low_stocks:
        product = Product.get_by_id(db, stock['product_id'])
        stock = dict(stock)
        stock['product_name'] = product['name'] if product else stock['product_id']
        enriched.append(stock)
    return render_template('stock/low.html', stocks=enriched)

@bp.route('/export')
@admin_required
def export_csv():
    db = get_db()
    stocks = Stock.get_all(db)
    
    # Enrich each stock entry with its product name
    enriched = []
    for stock in stocks:
        product = Product.get_by_id(db, stock['product_id'])
        stock = dict(stock)
        stock['product_name'] = product['name'] if product else stock['product_id']
        enriched.append(stock)
    
    headers = ['ID', 'Product', 'Quantity', 'Lot Number', 'Expiry Date', 'Location']
    rows = []
    for stock in enriched:
        rows.append({
            'ID': stock['id'],
            'Product': stock['product_name'],
            'Quantity': stock['quantity'],
            'Lot Number': stock['lot_number'] or '',
            'Expiry Date': stock['expiry_date'] or '',
            'Location': stock['location'] or ''
        })
    
    return generate_csv_response('stock', headers, rows)
