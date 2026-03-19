import os, sys
sys.path.insert(0, os.path.dirname(__file__))

DB_PATH = os.path.join(os.path.dirname(__file__), "portal.db")
if not os.path.exists(DB_PATH):
    print("Setting up database...")
    import setup_db
    setup_db.setup()

print("=" * 50)
print("  COMSTEST UNIVERSITY — Student Portal v4")
print("  Open: http://127.0.0.1:5000")
print("  Teacher: Hxrry / Haris@123")
print("  Student: ahsan_101 / Ahsan@101")
print("=" * 50)

from app import app
app.run(debug=False, port=5000, host="127.0.0.1")
