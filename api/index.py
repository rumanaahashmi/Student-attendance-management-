import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from app import app
except Exception as e:
    print(f"Error importing app: {e}")
    raise

# Ensure Flask app is the WSGI application for Vercel
if __name__ == "__main__":
    app.run(debug=False)

