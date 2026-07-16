from flask import Blueprint, render_template, request
from app.extensions import get_db
from app.auth import admin_required
from app.models.sale import Sale
from app.models.purchase_order import PurchaseOrder
from app.models.stock import Stock
from app.models.product import Product
from app.services import report_service

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
