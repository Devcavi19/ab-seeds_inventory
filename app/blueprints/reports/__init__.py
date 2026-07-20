from flask import Blueprint, render_template, request
from app.extensions import get_db
from app.auth import admin_required
from app.models.sale import Sale
from app.models.purchase_order import PurchaseOrder
from app.models.stock import Stock
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.customer import Customer
from app.services import report_service
from app.utils.csv_export import generate_csv_response

bp = Blueprint('reports', __name__, url_prefix='/reports', template_folder='templates')

@bp.route('/sales')
@admin_required
def sales_report():
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    sales = Sale.get_all(db)
    if start_date and end_date:
        sales = [s for s in sales if start_date <= s['sale_date'] <= end_date]

    total_amount = report_service.get_total_sales_amount(db, start_date, end_date)

    return render_template(
        'reports/sales.html',
        sales=sales,
        total_amount=total_amount,
        start_date=start_date,
        end_date=end_date,
    )

@bp.route('/purchases')
@admin_required
def purchases_report():
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    orders = PurchaseOrder.get_all(db)
    if start_date and end_date:
        orders = [o for o in orders if start_date <= o['order_date'] <= end_date]

    total_amount = report_service.get_total_purchases_amount(db, start_date, end_date)

    return render_template(
        'reports/purchases.html',
        orders=orders,
        total_amount=total_amount,
        start_date=start_date,
        end_date=end_date,
    )

@bp.route('/stock')
@admin_required
def stock_report():
    db = get_db()
    stocks = Stock.get_all(db)
    products = Product.get_all(db)
    products_by_id = {p['id']: p for p in products}

    stock_items = []
    for stock in stocks:
        product = products_by_id.get(stock['product_id'])
        stock_item = dict(stock)
        stock_item['product_name'] = product['name'] if product else 'Unknown'
        stock_items.append(stock_item)

    return render_template('reports/stock.html', stock_items=stock_items)


@bp.route('/sales/export')
@admin_required
def export_sales_report_csv():
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    sales = Sale.get_all(db)
    if start_date and end_date:
        sales = [s for s in sales if start_date <= s['sale_date'] <= end_date]
    
    headers = ['ID', 'Sale Number', 'Customer', 'Status', 'Sale Date', 'Payment Method', 'Total Amount']
    rows = []
    for sale in sales:
        rows.append({
            'ID': sale['id'],
            'Sale Number': sale['sale_number'],
            'Customer': sale['customer_name'] or sale['customer_id'] or 'Walk-in',
            'Status': sale['status'],
            'Sale Date': sale['sale_date'],
            'Payment Method': sale['payment_method'] or '',
            'Total Amount': f"₱{sale['total_amount']:.2f}" if sale['total_amount'] else "₱0.00"
        })
    
    return generate_csv_response('sales_report', headers, rows)


@bp.route('/purchases/export')
@admin_required
def export_purchases_report_csv():
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    orders = PurchaseOrder.get_all(db)
    
    # Enrich with supplier names
    enriched = []
    for order in orders:
        supplier = Supplier.get_by_id(db, order['supplier_id'])
        order = dict(order)
        order['supplier_name'] = supplier['name'] if supplier else order['supplier_id']
        enriched.append(order)
    
    if start_date and end_date:
        enriched = [o for o in enriched if start_date <= o['order_date'] <= end_date]
    
    headers = ['ID', 'Order Number', 'Supplier', 'Status', 'Order Date', 'Received Date', 'Total Amount']
    rows = []
    for order in enriched:
        rows.append({
            'ID': order['id'],
            'Order Number': order['order_number'],
            'Supplier': order['supplier_name'],
            'Status': order['status'],
            'Order Date': order['order_date'],
            'Received Date': order['received_date'] or '',
            'Total Amount': f"₱{order['total_amount']:.2f}" if order['total_amount'] else "₱0.00"
        })
    
    return generate_csv_response('purchases_report', headers, rows)


@bp.route('/stock/export')
@admin_required
def export_stock_report_csv():
    db = get_db()
    stocks = Stock.get_all(db)
    products = Product.get_all(db)
    products_by_id = {p['id']: p for p in products}
    
    stock_items = []
    for stock in stocks:
        product = products_by_id.get(stock['product_id'])
        stock_item = dict(stock)
        stock_item['product_name'] = product['name'] if product else 'Unknown'
        stock_items.append(stock_item)
    
    headers = ['ID', 'Product', 'Quantity', 'Lot Number', 'Expiry Date', 'Location']
    rows = []
    for item in stock_items:
        rows.append({
            'ID': item['id'],
            'Product': item['product_name'],
            'Quantity': item['quantity'],
            'Lot Number': item['lot_number'] or '',
            'Expiry Date': item['expiry_date'] or '',
            'Location': item['location'] or ''
        })
    
    return generate_csv_response('stock_report', headers, rows)
