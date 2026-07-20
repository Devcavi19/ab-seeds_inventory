# AB Seeds Inventory

A comprehensive seed inventory management system for agricultural businesses. Track products, stock levels, suppliers, customers, purchases, and sales with an intuitive web interface that can also run as a desktop application.

## Overview

AB Seeds Inventory is a Flask-based inventory management system specifically designed for seed businesses. It provides a complete solution for managing agricultural inventory with features for tracking products, stock levels, suppliers, customers, purchases, and sales.

The application follows an **offline-first architecture** using SQLite as the primary database, with optional synchronization to Turso for cloud-based data persistence and multi-device access.

## Features

### Core Inventory Management
- **Product Management**: Add, edit, delete, and search products with images, descriptions, pricing, and categorization
- **Category Management**: Organize products into categories for easy filtering and reporting
- **Stock Tracking**: Monitor stock quantities, lot numbers, expiry dates, and storage locations
- **Low Stock Alerts**: Automatic notifications when stock falls below defined thresholds

### Supplier & Customer Management
- **Supplier Directory**: Manage supplier information including contact details, addresses, and notes
- **Customer Database**: Track customer information and purchase history
- **Relationship Management**: Link products to suppliers and sales to customers

### Transaction Management
- **Purchase Orders**: Create and track purchase orders from suppliers with status management
- **Sales Processing**: Record sales transactions with multiple items, payment methods, and status tracking
- **Order History**: Complete history of all purchases and sales with filtering capabilities

### Reporting & Analytics
- **Dashboard**: Real-time overview with summary counts, revenue statistics, and trends
- **Sales Reports**: Daily sales tracking, top-selling products, and revenue analytics
- **Inventory Reports**: Low stock items, stock by category, and product performance
- **Financial Reports**: Total sales amount, total purchases amount, and profit analysis

### User Management
- **Authentication**: Secure login with username/password
- **Role-Based Access**: Admin and regular user roles with different permissions
- **User Management**: Create, edit, and deactivate users (admin only)

### Sync & Offline Capabilities
- **Offline-First**: Works completely offline with local SQLite database
- **Cloud Sync**: Optional synchronization with Turso for cloud backup and multi-device access
- **Background Sync**: Automatic periodic synchronization when configured

### Desktop Application
- **Native Window**: Run as a desktop application using FlaskWebGUI
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Build Support**: Create standalone executables with PyInstaller

## Python Version

- **Python 3.10 or higher** is required

## Dependencies

The project requires the following Python packages:

```
Flask>=3.0              # Web framework
bcrypt>=4.0             # Password hashing
python-dotenv>=1.0      # Environment variable management
pytest>=8.0             # Testing framework
flaskwebgui>=1.0.0      # Desktop application wrapper
waitress>=3.0.0         # Production WSGI server
pyturso>=0.7.0          # Turso database synchronization (optional)
```

## Installation

### Prerequisites

- Python 3.10+
- pip (Python package manager)
- Git (for cloning the repository)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hecavi/ab-seeds_inventory.git
   cd ab-seeds_inventory
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the database directory:**
   ```bash
   mkdir -p data
   ```

5. **Run database migrations:**
   ```bash
   python -c "from app import create_app; app = create_app(); app.app_context().push()"
   ```
   The migrations will run automatically on first startup.

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root:

```bash
# Database configuration
DATABASE_PATH=data/local.db

# Optional Turso synchronization (remove if not using cloud sync)
TURSO_DATABASE_URL=libsql://your-database-url.turso.io
TURSO_AUTH_TOKEN=your-auth-token

# Flask configuration
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
```

## Running the Application

### Development Mode (Web Server)

```bash
python run.py
```

The application will be available at `http://localhost:5000`

### Desktop Mode

```bash
python run_desktop.py
```

This launches the application in a native window using FlaskWebGUI.

## User Guide

### Getting Started

1. **First Run Setup:**
   - On first launch, create an admin user by running:
     ```bash
     python create_admin.py
     ```
   - This creates an admin user with username: `admin` and password: `admin`

2. **Logging In:**
   - Navigate to the login page
   - Enter your username and password
   - Click "Login" to access the dashboard

### Dashboard

The dashboard provides an overview of your inventory:
- **Summary Cards**: Quick view of total products, customers, suppliers, low stock items, and pending orders
- **Sales Chart**: Daily sales revenue for the past 7 days
- **Top Products**: Best-selling products by quantity
- **Low Stock Alerts**: Products that need reordering

### Managing Products

1. **View Products:**
   - Navigate to Products section
   - Browse all active products with search and filter options

2. **Add a Product:**
   - Click "Add Product" button
   - Fill in product details (name, description, price, stock quantity, category)
   - Upload an optional product image
   - Click "Save"

3. **Edit a Product:**
   - Click on a product from the list
   - Make changes to any field
   - Click "Update"

4. **Delete a Product:**
   - Click the delete button on a product
   - Confirm the deletion (products are soft-deleted and can be restored)

### Managing Categories

1. **Create Category:**
   - Go to Categories section
   - Click "Add Category"
   - Enter name and optional description
   - Click "Save"

2. **Note:** Categories with active products cannot be deleted to maintain data integrity.

### Managing Stock

1. **View Stock:**
   - Navigate to Stock section
   - See all stock items with quantities

2. **Update Stock:**
   - Edit product stock quantity directly
   - Or create purchase orders to add stock

### Processing Sales

1. **Create a Sale:**
   - Go to Sales section
   - Click "Add Sale"
   - Select customer (or create new one)
   - Add products with quantities
   - Select payment method
   - Click "Complete Sale"

2. **View Sales History:**
   - Browse all sales with filtering by date, status, or customer
   - View sale details including all items

### Managing Purchases

1. **Create Purchase Order:**
   - Go to Purchases section
   - Click "Add Purchase Order"
   - Select supplier
   - Add products with quantities and costs
   - Set expected delivery date
   - Click "Save"

2. **Receive Purchase Order:**
   - Open the purchase order
   - Mark as received
   - Update received quantities
   - System automatically updates stock levels

### Running Reports

1. **Access Reports:**
   - Navigate to Reports section
   - View pre-built reports:
     - Sales Reports
     - Purchase Reports
     - Inventory Reports
     - Financial Summary

2. **Custom Reports:**
   - Filter by date ranges
   - Export data for external analysis

### User Management (Admin Only)

1. **Create User:**
   - Go to Management > Users
   - Click "Add User"
   - Fill in user details and select role (admin or user)
   - Click "Save"

2. **Edit User:**
   - Select user from list
   - Update information
   - Toggle active status

3. **Delete User:**
   - Click delete button
   - Confirm deletion

## Developer's Guide

### Project Structure

```
ab-seeds_inventory/
├── app/                          # Main application directory
│   ├── __init__.py               # Application factory
│   ├── config.py                 # Configuration settings
│   ├── extensions.py             # Flask extensions (database)
│   ├── auth.py                   # Authentication decorators
│   ├── management.py             # Management routes
│   │
│   ├── blueprints/               # Feature modules (MVC pattern)
│   │   ├── auth/                 # Authentication (login/logout)
│   │   ├── categories/           # Category management
│   │   ├── customers/            # Customer management
│   │   ├── dashboard/            # Dashboard and analytics
│   │   ├── products/             # Product management
│   │   ├── purchases/            # Purchase order management
│   │   ├── reports/              # Reporting functionality
│   │   ├── sales/                # Sales management
│   │   ├── stock/                # Stock management
│   │   ├── suppliers/            # Supplier management
│   │   └── sync/                 # Synchronization status
│   │
│   ├── models/                   # Data models
│   │   ├── category.py
│   │   ├── customer.py
│   │   ├── product.py
│   │   ├── purchase_order.py
│   │   ├── purchase_order_item.py
│   │   ├── sale.py
│   │   ├── sale_item.py
│   │   ├── stock.py
│   │   ├── supplier.py
│   │   └── user.py
│   │
│   ├── services/                 # Business logic services
│   │   ├── report_service.py     # Reporting calculations
│   │   ├── sync_service.py      # Turso synchronization
│   │   └── __init__.py
│   │
│   ├── static/                   # Static files
│   │   ├── css/                  # Stylesheets
│   │   ├── images/               # Images (including app icon)
│   │   └── js/                   # JavaScript files
│   │
│   └── templates/               # HTML templates
│       ├── base.html             # Base template
│       ├── components/           # Reusable components
│       ├── management/           # Management templates
│       └── ...                   # Feature-specific templates
│
├── migrations/                   # Database migration scripts
│   ├── 001_initial_schema.sql
│   ├── 002_update_products_schema.sql
│   ├── 003_add_is_active_to_customers.sql
│   └── 004_seed_stock_from_products.sql
│
├── tests/                        # Test suite
├── data/                         # Data storage (SQLite database, uploads)
│   └── uploads/                  # Product images
│
├── run.py                        # Web server entry point
├── run_desktop.py                # Desktop application entry point
├── build_executable.sh           # Build script for standalone executable
├── create_admin.py               # Admin user creation script
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not tracked)
└── README.md                     # This file
```

### Database Schema

The application uses SQLite with the following main tables:

- **users**: User accounts with authentication and role information
- **categories**: Product categories
- **products**: Product information with pricing and descriptions
- **suppliers**: Supplier information
- **customers**: Customer information
- **stock**: Stock levels and inventory tracking
- **purchase_orders**: Purchase order headers
- **purchase_order_items**: Individual items in purchase orders
- **sales**: Sale transaction headers
- **sale_items**: Individual items in sales
- **schema_migrations**: Track applied database migrations

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   Templates  │    │   Static     │    │  FlaskWebGUI │ │
│  │   (Jinja2)   │    │   Assets     │    │  (Desktop)  │ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                      │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   Flask App  │    │  Blueprints   │    │  Services   │ │
│  │   (Factory)  │    │  (Routes)     │    │  (Business  │ │
│  └──────────────┘    └──────────────┘    │   Logic)    │ │
│                                                  └────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                             │
│  ┌──────────────┐          ┌─────────────────────────────┐ │
│  │   SQLite     │          │       Turso Sync Service     │ │
│  │   Database   │◄────────►│  (Optional Cloud Sync)       │ │
│  │   (Local)    │          │                             │ │
│  └──────────────┘          └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### Application Factory

The app uses Flask's application factory pattern (`app/__init__.py`):
- Creates and configures the Flask application
- Initializes extensions (database)
- Registers blueprints
- Sets up synchronization service
- Runs database migrations

#### Database Layer

- **SQLite**: Primary database using Python's built-in `sqlite3` module
- **Turso Sync**: Optional synchronization using `pyturso` and `turso.sync`
- **Migrations**: SQL-based migration system that runs on startup

#### Authentication

- **Password Hashing**: Uses `bcrypt` for secure password storage
- **Session Management**: Flask sessions for user authentication
- **Decorators**: `@login_required` and `@admin_required` for access control

### Adding New Features

1. **Create a new blueprint:**
   ```bash
   mkdir -p app/blueprints/new_feature
   touch app/blueprints/new_feature/__init__.py
   ```

2. **Define routes in the blueprint:**
   ```python
   from flask import Blueprint, render_template
   
   bp = Blueprint('new_feature', __name__, url_prefix='/new-feature', template_folder='templates')
   
   @bp.route('/')
   def index():
       return render_template('new_feature/index.html')
   ```

3. **Register the blueprint in `app/__init__.py`:**
   ```python
   from app.blueprints.new_feature import bp as new_feature_bp
   app.register_blueprint(new_feature_bp)
   ```

4. **Create templates in `app/blueprints/new_feature/templates/`**

5. **Add tests in `tests/`**

### Database Migrations

1. Create a new migration file in `migrations/` with a sequential number:
   ```bash
   touch migrations/005_add_new_table.sql
   ```

2. Write the SQL migration:
   ```sql
   CREATE TABLE IF NOT EXISTS new_table (
       id TEXT PRIMARY KEY,
       name TEXT,
       created_at TEXT
   );
   ```

3. The migration will run automatically on the next application startup.

### Testing

Run the test suite:

```bash
pytest
```

Or run specific tests:

```bash
pytest tests/test_auth.py
pytest tests/test_products.py
```

### Building for Production

#### Standalone Executable

Use the provided build script to create a standalone executable:

```bash
chmod +x build_executable.sh
./build_executable.sh
```

The executable will be created in `dist/ABSeedsInventory/`

#### Requirements for Building

- PyInstaller: `pip install pyinstaller`
- All project dependencies must be installed

#### Build Options

The build script uses the following PyInstaller options:
- `--name "ABSeedsInventory"`: Application name
- `--windowed`: No console window
- `--icon=app/static/images/icon.png`: Application icon
- `--add-data`: Include templates and static files
- `--hidden-import`: Ensure all dependencies are bundled

### Deployment Options

#### Local Deployment

```bash
# Run in production mode with Waitress
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

Or using Waitress directly:

```bash
waitress-serve --port=5000 run:app
```

#### Desktop Distribution

1. Build the executable using PyInstaller
2. Package for your target platform:
   - **Windows**: Create an installer using Inno Setup
   - **macOS**: Create a DMG file
   - **Linux**: Create .deb or .rpm packages

#### Cloud Deployment

The application can be deployed to any platform that supports Flask:
- Heroku
- Render
- PythonAnywhere
- AWS Elastic Beanstalk
- Google App Engine

Note: For cloud deployment, ensure the `data/` directory is writable.

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_PATH` | Path to SQLite database | No | `data/local.db` |
| `TURSO_DATABASE_URL` | Turso remote URL for sync | No | None |
| `TURSO_AUTH_TOKEN` | Turso authentication token | No | None |
| `SECRET_KEY` | Flask secret key | No | `dev-secret-key` |
| `FLASK_DEBUG` | Enable debug mode | No | `True` (DevConfig) |

### Troubleshooting

#### Common Issues

1. **Database not found:**
   - Ensure the `data/` directory exists
   - Check that the application has write permissions

2. **Turso sync not working:**
   - Verify `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` are correct
   - Ensure `pyturso` is installed
   - Check that the Turso native library is available

3. **Desktop app won't start:**
   - Ensure FlaskWebGUI is installed
   - Try running in web mode first to verify the app works

4. **Migrations not running:**
   - Check that the `migrations/` directory exists
   - Verify migration files have `.sql` extension

5. **Login issues:**
   - Run `python create_admin.py` to create/reset admin user
   - Default credentials: username=`admin`, password=`admin`

#### Debug Mode

Enable debug mode for detailed error information:

```bash
export FLASK_DEBUG=True
python run.py
```

Or set in `.env`:

```
FLASK_DEBUG=True
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

### License

This project is proprietary software. All rights reserved.

### Contact

For questions or support, please contact the project maintainer.

---

Built with Flask, SQLite, and Turso. Offline-first, ready for desktop and web deployment.