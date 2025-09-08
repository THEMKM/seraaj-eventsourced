#!/usr/bin/env python3
"""
Test script to validate service communication
"""
import asyncio
import httpx
import sys
from services.shared.port_config import PortConfigManager
from infrastructure.service_registry import ServiceRegistry


async def test_service_health(name: str, url: str) -> bool:
    """Test if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/health")
            if response.status_code == 200:
                print(f"✅ {name}: {url} - HEALTHY")
                return True
            else:
                print(f"❌ {name}: {url} - UNHEALTHY (status: {response.status_code})")
                return False
    except Exception as e:
        print(f"❌ {name}: {url} - CONNECTION FAILED ({e})")
        return False


async def test_service_communication():
    """Test communication between all services"""
    print("Testing Service Communication")
    print("=" * 50)
    
    # Test port configuration
    print("\nPort Configuration:")
    config_manager = PortConfigManager()
    config_manager.print_service_configuration()
    
    # Test service registry
    print("\nService Registry:")
    service_registry = ServiceRegistry()
    service_registry.register_default_services()
    
    # Test individual service health
    print("\nHealth Checks:")
    services_to_test = [
        ("BFF", "http://localhost:8000"),
        ("Auth", "http://localhost:8004"), 
        ("Applications", "http://localhost:8001"),
        ("Matching", "http://localhost:8003"),
        ("Volunteers", "http://localhost:8005"),
        ("Opportunities", "http://localhost:8006"),
        ("Organizations", "http://localhost:8007")
    ]
    
    healthy_count = 0
    for name, url in services_to_test:
        is_healthy = await test_service_health(name, url)
        if is_healthy:
            healthy_count += 1
    
    print(f"\nSummary: {healthy_count}/{len(services_to_test)} services healthy")
    
    # Test BFF API endpoints
    print("\nBFF API Tests:")
    if healthy_count > 0:
        await test_bff_endpoints()
    else:
        print("Skipping BFF tests - no services are healthy")
    
    return healthy_count == len(services_to_test)


async def test_bff_endpoints():
    """Test key BFF endpoints"""
    base_url = "http://localhost:8000/api"
    
    endpoints_to_test = [
        ("Health", f"{base_url}/health", "GET"),
        ("Services Health", f"{base_url}/health/services", "GET"),
    ]
    
    for name, url, method in endpoints_to_test:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if method == "GET":
                    response = await client.get(url)
                
                if response.status_code == 200:
                    print(f"✅ {name}: {response.status_code}")
                else:
                    print(f"⚠️ {name}: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ {name}: Failed - {e}")


async def main():
    """Main test function"""
    success = await test_service_communication()
    
    if success:
        print("\nAll services are communicating properly!")
        sys.exit(0)
    else:
        print("\nSome services have communication issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())