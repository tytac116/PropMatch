# PropMatch Backend Setup Guide

## 🚀 Quick Start

### Step 1: Environment Setup

1. **Copy the environment template:**
   ```bash
   cp env.example .env
   ```

2. **Fill in your credentials in `.env`:**
   - `DATABASE_URL`: Your Supabase PostgreSQL connection string
   - `OPENAI_API_KEY`: Your OpenAI API key (get from https://platform.openai.com/api-keys)
   - Other variables will be needed for later phases

### Step 2: Installation Options

#### Option A: Docker (Recommended for Production)

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Access your API:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs

#### Option B: Local Development

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize the database:**
   ```bash
   python scripts/startup.py
   ```

3. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 🧪 Testing Your Setup

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Get Properties
```bash
curl http://localhost:8000/api/v1/properties?limit=5
```

### 3. Simple Search
```bash
curl -X POST http://localhost:8000/api/v1/search/simple \
  -H "Content-Type: application/json" \
  -d '{"query": "apartment in cape town", "limit": 5}'
```

### 4. Property Statistics
```bash
curl http://localhost:8000/api/v1/properties/stats/summary
```

## 📚 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 What's Implemented (Phase 1)

✅ **FastAPI Foundation**
- Professional project structure
- Pydantic models matching frontend interface
- Database connection to Supabase PostgreSQL
- Automatic CSV data migration

✅ **Core Endpoints**
- `GET /api/v1/properties` - List properties with filtering
- `GET /api/v1/properties/{id}` - Get specific property
- `POST /api/v1/search` - Search properties (basic text search)
- `GET /api/v1/properties/stats/summary` - Property statistics

✅ **Docker Support**
- Dockerfile for containerization
- Docker Compose for local development
- Health checks and proper logging

## 🎯 Next Steps (Coming in Phase 2)

🔄 **Vector Search (Phase 2)**
- Pinecone integration for semantic search
- OpenAI embeddings for property descriptions
- AI-powered match scoring

🤖 **AI Explanations (Phase 3)**
- LLM-generated explanations
- Redis caching for performance
- Streaming responses

## 🐛 Troubleshooting

### Database Connection Issues
- Verify your `DATABASE_URL` in `.env`
- Check Supabase project is running
- Ensure IP is whitelisted in Supabase

### Port Already in Use
```bash
# Kill process on port 8000
sudo lsof -t -i tcp:8000 | xargs kill -9
```

### Missing Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## 📦 Project Structure

```
Backend/
├── app/
│   ├── api/routes/          # API endpoints
│   ├── core/               # Configuration
│   ├── db/                 # Database models
│   ├── models/             # Pydantic schemas
│   └── services/           # Business logic
├── scripts/                # Utility scripts
├── data/                   # CSV data files
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Local development
└── requirements.txt       # Python dependencies
``` 