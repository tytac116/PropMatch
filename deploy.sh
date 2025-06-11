#!/bin/bash

# PropMatch Deployment Script
echo "🚀 PropMatch Deployment Script"
echo "================================"

# Check if .env files exist
echo "📋 Checking environment files..."

if [ ! -f "Backend/.env" ]; then
    echo "❌ Backend/.env not found!"
    echo "📝 Please copy Backend/env.example to Backend/.env and fill in your values"
    exit 1
fi

if [ ! -f "Frontend/.env.local" ]; then
    echo "❌ Frontend/.env.local not found!"
    echo "📝 Please copy Frontend/env.example to Frontend/.env.local and fill in your values"
    exit 1
fi

echo "✅ Environment files found"

# Choose deployment method
echo ""
echo "🎯 Choose deployment method:"
echo "1) Docker Compose (Full stack locally)"
echo "2) Backend only (for testing)"
echo "3) Frontend only (for testing)"
echo "4) Build for production deployment"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🐳 Starting full stack with Docker Compose..."
        docker-compose up --build
        ;;
    2)
        echo "🔧 Starting backend only..."
        cd Backend
        pip install -r requirements.txt
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    3)
        echo "🎨 Starting frontend only..."
        cd Frontend
        npm install
        npm run dev
        ;;
    4)
        echo "📦 Building for production..."
        echo "Building backend Docker image..."
        docker build -t propmatch-backend ./Backend
        echo "Building frontend..."
        cd Frontend && npm install && npm run build
        echo "✅ Production build complete!"
        echo "Backend image: propmatch-backend"
        echo "Frontend build: Frontend/.next"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac 