import sys
from pathlib import Path

# Add root project directory to Python module search path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Explicit top-level WSGI application exports for Vercel
application = app
