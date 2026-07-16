from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.customer import Customer
from app.auth import admin_required

bp = Blueprint('customers', __name__, url_prefix='/customers', template_folder='templates')

@bp.route('/')
@admin_required
def list_customers():
    db = get_db()
    customers = Customer.get_all(db)
    return render_template('customers/list.html', customers=customers)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_customer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        db = get_db()
        Customer.create(db, name, email, phone, address)
        flash('Customer created successfully', 'success')
        return redirect(url_for('customers.list_customers'))
    
    return render_template('customers/create.html')

@bp.route('/<customer_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_customer(customer_id):
    db = get_db()
    customer = Customer.get_by_id(db, customer_id)
    
    if not customer:
        flash('Customer not found', 'error')
        return redirect(url_for('customers.list_customers'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        
        Customer.update(db, customer_id, name, email, phone, address)
        flash('Customer updated successfully', 'success')
        return redirect(url_for('customers.list_customers'))
    
    return render_template('customers/edit.html', customer=customer)

@bp.route('/<customer_id>/delete', methods=['POST'])
@admin_required
def delete_customer(customer_id):
    db = get_db()
    customer = Customer.get_by_id(db, customer_id)
    
    if not customer:
        flash('Customer not found', 'error')
    else:
        Customer.soft_delete(db, customer_id)
        flash('Customer deleted successfully', 'success')
    
    return redirect(url_for('customers.list_customers'))