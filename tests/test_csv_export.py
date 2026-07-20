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
