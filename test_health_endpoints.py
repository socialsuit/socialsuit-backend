import requests
import sys
import time

def test_health_endpoint(url, service_name):
    """Test a health endpoint and return the result."""
    print(f"\nTesting {service_name} health endpoint at {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print(f"✅ {service_name} health check passed!")
            return True
        else:
            print(f"❌ {service_name} health check failed with status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name} health check failed: {e}")
        return False

def test_ping_endpoint(url, service_name):
    """Test a ping endpoint and return the result."""
    print(f"\nTesting {service_name} ping endpoint at {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            print(f"✅ {service_name} ping check passed!")
            return True
        else:
            print(f"❌ {service_name} ping check failed with status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name} ping check failed: {e}")
        return False

def main():
    """Main function to test health endpoints."""
    print("=== Health Endpoint Testing ===\n")
    
    # Define services to test
    services = [
        {
            "name": "Social Suit",
            "health_url": "http://localhost:8000/healthz",
            "ping_url": "http://localhost:8000/ping"
        },
        {
            "name": "Sparkr",
            "health_url": "http://localhost:8001/healthz",
            "ping_url": "http://localhost:8001/ping"
        }
    ]
    
    # Test each service
    results = []
    for service in services:
        health_result = test_health_endpoint(service["health_url"], service["name"])
        ping_result = test_ping_endpoint(service["ping_url"], service["name"])
        results.append((service["name"], health_result and ping_result))
    
    # Print summary
    print("\n=== Test Summary ===")
    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    # Exit with appropriate code
    if all_passed:
        print("\nAll health checks passed!")
        return 0
    else:
        print("\nSome health checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())