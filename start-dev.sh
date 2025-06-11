#!/bin/bash

# PropMatch Development Server Startup Script
# This script starts both backend and frontend servers for local development

echo "🚀 Starting PropMatch Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i:$port >/dev/null 2>&1; then
        echo -e "${YELLOW}Warning: Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Check if required ports are available
echo "🔍 Checking port availability..."
check_port 8000
backend_port_free=$?
check_port 3000
frontend_port_free=$?

if [ $backend_port_free -ne 0 ] || [ $frontend_port_free -ne 0 ]; then
    echo -e "${RED}Please free up the required ports and try again${NC}"
    exit 1
fi

# Start backend server
echo -e "${BLUE}🔧 Starting Backend API Server (Python FastAPI)...${NC}"
cd Backend
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt >/dev/null 2>&1

# Start backend in background
echo -e "${GREEN}✅ Backend server starting on http://localhost:8000${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend server
echo -e "${BLUE}🎨 Starting Frontend Server (Next.js)...${NC}"
cd ../Frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install >/dev/null 2>&1
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}Creating .env.local configuration...${NC}"
    cat > .env.local << EOL
# PropMatch Frontend Environment Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING=true
NEXT_PUBLIC_CACHE_EXPLANATIONS=true
NEXT_PUBLIC_DEBUG_MODE=false
EOL
fi

echo -e "${GREEN}✅ Frontend server starting on http://localhost:3000${NC}"
npm run dev &
FRONTEND_PID=$!

# Wait for both servers to be ready
echo -e "${BLUE}⏳ Waiting for servers to be ready...${NC}"
sleep 5

# Test backend health
if curl -s http://localhost:8000/api/v1/explanations/health/ >/dev/null; then
    echo -e "${GREEN}✅ Backend API is healthy${NC}"
else
    echo -e "${RED}❌ Backend API is not responding${NC}"
fi

# Test frontend
if curl -s http://localhost:3000 >/dev/null; then
    echo -e "${GREEN}✅ Frontend is ready${NC}"
else
    echo -e "${RED}❌ Frontend is not responding${NC}"
fi

echo ""
echo -e "${GREEN}🎉 PropMatch Development Environment Ready!${NC}"
echo ""
echo -e "${BLUE}📱 Frontend:${NC} http://localhost:3000"
echo -e "${BLUE}🔧 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}🏥 Health Check:${NC} http://localhost:8000/api/v1/explanations/health/"
echo ""
echo -e "${YELLOW}💡 Try searching for: 'Modern 2-bedroom apartment in Sea Point with ocean views'${NC}"
echo ""
echo -e "${RED}Press Ctrl+C to stop both servers${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ Servers stopped${NC}"
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup INT

# Wait for user to stop
wait 