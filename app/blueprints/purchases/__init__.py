from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.purchase_order import PurchaseOrder
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.stock import Stock
from app.auth import admin_required
from app.utils.csv_export import generate_csv_response

bp = Blueprint('purchases', __name__, url_prefix='/purchases', template_folder='templates')

@bp.route('/')
@admin_required
def list_purchase_orders():
    db = get_db()
    orders = PurchaseOrder.get_all(db)
    enriched = []
    for order in orders:
        supplier = Supplier.get_by_id(db, order['supplier_id'])
        order = dict(order)
        order['supplier_name'] = supplier['name'] if supplier else order['supplier_id']
        enriched.append(order)
    return render_template('purchases/list.html', orders=enriched)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_purchase_order():
    db = get_db()
    suppliers = Supplier.get_all(db)
    products = Product.get_all(db)
    
    if request.method == 'POST':
        supplier_id = request.form['supplier_id']
        order_number = request.form['order_number']
        status = request.form['status']
        order_date = request.form['order_date']
        received_date = request.form.get('received_date', '')
        notes = request.form.get('notes', '')
        
        # Create purchase order
        order = PurchaseOrder.create(db, supplier_id, order_number, status, order_date, 
                                    received_date, 0.0, notes)
        
        # Process order items
        item_product_ids = request.form.getlist('item_product_id[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_unit_costs = request.form.getlist('item_unit_cost[]')
        
        total_amount = 0.0
        for i in range(len(item_product_ids)):
            if item_product_ids[i] and item_quantities[i] and item_unit_costs[i]:
                product_id = item_product_ids[i]
                quantity = int(item_quantities[i])
                unit_cost = float(item_unit_costs[i])
                
                PurchaseOrderItem.create(db, order['id'], product_id, quantity, unit_cost)
                total_amount += quantity * unit_cost
        
        # Update total amount
        PurchaseOrder.update_total_amount(db, order['id'], total_amount)
        
        # Add to stock if created as completed
        if status == 'completed':
            for i in range(len(item_product_ids)):
                if item_product_ids[i] and item_quantities[i] and item_unit_costs[i]:
                    Stock.adjust_quantity(db, item_product_ids[i], int(item_quantities[i]))
        
        flash('Purchase order created successfully', 'success')
        return redirect(url_for('purchases.list_purchase_orders'))
    
    return render_template('purchases/create.html', suppliers=suppliers, products=products)

@bp.route('/<order_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_purchase_order(order_id):
    db = get_db()
    order = PurchaseOrder.get_by_id(db, order_id)
    suppliers = Supplier.get_all(db)
    products = Product.get_all(db)
    items = PurchaseOrderItem.get_by_order_id(db, order_id)
    
    if not order:
        flash('Purchase order not found', 'error')
        return redirect(url_for('purchases.list_purchase_orders'))
    
    if request.method == 'POST':
        supplier_id = request.form['supplier_id']
        order_number = request.form['order_number']
        status = request.form['status']
        order_date = request.form['order_date']
        received_date = request.form.get('received_date', '')
        notes = request.form.get('notes', '')
        
        # Update purchase order
        PurchaseOrder.update(db, order_id, supplier_id, order_number, status, order_date, 
                            received_date, order['total_amount'], notes)
        
        # Process order items - first delete existing items
        PurchaseOrderItem.delete_by_order_id(db, order_id)
        
        # Then add new items
        item_product_ids = request.form.getlist('item_product_id[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_unit_costs = request.form.getlist('item_unit_cost[]')
        
        total_amount = 0.0
        for i in range(len(item_product_ids)):
            if item_product_ids[i] and item_quantities[i] and item_unit_costs[i]:
                product_id = item_product_ids[i]
                quantity = int(item_quantities[i])
                unit_cost = float(item_unit_costs[i])
                
                PurchaseOrderItem.create(db, order_id, product_id, quantity, unit_cost)
                total_amount += quantity * unit_cost
        
        # Update total amount
        PurchaseOrder.update_total_amount(db, order_id, total_amount)
        
        flash('Purchase order updated successfully', 'success')
        return redirect(url_for('purchases.list_purchase_orders'))
    
    return render_template('purchases/edit.html', order=order, suppliers=suppliers, 
                          products=products, items=items)

@bp.route('/<order_id>/view')
@admin_required
def view_purchase_order(order_id):
    db = get_db()
    order = PurchaseOrder.get_by_id(db, order_id)
    items = PurchaseOrderItem.get_by_order_id(db, order_id)
    
    if not order:
        flash('Purchase order not found', 'error')
        return redirect(url_for('purchases.list_purchase_orders'))
    
    # Resolve supplier UUID to a human-readable name
    supplier = Supplier.get_by_id(db, order['supplier_id'])
    order = dict(order)
    order['supplier_name'] = supplier['name'] if supplier else order['supplier_id']

    # Enrich each line item with its product name
    enriched_items = []
    for item in items:
        product = Product.get_by_id(db, item['product_id'])
        item = dict(item)
        item['product_name'] = product['name'] if product else item['product_id']
        enriched_items.append(item)

    return render_template('purchases/view.html', order=order, items=enriched_items)

@bp.route('/<order_id>/update-status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    db = get_db()
    order = PurchaseOrder.get_by_id(db, order_id)
    
    if not order:
        flash('Purchase order not found', 'error')
        return redirect(url_for('purchases.list_purchase_orders'))
    
    status = request.form['status']
    previous_status = order['status']
    
    if status == 'completed' and previous_status != 'completed':
        items = PurchaseOrderItem.get_by_order_id(db, order_id)
        for item in items:
            Stock.adjust_quantity(db, item['product_id'], item['quantity'])
            
    PurchaseOrder.update_status(db, order_id, status)
    
    flash('Purchase order status updated successfully', 'success')
    return redirect(url_for('purchases.view_purchase_order', order_id=order_id))

@bp.route('/export')
@admin_required
def export_csv():
    db = get_db()
    orders = PurchaseOrder.get_all(db)
    
    # Enrich with supplier names
    enriched = []
    for order in orders:
        supplier = Supplier.get_by_id(db, order['supplier_id'])
        order = dict(order)
        order['supplier_name'] = supplier['name'] if supplier else order['supplier_id']
        enriched.append(order)
    
    headers = ['ID', 'Order Number', 'Supplier', 'Status', 'Order Date', 'Received Date', 'Total Amount', 'Notes']
    rows = []
    for order in enriched:
        rows.append({
            'ID': order['id'],
            'Order Number': order['order_number'],
            'Supplier': order['supplier_name'],
            'Status': order['status'],
            'Order Date': order['order_date'],
            'Received Date': order['received_date'] or '',
            'Total Amount': f"₱{order['total_amount']:.2f}" if order['total_amount'] else "₱0.00",
            'Notes': order['notes'] or ''
        })
    
    return generate_csv_response('purchase_orders', headers, rows)
