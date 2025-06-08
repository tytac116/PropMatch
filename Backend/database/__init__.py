"""
PropMatch Database Package
==========================

This package handles all database operations including:
- Supabase PostgreSQL connections
- Data models and schemas  
- Migration utilities
- CRUD operations
"""

from .database import DatabaseManager, Property, Base

__all__ = ['DatabaseManager', 'Property', 'Base'] 