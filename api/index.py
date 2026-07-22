import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import app

# Export the Flask app as the handler for Vercel
__all__ = ['app']

if __name__ == "__main__":
    app.run()

