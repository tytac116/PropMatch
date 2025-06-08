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

# Scraping Configuration
MAX_CREDITS_PER_KEY=490
TOTAL_AVAILABLE_CREDITS=2940
MAX_SCRAPES_PER_MINUTE=10
```

### 3. Database Setup (Supabase)
```bash
# Setup database tables and migrate data
python -m database.database
```

### 4. Run Scraper (if needed)
```bash
# Smart resume scraper (automatically detects where to continue)
python -m scrapers.smart_resume_scraper
```

## 📚 Key Components

### Scrapers
- **SmartResumeScraper**: Intelligent scraper that can resume from any interruption point
- **EnhancedProperty24Scraper**: Core scraping engine with dynamic feature extraction

### Database
- **PostgreSQL Schema**: Optimized for property data with JSON fields for complex data
- **Migration Tools**: Automatic JSON to PostgreSQL data migration
- **Connection Management**: Robust Supabase integration

### Models
- **PropertyData**: Comprehensive property data structure
- **POI**: Points of Interest around properties

## 🔧 Features

### Scraping Features
- ✅ **Smart Resume**: Continue from any interruption point
- ✅ **API Key Rotation**: Automatic switching between 6 API keys
- ✅ **Rate Limiting**: Respectful scraping with delays
- ✅ **Error Handling**: Comprehensive retry logic
- ✅ **Real-time Progress**: Live tracking and logging
- ✅ **Incremental Saving**: No data loss on crashes

### Data Features
- ✅ **Rich Property Data**: 25+ fields per property
- ✅ **Points of Interest**: Nearby amenities and facilities
- ✅ **Dynamic Room Detection**: Flexible room type extraction
- ✅ **External Features**: Parking, pools, gardens, etc.
- ✅ **Financial Data**: Prices, levies, rates & taxes
- ✅ **Location Data**: Suburb, city, province mapping

### Database Features
- ✅ **PostgreSQL Integration**: Scalable relational database
- ✅ **JSON Field Support**: Complex data structures
- ✅ **Auto Migration**: JSON to database conversion
- ✅ **Data Validation**: Type checking and constraints
- ✅ **Performance Optimized**: Indexed searches

## 📈 Data Statistics

- **Total Properties**: 1,657
- **Property Types**: Houses, Apartments, Townhouses
- **Coverage Area**: Cape Town, Western Cape
- **Average Price**: R 4.2M
- **Date Range**: Current listings (as of June 2025)

## 🔐 Security

- Environment variables for sensitive data
- Database credentials encrypted
- API keys rotated automatically
- No hardcoded secrets in code

## 🛠️ Development

### Adding New Scrapers
1. Create new scraper in `scrapers/` directory
2. Inherit from `EnhancedProperty24Scraper` 
3. Add to `scrapers/__init__.py`

### Database Schema Changes
1. Update `database/database.py` models
2. Run migration script
3. Test with sample data

## 📄 License

This project is for educational and research purposes.

## 🤝 Contributing

When adding new features:
1. Follow the existing folder structure
2. Add comprehensive logging
3. Include error handling
4. Update documentation
5. Test thoroughly

---

**Next Steps**: Set up Supabase integration and load data into PostgreSQL database. 