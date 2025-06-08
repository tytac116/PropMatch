#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script for PropMatch API

This script tests all endpoints and provides detailed output for debugging.
Run this before testing with Postman to ensure everything works.

Usage:
    python test_api_endpoints.py
"""

import asyncio
import httpx
import json
import os
import sys
from typing import Dict, Any, Optional
import time

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = None
        self.results = []
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def log_test(self, test_name: str, status: str, details: Dict[str, Any]):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            **details
        }
        self.results.append(result)
        
        # Color coding for terminal
        color = "\033[92m" if status == "PASS" else "\033[91m" if status == "FAIL" else "\033[93m"
        reset = "\033[0m"
        
        print(f"{color}[{status}]{reset} {test_name}")
        if details.get("error"):
            print(f"  Error: {details['error']}")
        elif details.get("response_data"):
            print(f"  Response: {details['response_data']}")
        print()
    
    async def test_endpoint(self, method: str, endpoint: str, test_name: str, 
                          data: Optional[Dict] = None, params: Optional[Dict] = None,
                          expected_status: int = 200) -> Dict[str, Any]:
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = await self.client.get(url, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Check status
            if response.status_code == expected_status:
                self.log_test(test_name, "PASS", {
                    "status_code": response.status_code,
                    "response_size": len(str(response_data)),
                    "url": url
                })
                return {"success": True, "data": response_data}
            else:
                self.log_test(test_name, "FAIL", {
                    "status_code": response.status_code,
                    "expected": expected_status,
                    "error": str(response_data),
                    "url": url
                })
                return {"success": False, "error": str(response_data)}
                
        except Exception as e:
            self.log_test(test_name, "ERROR", {
                "error": str(e),
                "url": f"{self.base_url}{endpoint}"
            })
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting PropMatch API Testing Suite")
        print("=" * 50)
        
        # 1. Health checks
        await self.test_endpoint("GET", "/", "Root Health Check")
        await self.test_endpoint("GET", "/health", "General Health Check")
        await self.test_endpoint("GET", "/api/v1/search/health", "Search Service Health Check")
        
        print("\n📊 Testing Properties Endpoints")
        print("-" * 30)
        
        # 2. Properties endpoints
        await self.test_endpoint("GET", "/api/v1/properties/", "Get All Properties (Default)")
        await self.test_endpoint("GET", "/api/v1/properties/", "Get Properties with Pagination", 
                                params={"skip": 0, "limit": 5})
        await self.test_endpoint("GET", "/api/v1/properties/", "Filter by Property Type", 
                                params={"property_type": "House", "limit": 3})
        await self.test_endpoint("GET", "/api/v1/properties/", "Filter by Price Range", 
                                params={"min_price": 1000000, "max_price": 3000000, "limit": 5})
        await self.test_endpoint("GET", "/api/v1/properties/", "Filter by Bedrooms", 
                                params={"bedrooms": 3, "limit": 5})
        await self.test_endpoint("GET", "/api/v1/properties/", "Filter by City", 
                                params={"city": "Cape Town", "limit": 5})
        
        # Get property stats
        await self.test_endpoint("GET", "/api/v1/properties/stats/summary", "Property Statistics")
        
        # Try to get a specific property (we'll need to get an ID first)
        props_result = await self.test_endpoint("GET", "/api/v1/properties/", "Get Property for ID Test", 
                                              params={"limit": 1})
        if props_result["success"] and props_result["data"]:
            properties = props_result["data"]
            if properties and len(properties) > 0:
                property_id = properties[0].get("id")
                if property_id:
                    await self.test_endpoint("GET", f"/api/v1/properties/{property_id}", 
                                           "Get Specific Property by ID")
                
                # Try listing number if available
                listing_number = properties[0].get("listing_number")
                if listing_number:
                    await self.test_endpoint("GET", f"/api/v1/properties/listing/{listing_number}", 
                                           "Get Property by Listing Number")
        
        print("\n🔍 Testing Search Endpoints")
        print("-" * 30)
        
        # 3. Search endpoints
        search_requests = [
            {
                "query": "3 bedroom house near schools",
                "filters": {"property_type": "house", "bedrooms": 3},
                "page": 1,
                "page_size": 5
            },
            {
                "query": "apartment with sea view",
                "page": 1,
                "page_size": 3
            },
            {
                "query": "luxury property in Camps Bay",
                "filters": {"min_price": 5000000},
                "page": 1,
                "page_size": 5
            }
        ]
        
        for i, search_req in enumerate(search_requests, 1):
            await self.test_endpoint("POST", "/api/v1/search/", f"AI Search Test {i}", 
                                   data=search_req, params={"use_ai": True})
            await self.test_endpoint("POST", "/api/v1/search/", f"Basic Search Test {i}", 
                                   data=search_req, params={"use_ai": False})
        
        # Simple search tests
        simple_searches = [
            {"query": "cheap apartment", "limit": 3, "use_ai": True},
            {"query": "house with garden", "limit": 5, "use_ai": False},
            {"query": "modern flat", "limit": 2, "use_ai": True}
        ]
        
        for i, search_data in enumerate(simple_searches, 1):
            await self.test_endpoint("POST", "/api/v1/search/simple", f"Simple Search Test {i}", 
                                   data=search_data)
        
        # Vector search test
        await self.test_endpoint("GET", "/api/v1/search/test-vector", "Vector Search Test",
                               params={"query": "family home near amenities", "limit": 3})
        
        # Explanation test (placeholder endpoint)
        if props_result["success"] and props_result["data"] and len(props_result["data"]) > 0:
            property_id = props_result["data"][0].get("id")
            if property_id:
                await self.test_endpoint("POST", f"/api/v1/search/explanation/{property_id}", 
                                       "Property Explanation Test",
                                       data={"search_query": "family home with garden"})
        
        print("\n📋 Test Summary")
        print("=" * 50)
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        errors = len([r for r in self.results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Errors: {errors}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0 or errors > 0:
            print("\n🚨 Failed/Error Tests:")
            for result in self.results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"  • {result['test']}: {result.get('error', 'Unknown error')}")

async def check_server_running():
    """Check if the FastAPI server is running"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/")
            return response.status_code == 200
    except:
        return False

async def main():
    print("🔧 PropMatch API Testing Suite")
    print("=" * 50)
    
    # Check if server is running
    print("Checking if server is running...")
    if not await check_server_running():
        print(f"❌ Server is not running at {BASE_URL}")
        print("\n💡 To start the server, run:")
        print("   cd Backend")
        print("   uvicorn app.main:app --reload --port 8000")
        print("\nThen run this test script again.")
        return
    
    print(f"✅ Server is running at {BASE_URL}")
    print()
    
    # Run tests
    async with APITester() as tester:
        await tester.run_all_tests()
    
    print("\n🎉 Testing Complete!")
    print("\nNext Steps:")
    print("1. Review any failed tests above")
    print("2. Use the Postman collection for manual testing")
    print("3. Check server logs for detailed error information")

if __name__ == "__main__":
    asyncio.run(main()) 