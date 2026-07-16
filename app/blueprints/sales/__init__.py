from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.stock import Stock
from app.auth import admin_required

bp = Blueprint('sales', __name__, url_prefix='/sales', template_folder='templates')

@bp.route('/')
@admin_required
def list_sales():
    db = get_db()
    sales = Sale.get_all(db)
    return render_template('sales/list.html', sales=sales)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_sale():
    db = get_db()
    customers = Customer.get_all(db)
    products = Product.get_all(db)

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        sale_number = request.form['sale_number']
        status = request.form['status']
        sale_date = request.form['sale_date']
        payment_method = request.form.get('payment_method', '')
        notes = request.form.get('notes', '')

        item_product_ids = request.form.getlist('item_product_id[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_unit_prices = request.form.getlist('item_unit_price[]')

        # Validate stock availability before creating anything
        for i in range(len(item_product_ids)):
            if item_product_ids[i] and item_quantities[i] and item_unit_prices[i]:
                product_id = item_product_ids[i]
                quantity = int(item_quantities[i])

                stock = Stock.get_by_product_id(db, product_id)
                available = stock['quantity'] if stock else 0
                if available < quantity:
                    product = Product.get_by_id(db, product_id)
                    product_name = product['name'] if product else product_id
                    flash(f'Insufficient stock for {product_name}. Available: {available}, requested: {quantity}.', 'error')
                    return render_template('sales/create.html', customers=customers, products=products)

        # Create sale
        sale = Sale.create(db, customer_id, sale_number, status, sale_date,
                          payment_method, 0.0, notes)

        # Process sale items
        total_amount = 0.0
        for i in range(len(item_product_ids)):
            if item_product_ids[i] and item_quantities[i] and item_unit_prices[i]:
                product_id = item_product_ids[i]
                quantity = int(item_quantities[i])
                unit_price = float(item_unit_prices[i])

                SaleItem.create(db, sale['id'], product_id, quantity, unit_price)
                total_amount += quantity * unit_price

        # Update total amount
        Sale.update_total_amount(db, sale['id'], total_amount)

        # Deduct stock only when the sale is completed
        if status == 'completed':
            for i in range(len(item_product_ids)):
                if item_product_ids[i] and item_quantities[i] and item_unit_prices[i]:
                    product_id = item_product_ids[i]
                    quantity = int(item_quantities[i])
                    Stock.adjust_quantity(db, product_id, -quantity)

        flash('Sale created successfully', 'success')
        return redirect(url_for('sales.list_sales'))

    return render_template('sales/create.html', customers=customers, products=products)

@bp.route('/<sale_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_sale(sale_id):
    db = get_db()
    sale = Sale.get_by_id(db, sale_id)
    customers = Customer.get_all(db)
    products = Product.get_all(db)
    items = SaleItem.get_by_sale_id(db, sale_id)

    if not sale:
        flash('Sale not found', 'error')
        return redirect(url_for('sales.list_sales'))

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        sale_number = request.form['sale_number']
        status = request.form['status']
        sale_date = request.form['sale_date']
        payment_method = request.form.get('payment_method', '')
        notes = request.form.get('notes', '')

        # Update sale
        Sale.update(db, sale_id, customer_id, sale_number, status, sale_date,
                    payment_method, sale['total_amount'], notes)

        # Process sale items - first delete existing items
        SaleItem.delete_by_sale_id(db, sale_id)

        # Then add new items
        item_product_ids = request.form.getlist('item_product_id[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_unit_prices = request.form.getlist('item_unit_price[]')

        total_amount = 0.0
        for i in range(len(item_product_ids)):
            if item_product_ids[i] and item_quantities[i] and item_unit_prices[i]:
                product_id = item_product_ids[i]
                quantity = int(item_quantities[i])
                unit_price = float(item_unit_prices[i])

                SaleItem.create(db, sale_id, product_id, quantity, unit_price)
                total_amount += quantity * unit_price

        # Update total amount
        Sale.update_total_amount(db, sale_id, total_amount)

        flash('Sale updated successfully', 'success')
        return redirect(url_for('sales.list_sales'))

    return render_template('sales/edit.html', sale=sale, customers=customers,
                          products=products, items=items)

@bp.route('/<sale_id>/view')
@admin_required
def view_sale(sale_id):
    db = get_db()
    sale = Sale.get_by_id(db, sale_id)
    items = SaleItem.get_by_sale_id(db, sale_id)

    if not sale:
        flash('Sale not found', 'error')
        return redirect(url_for('sales.list_sales'))

    return render_template('sales/view.html', sale=sale, items=items)

@bp.route('/<sale_id>/update-status', methods=['POST'])
@admin_required
def update_sale_status(sale_id):
    db = get_db()
    sale = Sale.get_by_id(db, sale_id)

    if not sale:
        flash('Sale not found', 'error')
        return redirect(url_for('sales.list_sales'))

    status = request.form['status']
    previous_status = sale['status']

    if status == 'completed' and previous_status != 'completed':
        items = SaleItem.get_by_sale_id(db, sale_id)

        # Check stock availability for every item before deducting anything
        for item in items:
            stock = Stock.get_by_product_id(db, item['product_id'])
            available = stock['quantity'] if stock else 0
            if available < item['quantity']:
                product = Product.get_by_id(db, item['product_id'])
                product_name = product['name'] if product else item['product_id']
                flash(f'Insufficient stock for {product_name}. Available: {available}, requested: {item["quantity"]}.', 'error')
                return redirect(url_for('sales.view_sale', sale_id=sale_id))

        for item in items:
            Stock.adjust_quantity(db, item['product_id'], -item['quantity'])

    Sale.update_status(db, sale_id, status)

    flash('Sale status updated successfully', 'success')
    return redirect(url_for('sales.view_sale', sale_id=sale_id))
