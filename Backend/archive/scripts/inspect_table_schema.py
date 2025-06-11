#!/usr/bin/env python3
"""
Inspect Supabase table schema to understand the actual structure
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def inspect_table_schema():
    """Inspect the properties table schema"""
    try:
        from supabase import create_client, Client
        
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔍 Inspecting table schema...")
        
        # Method 1: Try to get all data from properties table (limited)
        try:
            result = supabase.table('properties').select("*").limit(1).execute()
            
            if result.data and len(result.data) > 0:
                print("✅ Properties table exists!")
                sample_record = result.data[0]
                
                print(f"📊 Table columns found:")
                for column, value in sample_record.items():
                    value_type = type(value).__name__
                    value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"   {column}: {value_type} = {value_preview}")
                
                print(f"\n📈 Sample record keys: {list(sample_record.keys())}")
                return True
            else:
                print("❌ Properties table exists but has no data")
                return False
                
        except Exception as e:
            print(f"❌ Error querying properties table: {e}")
            
            # Method 2: Try different common column names
            print("\n🔍 Trying different column combinations...")
            
            test_columns = [
                ["*"],
                ["listing_number", "title", "price"],
                ["id", "title", "city"],
                ["property_id", "title", "location"],
            ]
            
            for columns in test_columns:
                try:
                    col_str = ",".join(columns)
                    print(f"   Testing: {col_str}")
                    result = supabase.table('properties').select(col_str).limit(1).execute()
                    
                    if result.data:
                        print(f"   ✅ Success with: {col_str}")
                        print(f"   📝 Data: {result.data[0]}")
                        return True
                except Exception as inner_e:
                    print(f"   ❌ Failed: {inner_e}")
            
            return False
            
    except ImportError:
        print("❌ Supabase client not available")
        return False
    except Exception as e:
        print(f"❌ Failed to inspect schema: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Inspecting Supabase Table Schema")
    print("=" * 40)
    
    success = inspect_table_schema()
    
    if success:
        print("\n🎉 Table schema inspection completed!")
    else:
        print("\n❌ Could not inspect table schema")
        print("💡 Check if the properties table exists and has data")

if __name__ == "__main__":
    main() 