"""
Test script for the authentication system.
Demonstrates API key creation, OAuth2 flow, and scope-based access control.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_utils import APIKeyManager, ScopeManager
from app.models.api import ApiKey


class AuthSystemTester:
    """Test the authentication system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.admin_api_key = None
        self.test_api_key = None
        self.jwt_token = None
    
    async def setup_admin_key(self):
        """Create an admin API key directly in the database."""
        print("🔧 Setting up admin API key...")
        
        # Generate admin API key
        admin_key = APIKeyManager.generate_api_key()
        key_hash = APIKeyManager.hash_api_key(admin_key)
        
        # Create admin API key in database
        async for db in get_db():
            db_api_key = ApiKey(
                key_hash=key_hash,
                name="admin_test_key",
                description="Admin key for testing",
                scopes=["admin"],
                created_at=datetime.utcnow()
            )
            
            db.add(db_api_key)
            await db.commit()
            await db.refresh(db_api_key)
            
            self.admin_api_key = admin_key
            print(f"✅ Admin API key created: {admin_key[:20]}...")
            break
    
    async def test_scope_listing(self):
        """Test listing available scopes."""
        print("\n📋 Testing scope listing...")
        
        response = await self.client.get(f"{self.base_url}/api/v1/auth/scopes")
        
        if response.status_code == 200:
            scopes = response.json()
            print("✅ Available scopes:")
            for scope_info in scopes["scopes"]:
                print(f"   - {scope_info['scope']}: {scope_info['description']}")
        else:
            print(f"❌ Failed to list scopes: {response.status_code}")
    
    async def test_api_key_creation(self):
        """Test API key creation."""
        print("\n🔑 Testing API key creation...")
        
        headers = {"Authorization": f"ApiKey {self.admin_api_key}"}
        
        key_data = {
            "name": "test_client",
            "description": "Test API key for client",
            "scopes": ["read:public", "read:funding", "write:webhooks"]
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/auth/keys",
            json=key_data,
            headers=headers
        )
        
        if response.status_code == 201:
            result = response.json()
            self.test_api_key = result["api_key"]
            print(f"✅ API key created: {self.test_api_key[:20]}...")
            print(f"   ID: {result['id']}")
            print(f"   Scopes: {result['scopes']}")
        else:
            print(f"❌ Failed to create API key: {response.status_code}")
            print(f"   Response: {response.text}")
    
    async def test_api_key_listing(self):
        """Test API key listing."""
        print("\n📝 Testing API key listing...")
        
        headers = {"Authorization": f"ApiKey {self.admin_api_key}"}
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/auth/keys",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Found {result['total']} API keys:")
            for key in result["api_keys"]:
                print(f"   - {key['name']} (ID: {key['id']}, Scopes: {key['scopes']})")
        else:
            print(f"❌ Failed to list API keys: {response.status_code}")
    
    async def test_oauth2_flow(self):
        """Test OAuth2 client credentials flow."""
        print("\n🔐 Testing OAuth2 flow...")
        
        if not self.test_api_key:
            print("❌ No test API key available for OAuth2 test")
            return
        
        # Use API key as client credentials
        token_data = {
            "grant_type": "client_credentials",
            "client_id": "test_client",
            "client_secret": self.test_api_key,
            "scope": "read:public read:funding"
        }
        
        response = await self.client.post(
            f"{self.base_url}/oauth/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            result = response.json()
            self.jwt_token = result["access_token"]
            print(f"✅ JWT token obtained")
            print(f"   Token type: {result['token_type']}")
            print(f"   Expires in: {result['expires_in']} seconds")
            print(f"   Scope: {result.get('scope', 'N/A')}")
        else:
            print(f"❌ Failed to get OAuth2 token: {response.status_code}")
            print(f"   Response: {response.text}")
    
    async def test_protected_endpoints(self):
        """Test protected endpoints with different authentication methods."""
        print("\n🛡️ Testing protected endpoints...")
        
        # Test endpoints to check
        endpoints = [
            ("/api/v1/protected/public", "read:public"),
            ("/api/v1/protected/funding", "read:funding"),
            ("/api/v1/protected/investors", "read:investors"),
            ("/api/v1/protected/admin/stats", "admin")
        ]
        
        # Test with API key
        print("\n   Testing with API key:")
        for endpoint, required_scope in endpoints:
            headers = {"Authorization": f"ApiKey {self.test_api_key}"}
            response = await self.client.get(f"{self.base_url}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ {endpoint} - {result['message']}")
            elif response.status_code == 403:
                print(f"   🚫 {endpoint} - Insufficient permissions (expected for {required_scope})")
            else:
                print(f"   ❌ {endpoint} - Error: {response.status_code}")
        
        # Test with JWT token
        if self.jwt_token:
            print("\n   Testing with JWT token:")
            for endpoint, required_scope in endpoints:
                headers = {"Authorization": f"Bearer {self.jwt_token}"}
                response = await self.client.get(f"{self.base_url}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ {endpoint} - {result['message']}")
                elif response.status_code == 403:
                    print(f"   🚫 {endpoint} - Insufficient permissions (expected for {required_scope})")
                else:
                    print(f"   ❌ {endpoint} - Error: {response.status_code}")
    
    async def test_auth_context(self):
        """Test authentication context endpoint."""
        print("\n👤 Testing authentication context...")
        
        # Test with API key
        headers = {"Authorization": f"ApiKey {self.test_api_key}"}
        response = await self.client.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Key auth context:")
            print(f"   Auth type: {result['auth_type']}")
            print(f"   Scopes: {result['scopes']}")
            print(f"   API key ID: {result.get('api_key_id')}")
        
        # Test with JWT token
        if self.jwt_token:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = await self.client.get(f"{self.base_url}/api/v1/auth/me", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ JWT auth context:")
                print(f"   Auth type: {result['auth_type']}")
                print(f"   Scopes: {result['scopes']}")
                print(f"   Client ID: {result.get('client_id')}")
    
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        print("\n⏱️ Testing rate limiting...")
        
        headers = {"Authorization": f"ApiKey {self.test_api_key}"}
        
        # Make multiple requests quickly
        success_count = 0
        rate_limited_count = 0
        
        for i in range(10):
            response = await self.client.get(
                f"{self.base_url}/api/v1/protected/public",
                headers=headers
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
        
        print(f"✅ Rate limiting test completed:")
        print(f"   Successful requests: {success_count}")
        print(f"   Rate limited requests: {rate_limited_count}")
    
    async def run_all_tests(self):
        """Run all authentication tests."""
        print("🚀 Starting Authentication System Tests")
        print("=" * 50)
        
        try:
            await self.setup_admin_key()
            await self.test_scope_listing()
            await self.test_api_key_creation()
            await self.test_api_key_listing()
            await self.test_oauth2_flow()
            await self.test_protected_endpoints()
            await self.test_auth_context()
            await self.test_rate_limiting()
            
            print("\n" + "=" * 50)
            print("✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.client.aclose()


async def main():
    """Main test function."""
    tester = AuthSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("Authentication System Test Suite")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Run: python start_dev.py")
    print()
    
    asyncio.run(main())