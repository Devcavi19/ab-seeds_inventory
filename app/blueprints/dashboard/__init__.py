from flask import Blueprint, render_template
from app.extensions import get_db
from app.auth import login_required
from app.services import report_service

bp = Blueprint('dashboard', __name__, template_folder='templates')

@bp.route('/')
@login_required
def index():
    db = get_db()
    summary = report_service.get_summary_counts(db)
    total_sales_amount = report_service.get_total_sales_amount(db)
    total_purchases_amount = report_service.get_total_purchases_amount(db)
    sales_by_day = report_service.get_sales_by_day(db, 7)
    top_products = report_service.get_top_selling_products(db, 5)
    low_stock_items = report_service.get_low_stock_items(db)

    return render_template(
        'dashboard/index.html',
        summary=summary,
        total_sales_amount=total_sales_amount,
        total_purchases_amount=total_purchases_amount,
        sales_by_day=sales_by_day,
        top_products=top_products,
        low_stock_items=low_stock_items,
    )
