from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import get_db
from app.models.supplier import Supplier
from app.auth import admin_required
from app.utils.csv_export import generate_csv_response

bp = Blueprint('suppliers', __name__, url_prefix='/suppliers', template_folder='templates')

@bp.route('/')
@admin_required
def list_suppliers():
    db = get_db()
    suppliers = Supplier.get_all(db)
    return render_template('suppliers/list.html', suppliers=suppliers)

@bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_supplier():
    if request.method == 'POST':
        name = request.form['name']
        contact_person = request.form['contact_person']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        notes = request.form.get('notes', '')
        
        db = get_db()
        Supplier.create(db, name, contact_person, phone, email, address, notes)
        flash('Supplier created successfully', 'success')
        return redirect(url_for('suppliers.list_suppliers'))
    
    return render_template('suppliers/create.html')

@bp.route('/<supplier_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_supplier(supplier_id):
    db = get_db()
    supplier = Supplier.get_by_id(db, supplier_id)
    
    if not supplier:
        flash('Supplier not found', 'error')
        return redirect(url_for('suppliers.list_suppliers'))
    
    if request.method == 'POST':
        name = request.form['name']
        contact_person = request.form['contact_person']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        notes = request.form.get('notes', '')
        
        Supplier.update(db, supplier_id, name, contact_person, phone, email, address, notes)
        flash('Supplier updated successfully', 'success')
        return redirect(url_for('suppliers.list_suppliers'))
    
    return render_template('suppliers/edit.html', supplier=supplier)

@bp.route('/<supplier_id>/delete', methods=['POST'])
@admin_required
def delete_supplier(supplier_id):
    db = get_db()
    supplier = Supplier.get_by_id(db, supplier_id)
    
    if not supplier:
        flash('Supplier not found', 'error')
    else:
        Supplier.soft_delete(db, supplier_id)
        flash('Supplier deleted successfully', 'success')
    
    return redirect(url_for('suppliers.list_suppliers'))


@bp.route('/export')
@admin_required
def export_csv():
    db = get_db()
    suppliers = db.execute(
        'SELECT * FROM suppliers WHERE is_active = TRUE ORDER BY name ASC'
    ).fetchall()
    
    headers = ['ID', 'Name', 'Contact Person', 'Phone', 'Email', 'Address', 'Notes']
    rows = []
    for s in suppliers:
        rows.append({
            'ID': s['id'],
            'Name': s['name'],
            'Contact Person': s['contact_person'],
            'Phone': s['phone'],
            'Email': s['email'],
            'Address': s['address'],
            'Notes': s['notes'] or ''
        })
    
    return generate_csv_response('suppliers', headers, rows)