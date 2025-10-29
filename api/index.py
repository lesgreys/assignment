"""
Vercel serverless function wrapper for DoorLoop CX Dashboard
"""
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from src.app import app

# Get the underlying Flask server
server = app.server

# Vercel expects a handler function
def handler(request, response):
    """Handle requests in Vercel serverless environment"""
    return server(request, response)

# For Vercel's Python runtime
application = server
