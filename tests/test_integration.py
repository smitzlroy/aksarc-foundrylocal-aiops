"""Integration tests for API endpoints."""

import time
import subprocess
import sys


def wait_for_server(max_wait=30):
    """Wait for server to be responsive."""
    print("⏳ Waiting for server to start...")
    for i in range(max_wait):
        try:
            result = subprocess.run(
                ['curl', 'http://localhost:8000/', '-s', '-o', 'NUL', '-w', '%{http_code}'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if '200' in result.stdout:
                print(f"✓ Server ready after {i+1}s")
                return True
        except:
            pass
        time.sleep(1)
    return False


def test_endpoint(name, url, method='GET'):
    """Test an API endpoint."""
    try:
        if method == 'GET':
            result = subprocess.run(
                ['curl', '-s', url],
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            result = subprocess.run(
                ['curl', '-s', '-X', method, url],
                capture_output=True,
                text=True,
                timeout=10
            )
        
        if result.returncode == 0 and result.stdout:
            # Try to parse as JSON
            import json
            try:
                data = json.loads(result.stdout)
                print(f"✓ {name}: OK (returned {len(str(data))} chars)")
                return True, data
            except:
                # Not JSON, but got response
                print(f"✓ {name}: OK (non-JSON response)")
                return True, result.stdout
        else:
            print(f"✗ {name}: FAILED - {result.stderr}")
            return False, None
    except Exception as e:
        print(f"✗ {name}: ERROR - {e}")
        return False, None


def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("API INTEGRATION TESTS")
    print("="*60)
    
    # Wait for server
    if not wait_for_server():
        print("✗ Server not responding")
        return 1
    
    print("\n✓ Testing API endpoints...")
    
    endpoints = [
        ("Health Check", "http://localhost:8000/", "GET"),
        ("Platform Detection", "http://localhost:8000/api/platform/detect", "GET"),
        ("Cluster Status", "http://localhost:8000/api/cluster/status", "GET"),
        ("Foundry Status", "http://localhost:8000/api/foundry/status", "GET"),
        ("Network Topology", "http://localhost:8000/api/topology/analyze", "GET"),
        ("AKS Arc Prerequisites", "http://localhost:8000/api/aksarc/diagnostics/check", "GET"),
    ]
    
    results = []
    for name, url, method in endpoints:
        success, data = test_endpoint(name, url, method)
        results.append((name, success))
        time.sleep(0.5)  # Be nice to the server
    
    # Summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} endpoints working")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print("\n⚠️  Some endpoints failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
