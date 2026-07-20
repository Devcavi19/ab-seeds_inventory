from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.stock import Stock
from app.auth import admin_required

bp = Blueprint('sales', __name__, url_prefix='/sales', template_folder='templates')


def _validate_and_aggregate_line_items(db, product_ids, quantities, unit_prices=None):
    """
    Validate a set of sale line items and aggregate the requested quantity per
    product_id, so that multiple line items for the same product in one request
    are checked against stock jointly rather than independently.

    `product_ids`, `quantities`, and (optionally) `unit_prices` are parallel
    lists already narrowed down to the "real" line items to validate - callers
    are responsible for filtering out blank/incomplete form rows first.

    Validates, in order, for every line item:
      - quantity must be > 0 (a negative or zero quantity would otherwise pass
        the oversell check and then inflate stock via Stock.adjust_quantity)
      - unit_price must be >= 0, when unit_prices is provided

    Then checks each product's *total* requested quantity (summed across all
    of its line items) against current stock.

    Returns (requested_by_product, None) on success, where requested_by_product
    maps product_id -> total requested quantity. Returns (None, error_message)
    on the first validation failure. Never mutates stock.
    """
    requested_by_product = {}

    for i in range(len(product_ids)):
        product_id = product_ids[i]
        quantity = int(quantities[i])

        if quantity <= 0:
            return None, f'Invalid quantity ({quantity}). Quantity must be greater than zero.'

        if unit_prices is not None:
            unit_price = float(unit_prices[i])
            if unit_price < 0:
                return None, f'Invalid unit price ({unit_price}). Unit price cannot be negative.'

        requested_by_product[product_id] = requested_by_product.get(product_id, 0) + quantity

    for product_id, total_requested in requested_by_product.items():
        stock = Stock.get_by_product_id(db, product_id)
        available = stock['quantity'] if stock else 0
        if available < total_requested:
            product = Product.get_by_id(db, product_id)
            product_name = product['name'] if product else product_id
            return None, f'Insufficient stock for {product_name}. Available: {available}, requested: {total_requested}.'

    return requested_by_product, None

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
        customer_id = request.form.get('customer_id')
        if not customer_id:
            customer_id = None
        sale_number = request.form['sale_number']
        status = request.form['status']
        sale_date = request.form['sale_date']
        payment_method = request.form.get('payment_method', '')
        notes = request.form.get('notes', '')

        item_product_ids = request.form.getlist('item_product_id[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_unit_prices = request.form.getlist('item_unit_price[]')

        # Narrow down to the "real" line items (skip blank/incomplete form rows) -
        # both the validation pass and the creation pass below must consider the
        # exact same set of rows.
        valid_indices = [i for i in range(len(item_product_ids))
                          if item_product_ids[i] and item_quantities[i] and item_unit_prices[i]]

        # Validate quantities/prices and stock availability before creating anything
        requested_by_product, error = _validate_and_aggregate_line_items(
            db,
            [item_product_ids[i] for i in valid_indices],
            [item_quantities[i] for i in valid_indices],
            [item_unit_prices[i] for i in valid_indices],
        )
        if error:
            flash(error, 'error')
            return render_template('sales/create.html', customers=customers, products=products)

        # Create sale
        sale = Sale.create(db, customer_id, sale_number, status, sale_date,
                          payment_method, 0.0, notes)

        # Process sale items
        total_amount = 0.0
        for i in valid_indices:
            product_id = item_product_ids[i]
            quantity = int(item_quantities[i])
            unit_price = float(item_unit_prices[i])

            SaleItem.create(db, sale['id'], product_id, quantity, unit_price)
            total_amount += quantity * unit_price

        # Update total amount
        Sale.update_total_amount(db, sale['id'], total_amount)

        # Deduct stock only when the sale is completed - deduct the aggregated
        # per-product total once, rather than once per line item.
        if status == 'completed':
            for product_id, total_requested in requested_by_product.items():
                Stock.adjust_quantity(db, product_id, -total_requested)

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
        customer_id = request.form.get('customer_id')
        if not customer_id:
            customer_id = None
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

    # Enrich each line item with its product name
    enriched_items = []
    for item in items:
        product = Product.get_by_id(db, item['product_id'])
        item = dict(item)
        item['product_name'] = product['name'] if product else item['product_id']
        enriched_items.append(item)

    return render_template('sales/view.html', sale=sale, items=enriched_items)

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

        # Validate quantities and check stock availability (aggregated per
        # product across all of this sale's line items) before deducting anything
        requested_by_product, error = _validate_and_aggregate_line_items(
            db,
            [item['product_id'] for item in items],
            [item['quantity'] for item in items],
        )
        if error:
            flash(error, 'error')
            return redirect(url_for('sales.view_sale', sale_id=sale_id))

        for product_id, total_requested in requested_by_product.items():
            Stock.adjust_quantity(db, product_id, -total_requested)

    Sale.update_status(db, sale_id, status)

    flash('Sale status updated successfully', 'success')
    return redirect(url_for('sales.view_sale', sale_id=sale_id))
