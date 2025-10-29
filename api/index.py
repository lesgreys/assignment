"""
Vercel serverless function wrapper for DoorLoop CX Dashboard
"""
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

# Import the Flask server from the Dash app
from app import server as app
