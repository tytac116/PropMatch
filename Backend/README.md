# PropMatch Backend

A robust property data scraping and management system for South African real estate, specifically focused on Cape Town properties from Property24.

## 📊 Project Overview

- **Total Properties Scraped**: 1,657 Cape Town properties
- **Success Rate**: 80.2%
- **Data Source**: Property24.com
- **Database**: Supabase PostgreSQL
- **Scraping Engine**: FireCrawl API with intelligent resume capabilities

## 🗂️ Project Structure

```
Backend/
├── scrapers/                    # Web scraping modules
│   ├── smart_resume_scraper.py  # Intelligent auto-resume scraper
│   ├── enhanced_property24_scraper.py  # Core Property24 scraping logic
│   └── __init__.py
├── database/                    # Database operations
│   ├── database.py             # Supabase PostgreSQL integration
│   └── __init__.py
├── models/                      # Data models
│   ├── models.py               # PropertyData and POI models
│   └── __init__.py
├── config/                      # Configuration files
│   ├── .env                    # Environment variables (gitignored)
│   └── __init__.py
├── data/                        # Scraped data
│   └── property24_production_20250605_165810.json  # Main dataset (1,657 properties)
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
Create `config/.env` file with your API keys:
```env
# FireCrawl API Keys (for scraping)
FIRECRAWL_API_KEY_1=fc-your-key-1
FIRECRAWL_API_KEY_2=fc-your-key-2
# ... up to 6 keys

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-database-password
SUPABASE_ANON_KEY=your-anon-key

# LangSmith Tracing (Optional - for AI observability)
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=PropMatch-Backend

# Scraping Configuration
MAX_CREDITS_PER_KEY=490
TOTAL_AVAILABLE_CREDITS=2940
MAX_SCRAPES_PER_MINUTE=10
```

## 🔍 AI Observability

LangSmith integration provides complete visibility into AI operations:
- **Trace all AI calls** in real-time
- **Monitor token usage** and costs
- **Debug AI responses** and prompts
- **Track performance** metrics

See [LANGSMITH_SETUP.md](LANGSMITH_SETUP.md) for setup instructions.

### Database Features
- ✅ **PostgreSQL Integration**: Scalable relational database
- ✅ **JSON Field Support**: Complex data structures
- ✅ **Auto Migration**: JSON to database conversion
- ✅ **Data Validation**: Type checking and constraints
- ✅ **Performance Optimized**: Indexed searches

### AI Features
- ✅ **AI-Powered Search**: GPT-4o-mini for intelligent property ranking
- ✅ **Semantic Understanding**: Vector embeddings for property matching
- ✅ **Real-time Explanations**: AI-generated property match explanations
- ✅ **LangSmith Tracing**: Complete AI observability and debugging
- ✅ **Token Tracking**: Monitor AI usage and costs
- ✅ **Hybrid Search**: Vector + BM25 + AI scoring