"""
Vercel serverless entry point for PropMatch FastAPI backend.
This file adapts the FastAPI application for Vercel's serverless environment.
"""

import os
import sys
from pathlib import Path

# Add the Backend directory to Python path so we can import from app
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

# Import the FastAPI app
from app.main import app

# Export the app for Vercel
# Vercel will look for a variable named 'app' or a function that returns the app
handler = app

# For debugging in Vercel logs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)