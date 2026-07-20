# CSV Export Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement CSV export functionality across all main data views and reports.

**Architecture:** A centralized utility function converts data rows to CSV. Blueprint routes pass specific queried data to this utility, and UI templates include "Export CSV" buttons.

**Tech Stack:** Python built-in `csv`, Flask `Response`, Jinja2.

## Global Constraints

- Must work without external libraries for CSV generation (use Python's `csv` module).
- CSV headers should be user-friendly, not just database columns.
- CSV values should accurately represent what the user sees (e.g., category name instead of category ID).

---

### Task 1: CSV Generation Utility

**Files:**
- Create: `app/utils/csv_export.py`
- Create: `app/utils/__init__.py`
- Test: `tests/test_csv_export.py`

**Interfaces:**
- Produces: `generate_csv_response(filename: str, headers: list, rows: list) -> Response`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from flask import Flask
from app.utils.csv_export import generate_csv_response

def test_generate_csv_response():
    app = Flask(__name__)
    with app.app_context():
        headers = ['ID', 'Name', 'Price']
        rows = [
            {'ID': 1, 'Name': 'Seed A', 'Price': 10.50},
            {'ID': 2, 'Name': 'Seed B', 'Price': 20.00}
        ]
        response = generate_csv_response('test_export', headers, rows)
        
        assert response.mimetype == 'text/csv'
        assert 'attachment; filename=test_export.csv' in response.headers['Content-Disposition']
        
        data = response.get_data(as_text=True)
        assert 'ID,Name,Price' in data
        assert '1,Seed A,10.5' in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_csv_export.py -v`
Expected: FAIL with "No module named 'app.utils.csv_export'"

- [ ] **Step 3: Write minimal implementation**

Create `app/utils/__init__.py` (empty file).
Create `app/utils/csv_export.py`:

```python
import csv
import io
from flask import Response

def generate_csv_response(filename, headers, rows):
    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=headers)
    cw.writeheader()
    cw.writerows(rows)
    
    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_csv_export.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/utils/__init__.py app/utils/csv_export.py tests/test_csv_export.py
git commit -m "feat: add csv export utility function"
```

---

### Task 2: Implement Export for Categories and Products

**Files:**
- Modify: `app/blueprints/categories/__init__.py`
- Modify: `app/blueprints/categories/templates/categories/list.html`
- Modify: `tests/test_categories_routes.py`
- Modify: `app/blueprints/products/__init__.py`
- Modify: `app/blueprints/products/templates/products/list.html`
- Modify: `tests/test_products_routes.py`

**Interfaces:**
- Consumes: `generate_csv_response` from Task 1

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_categories_routes.py`:
```python
def test_export_categories_csv(client, auth):
    auth.login()
    response = client.get('/categories/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=categories.csv' in response.headers['Content-Disposition']
```

Append to `tests/test_products_routes.py`:
```python
def test_export_products_csv(client, auth):
    auth.login()
    response = client.get('/products/export')
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment; filename=products.csv' in response.headers['Content-Disposition']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_categories_routes.py::test_export_categories_csv -v`
Run: `pytest tests/test_products_routes.py::test_export_products_csv -v`
Expected: FAIL with 404 Not Found

- [ ] **Step 3: Write minimal implementation (Routes)**

In `app/blueprints/categories/__init__.py`, import `generate_csv_response` and add route:
```python
from app.utils.csv_export import generate_csv_response

@bp.route('/export')
@login_required
def export_csv():
    categories = get_db().execute(
        'SELECT * FROM categories ORDER BY name ASC'
    ).fetchall()
    
    headers = ['ID', 'Name', 'Description']
    rows = []
    for c in categories:
        rows.append({
            'ID': c['id'],
            'Name': c['name'],
            'Description': c['description']
        })
        
    return generate_csv_response('categories', headers, rows)
```

In `app/blueprints/products/__init__.py`, add route:
```python
from app.utils.csv_export import generate_csv_response

@bp.route('/export')
@login_required
def export_csv():
    db = get_db()
    products = db.execute('''
        SELECT p.id, p.name, p.description, p.price, p.stock_quantity, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.name ASC
    ''').fetchall()
    
    headers = ['ID', 'Name', 'Description', 'Price', 'Stock Quantity', 'Category']
    rows = []
    for p in products:
        rows.append({
            'ID': p['id'],
            'Name': p['name'],
            'Description': p['description'],
            'Price': f"₱{p['price']:.2f}" if p['price'] else "",
            'Stock Quantity': p['stock_quantity'],
            'Category': p['category_name'] or 'Unknown'
        })
        
    return generate_csv_response('products', headers, rows)
```

- [ ] **Step 4: Write UI integration (Buttons)**

In `app/blueprints/categories/templates/categories/list.html`:
Find `<a href="{{ url_for('categories.create_category') }}"...>`
Add next to it:
`<a href="{{ url_for('categories.export_csv') }}" class="btn btn-secondary btn-sm ml-2">Export CSV</a>`

In `app/blueprints/products/templates/products/list.html`:
Find `<a href="{{ url_for('products.create_product') }}"...>`
Add next to it:
`<a href="{{ url_for('products.export_csv') }}" class="btn btn-secondary btn-sm ml-2">Export CSV</a>`

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_categories_routes.py::test_export_categories_csv -v`
Run: `pytest tests/test_products_routes.py::test_export_products_csv -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/blueprints/categories/__init__.py app/blueprints/categories/templates/categories/list.html tests/test_categories_routes.py
git add app/blueprints/products/__init__.py app/blueprints/products/templates/products/list.html tests/test_products_routes.py
git commit -m "feat: add export to categories and products"
```

---

*(Note for agentic worker: The pattern established in Task 2 applies to all remaining tables (Customers, Suppliers, Purchases, Sales, Stock, Reports). Because writing out every table here would be extremely repetitive, please implement similar `/export` endpoints, test cases, and UI buttons for the remaining blueprints in subsequent steps by following the exact same TDD pattern. Below is a summarized task structure for the rest of the application.)*

---

### Task 3: Implement Export for Customers and Suppliers

**Files:**
- Modify: `app/blueprints/customers/__init__.py` and `customers/list.html`
- Modify: `tests/test_customers_routes.py`
- Modify: `app/blueprints/suppliers/__init__.py` and `suppliers/list.html`
- Modify: `tests/test_suppliers_routes.py`

**Interfaces:**
- Consumes: `generate_csv_response`

- [ ] **Step 1: Write failing tests for /customers/export and /suppliers/export**
- [ ] **Step 2: Run tests (FAIL)**
- [ ] **Step 3: Add routes converting DB row objects to CSV dictionaries with relevant headers (Name, Email, Phone, Address, etc.)**
- [ ] **Step 4: Add "Export CSV" buttons to their list templates next to the Create buttons**
- [ ] **Step 5: Run tests (PASS)**
- [ ] **Step 6: Commit**

---

### Task 4: Implement Export for Purchases and Sales

**Files:**
- Modify: `app/blueprints/purchases/__init__.py` and `purchases/list.html`
- Modify: `tests/test_purchase_routes.py`
- Modify: `app/blueprints/sales/__init__.py` and `sales/list.html`
- Modify: `tests/test_sales_routes.py`

**Interfaces:**
- Consumes: `generate_csv_response`

- [ ] **Step 1: Write failing tests for /purchases/export and /sales/export**
- [ ] **Step 2: Run tests (FAIL)**
- [ ] **Step 3: Add routes mapping the list data (including resolved customer/supplier names and total amounts) to CSV**
- [ ] **Step 4: Add "Export CSV" buttons to list templates**
- [ ] **Step 5: Run tests (PASS)**
- [ ] **Step 6: Commit**

---

### Task 5: Implement Export for Stock and Reports

**Files:**
- Modify: `app/blueprints/stock/__init__.py` and `stock/list.html`
- Modify: `tests/test_stock_routes.py`
- Modify: `app/blueprints/reports/__init__.py` and `reports/sales.html`, `reports/purchases.html`, `reports/stock.html`
- Modify: `tests/test_reports_routes.py`

**Interfaces:**
- Consumes: `generate_csv_response`

- [ ] **Step 1: Write failing tests for /stock/export and the report export routes (e.g. /reports/sales/export, /reports/purchases/export, /reports/stock/export)**
- [ ] **Step 2: Run tests (FAIL)**
- [ ] **Step 3: Add routes mapping the data to CSV**
- [ ] **Step 4: Add "Export CSV" buttons to templates**
- [ ] **Step 5: Run tests (PASS)**
- [ ] **Step 6: Commit**
