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
