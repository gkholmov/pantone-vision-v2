#!/usr/bin/env python3
"""
Supabase Connection Test Script
Tests database connection, tables, and storage bucket access
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not anon_key:
        print("❌ Missing required environment variables!")
        print("   Required: SUPABASE_URL, SUPABASE_ANON_KEY")
        print("   Optional: SUPABASE_SERVICE_ROLE_KEY")
        return None, None, None
    
    return url, anon_key, service_key

def test_basic_connection(supabase: Client):
    """Test basic Supabase connection"""
    try:
        # Try to fetch from auth (this should work even without tables)
        response = supabase.auth.get_session()
        print("✅ Basic connection successful")
        return True
    except Exception as e:
        print(f"❌ Basic connection failed: {e}")
        return False

def test_database_tables(supabase: Client):
    """Test database tables existence and structure"""
    print("\n🔍 Testing database tables...")
    
    tables_to_check = [
        "users",
        "pantone_colors", 
        "processing_history",
        "storage_metadata",
        "api_usage"
    ]
    
    results = {}
    
    for table in tables_to_check:
        try:
            # Try to select from table (limit 1 to minimize data transfer)
            response = supabase.table(table).select("*").limit(1).execute()
            print(f"✅ Table '{table}' exists")
            results[table] = True
        except Exception as e:
            print(f"❌ Table '{table}' error: {e}")
            results[table] = False
    
    return results

def test_pantone_colors_data(supabase: Client):
    """Test if pantone_colors table has initial data"""
    print("\n🎨 Testing Pantone colors data...")
    
    try:
        response = supabase.table("pantone_colors").select("*").limit(5).execute()
        data = response.data
        
        if data:
            print(f"✅ Found {len(data)} Pantone colors (showing first 5):")
            for color in data:
                print(f"   - {color.get('pantone_code', 'N/A')}: {color.get('pantone_name', 'N/A')} ({color.get('hex_color', 'N/A')})")
            return True
        else:
            print("⚠️  No Pantone colors found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching Pantone colors: {e}")
        return False

def test_storage_bucket(supabase: Client):
    """Test storage bucket access"""
    print("\n📁 Testing storage bucket...")
    
    try:
        # Try to list objects in the bucket
        response = supabase.storage.from_("pantone-images").list()
        print("✅ Storage bucket 'pantone-images' accessible")
        
        if response:
            print(f"   Found {len(response)} objects in bucket")
        else:
            print("   Bucket is empty (this is normal for new setup)")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage bucket error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Supabase Connection Test")
    print("=" * 50)
    
    # Load environment
    url, anon_key, service_key = load_environment()
    if not url:
        sys.exit(1)
    
    print(f"🔗 Connecting to: {url}")
    print(f"🔑 Using anon key: {anon_key[:20]}..." if anon_key else "❌ No anon key")
    print(f"🔐 Service key available: {'Yes' if service_key else 'No'}")
    
    # Create Supabase client
    try:
        supabase: Client = create_client(url, anon_key)
        print("✅ Supabase client created")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        sys.exit(1)
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Basic connection
    total_tests += 1
    if test_basic_connection(supabase):
        tests_passed += 1
    
    # Test 2: Database tables
    total_tests += 1
    table_results = test_database_tables(supabase)
    if all(table_results.values()):
        tests_passed += 1
        print("✅ All tables accessible")
    else:
        failed_tables = [table for table, success in table_results.items() if not success]
        print(f"❌ Failed tables: {', '.join(failed_tables)}")
    
    # Test 3: Pantone colors data
    total_tests += 1
    if test_pantone_colors_data(supabase):
        tests_passed += 1
    
    # Test 4: Storage bucket
    total_tests += 1
    if test_storage_bucket(supabase):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Supabase is ready for production.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the setup guide for troubleshooting.")
        sys.exit(1)

if __name__ == "__main__":
    main()