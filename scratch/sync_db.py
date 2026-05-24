import sys
import os

# Add the backend directory to sys.path so 'app' and 'main' can be found
backend_path = os.path.join(os.getcwd(), 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    from main import app, db
    with app.app_context():
        db.create_all()
        print("Database schema updated successfully.")
except Exception as e:
    print(f"Error: {e}")
