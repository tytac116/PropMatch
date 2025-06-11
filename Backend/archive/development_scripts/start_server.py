#!/usr/bin/env python3
"""
PropMatch API Server Startup Script

This script sets up the environment and starts the FastAPI server.
It handles environment variables and provides helpful feedback.

Usage:
    python start_server.py [--port 8000] [--host 0.0.0.0]
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

def setup_environment():
    """Setup environment variables"""
    # Load .env file first
    load_dotenv()
    
    # Only set defaults for missing values - don't override .env file
    os.environ.setdefault("DATABASE_URL", 
        "postgresql://postgres:GCEXYZ@001@db.zrawaliecoufegkanlpg.supabase.co:5432/postgres")
    os.environ.setdefault("SUPABASE_URL", 
        "https://zrawaliecoufegkanlpg.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", 
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpyYXdhbGllY291ZmVna2FubHBnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ1MjE3MzQsImV4cCI6MjA1MDA5NzczNH0.8Hnh6-mALLN5YOhZeGqXRBCQLKDgOPHCuBJE1gJLLwU")
    
    # Security and app settings
    os.environ.setdefault("SECRET_KEY", "dev-secret-key-change-in-production")
    os.environ.setdefault("ENVIRONMENT", "development")
    
    # Check if keys are available and show status
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    pinecone_key = os.environ.get("PINECONE_API_KEY", "")
    
    if openai_key:
        print("✅ OpenAI API key loaded successfully")
    else:
        print("⚠️  OpenAI API key not set - AI features may be limited")
        
    if pinecone_key:
        print("✅ Pinecone API key loaded successfully") 
    else:
        print("⚠️  Pinecone API key not set - Vector search may be limited")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Start PropMatch API Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    
    args = parser.parse_args()
    
    print("🚀 Starting PropMatch API Server")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ Error: Please run this script from the Backend directory")
        print("   cd Backend && python start_server.py")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Start server
    print(f"🌟 Server starting at http://{args.host}:{args.port}")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 ReDoc Documentation: http://localhost:8000/redoc")
    print("\n📊 Available Endpoints:")
    print("  • GET  /                          - Health check")
    print("  • GET  /api/v1/properties/        - List properties")
    print("  • GET  /api/v1/properties/{id}    - Get property by ID")
    print("  • POST /api/v1/search/            - AI-powered search")
    print("  • POST /api/v1/search/simple      - Simple search")
    print("  • GET  /api/v1/search/health      - Search service health")
    print("\n🔧 Use Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 