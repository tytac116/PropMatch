#!/usr/bin/env python3
"""
Database Connection Diagnostic Script
Tests Supabase PostgreSQL connection step by step
"""

import os
import sys
import socket
import psycopg2
from urllib.parse import urlparse
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_dns_resolution(hostname):
    """Test if hostname resolves to IP"""
    print(f"🔍 Testing DNS resolution for: {hostname}")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ Hostname resolves to: {ip}")
        return True, ip
    except socket.gaierror as e:
        print(f"❌ DNS resolution failed: {e}")
        return False, None

def test_port_connectivity(hostname, port):
    """Test if we can connect to the port"""
    print(f"🔍 Testing port connectivity to: {hostname}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is open and reachable")
            return True
        else:
            print(f"❌ Port {port} is not reachable (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Port connectivity test failed: {e}")
        return False

def test_postgres_connection(connection_string):
    """Test PostgreSQL connection"""
    print(f"🔍 Testing PostgreSQL connection...")
    try:
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL connection successful!")
        print(f"📊 Database version: {version[0]}")
        
        # Test if properties table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'properties';
        """)
        
        table_exists = cursor.fetchone()
        if table_exists:
            print(f"✅ 'properties' table exists")
            
            # Count properties
            cursor.execute("SELECT COUNT(*) FROM properties;")
            count = cursor.fetchone()
            print(f"📈 Found {count[0]} properties in table")
            
            # Show sample property
            cursor.execute("SELECT id, title, city FROM properties LIMIT 1;")
            sample = cursor.fetchone()
            if sample:
                print(f"📝 Sample property: {sample[0]} - {sample[1]} in {sample[2]}")
            
        else:
            print(f"❌ 'properties' table does not exist")
            
            # List available tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            tables = cursor.fetchall()
            print(f"📋 Available tables: {[t[0] for t in tables]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run comprehensive database diagnostics"""
    print("🚀 Starting Database Connection Diagnostics")
    print("=" * 50)
    
    # Get DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("💡 Make sure your .env file exists and contains DATABASE_URL")
        return
    
    print(f"🔗 Database URL found: {database_url[:50]}...")
    
    # Parse the connection string
    try:
        parsed = urlparse(database_url)
        hostname = parsed.hostname
        port = parsed.port or 5432
        username = parsed.username
        password = parsed.password
        database = parsed.path.lstrip('/')
        
        print(f"📊 Connection details:")
        print(f"   Host: {hostname}")
        print(f"   Port: {port}")
        print(f"   User: {username}")
        print(f"   Password: {'*' * len(password) if password else 'None'}")
        print(f"   Database: {database}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to parse DATABASE_URL: {e}")
        return
    
    # Step 1: Test DNS resolution
    dns_success, ip = test_dns_resolution(hostname)
    print()
    
    if not dns_success:
        print("🔍 Trying alternative DNS servers...")
        
        # Try different approaches
        try:
            import subprocess
            result = subprocess.run(['nslookup', hostname, '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10)
            print(f"📋 nslookup output:\n{result.stdout}")
        except:
            pass
        
        return
    
    # Step 2: Test port connectivity
    port_success = test_port_connectivity(hostname, port)
    print()
    
    if not port_success:
        print("❌ Cannot reach the database server")
        print("💡 This could indicate:")
        print("   - Supabase project is paused/suspended")
        print("   - Firewall blocking the connection")
        print("   - Network connectivity issues")
        return
    
    # Step 3: Test PostgreSQL connection
    postgres_success = test_postgres_connection(database_url)
    print()
    
    if postgres_success:
        print("🎉 All database tests passed!")
        print("✅ Your Supabase database is accessible and ready")
    else:
        print("❌ Database connection failed despite network connectivity")
        print("💡 This could indicate:")
        print("   - Incorrect credentials")
        print("   - Database authentication issues")
        print("   - Row Level Security blocking access")

if __name__ == "__main__":
    main() 