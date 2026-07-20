# CSV Export Feature Design Specification

## 1. Overview
The CSV Export feature allows users to download data from the application's main data tables and reports in `.csv` format. This functionality ensures that users can easily open and manipulate their inventory data in Excel or other spreadsheet applications.

## 2. Architecture and Data Flow
The feature will use a **Blueprint-Specific Exports** approach:
- Each blueprint (e.g., Products, Sales, Purchases, Stock, Reports, Categories, Customers, Suppliers) will have a new dedicated endpoint, e.g., `/products/export`.
- These endpoints will query the database, applying the exact same joins and formatting as their corresponding list/report views. This ensures the exported CSV matches what the user sees on their screen (e.g., resolving a Category ID to a Category Name).
- A centralized utility function will be responsible for converting a list of dictionaries (or objects) into a CSV response, keeping the code DRY.

## 3. Components
### 3.1. CSV Generation Utility
- **Location:** `app/utils/csv_export.py`
- **Function:** `generate_csv_response(filename, headers, rows)`
- **Behavior:** Uses Python's built-in `csv` and `io.StringIO` modules to build a CSV string. It returns a Flask `Response` object with `mimetype='text/csv'` and the `Content-Disposition` header set to `attachment; filename=<filename>.csv`.

### 3.2. Blueprint Export Endpoints
Each relevant blueprint will receive a new route:
- `@bp.route('/export')`
- The handler will fetch data (potentially reading search or filter parameters if applicable).
- It will format the data into a list of dictionaries matching the `headers` required by `generate_csv_response`.

### 3.3. UI Updates
- In each corresponding list template (e.g., `app/blueprints/products/templates/products/list.html`), an "Export CSV" button will be added.
- The button will be styled consistently with existing UI elements (e.g., secondary or outline buttons) and placed near the "Create" button or filter controls.

## 4. Error Handling
- If data retrieval fails, standard error handling/flash messages will apply, redirecting the user back to the list view.
- Empty data sets will successfully generate a CSV containing only the header row.

## 5. Testing Strategy
- Manual verification of CSV downloads for each blueprint, ensuring Excel compatibility and correct data joins (e.g., names instead of IDs).
- Testing that special characters in data (like commas or quotes) are properly escaped in the generated CSV.
