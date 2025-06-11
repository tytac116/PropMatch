# PropMatch Backend Archive

This directory contains archived files from the PropMatch backend development process. These files are kept for historical reference and debugging purposes but are not part of the active codebase.

## Directory Structure

### `/postman_collections/`
Contains all previous versions of Postman API collections:
- Various iterations of the API collection (v2.0 through v2.4)
- Specialized collections for BM25 hybrid search, AI search, and property retrieval
- **Current active collection**: `../PropMatch_AI_Explanation_Collection_v1.0.json`

### `/test_files/`
Development and testing scripts:
- `test_enhanced_search.py` - Enhanced search functionality tests
- `test_property_lookup.py` - Property lookup tests
- `test_api_endpoints.py` - Comprehensive API endpoint tests
- `test_supabase_load.py` - Supabase database loading tests
- `check_progress.py` - Development progress monitoring

### `/development_scripts/`
Helper scripts used during development:
- `install_dependencies.py` - Dependency installation helper
- `start_server.py` - Development server startup script

### `/scripts/`
Database and vector-related scripts:
- `load_vectors.py` - Vector database loading
- `test_supabase_client.py` - Supabase client testing
- `inspect_table_schema.py` - Database schema inspection
- `test_db_connection.py` - Database connection testing
- `startup.py` - Application startup script

### `/data/`
Large data files:
- `property24_for_supabase_fixed.csv` - Processed property data for Supabase
- `property24_production_20250605_165810.json` - Raw property data JSON

### `/models/` and `/config/`
Legacy model and configuration files that were replaced by the current `app/` structure.

## Usage

These files are kept for:
1. **Historical reference** - Understanding the evolution of the system
2. **Debugging** - Troubleshooting issues by comparing with previous implementations
3. **Recovery** - Restoring functionality if needed
4. **Testing** - Running comprehensive tests against the system

## Notes

- The active codebase is in the parent `app/` directory
- Current API collection is `../PropMatch_AI_Explanation_Collection_v1.0.json`
- These archived files should not be imported or used in the active application
- When updating dependencies, check if any archived test files need to be updated for compatibility 