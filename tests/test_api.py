"""Test the AKS Arc AI Ops API."""

import asyncio
import time

import httpx


async def test_api():
    """Test all API endpoints."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing AKS Arc AI Ops API\n")
        
        # Test root endpoint
        print("1️⃣ Testing root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")
        
        # Test health check
        print("2️⃣ Testing health check...")
        response = await client.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Overall Status: {data['status']}")
        print(f"   Services: {data['services']}\n")
        
        # Test cluster status
        print("3️⃣ Testing cluster status...")
        response = await client.get(f"{base_url}/api/cluster/status")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Timestamp: {data['timestamp']}")
        print(f"   Pods: {len(data['pods'])}")
        print(f"   Events: {len(data['events'])}\n")
        
        # Test get pods
        print("4️⃣ Testing get pods...")
        response = await client.get(f"{base_url}/api/cluster/pods")
        print(f"   Status: {response.status_code}")
        pods = response.json()
        print(f"   Total Pods: {len(pods)}")
        for pod in pods[:3]:
            print(f"      • {pod['namespace']}/{pod['name']} - {pod['phase']}")
        print()
        
        # Test filter by namespace
        print("5️⃣ Testing get pods (kube-system namespace)...")
        response = await client.get(
            f"{base_url}/api/cluster/pods",
            params={"namespace": "kube-system"}
        )
        print(f"   Status: {response.status_code}")
        pods = response.json()
        print(f"   Pods in kube-system: {len(pods)}\n")
        
        # Test get events
        print("6️⃣ Testing get events...")
        response = await client.get(
            f"{base_url}/api/cluster/events",
            params={"hours": 1}
        )
        print(f"   Status: {response.status_code}")
        events = response.json()
        print(f"   Events in last hour: {len(events)}\n")
        
        # Wait a bit for watcher to collect more data
        print("⏱️  Waiting 5 seconds for watcher to collect more snapshots...")
        await asyncio.sleep(5)
        
        # Test pod history
        if pods:
            first_pod = pods[0]
            print(f"7️⃣ Testing pod history for {first_pod['name']}...")
            response = await client.get(
                f"{base_url}/api/cluster/pods/{first_pod['namespace']}/{first_pod['name']}/history",
                params={"hours": 1}
            )
            print(f"   Status: {response.status_code}")
            history = response.json()
            print(f"   History entries: {len(history)}\n")
        
        print("✅ All tests completed successfully!")


if __name__ == "__main__":
    print("Starting API tests...\n")
    print("Make sure the server is running with: cd backend && python run.py\n")
    time.sleep(2)
    
    try:
        asyncio.run(test_api())
    except httpx.ConnectError:
        print("❌ Error: Could not connect to server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
