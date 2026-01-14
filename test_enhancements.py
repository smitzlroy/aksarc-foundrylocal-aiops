"""Comprehensive automated testing for AKS Arc enhancements."""

import asyncio
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from src.services.kubernetes import KubernetesClient
from src.services.network_analyzer import NetworkAnalyzer
from src.services.aks_arc_diagnostics import AksArcDiagnostics


async def test_platform_detection():
    """Test platform detection functionality."""
    print("\n" + "="*60)
    print("TEST 1: Platform Detection")
    print("="*60)
    
    try:
        k8s = KubernetesClient()
        await k8s.connect()
        
        platform_info = await k8s.get_platform_info()
        print(f"✓ Platform Type: {platform_info['type']}")
        print(f"✓ Details: {json.dumps(platform_info.get('details', {}), indent=2)}")
        
        await k8s.disconnect()
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


async def test_network_topology():
    """Test network topology analysis."""
    print("\n" + "="*60)
    print("TEST 2: Network Topology Analysis")
    print("="*60)
    
    try:
        k8s = KubernetesClient()
        await k8s.connect()
        
        analyzer = NetworkAnalyzer(k8s)
        topology = await analyzer.analyze_topology()
        
        print(f"✓ Pods found: {len(topology['pods'])}")
        print(f"✓ Services found: {len(topology['services'])}")
        print(f"✓ Dependencies: {len(topology['dependencies'])}")
        print(f"✓ Communication matrix: {len(topology['communication_matrix'])}")
        print(f"✓ Network policies: {topology['network_policies']['total_policies']}")
        print(f"✓ Namespace connectivity: {len(topology['namespace_connectivity'])} namespaces")
        
        # Check data structure
        print("\n  Data Structure Validation:")
        assert isinstance(topology['pods'], list), "pods should be a list"
        assert isinstance(topology['services'], list), "services should be a list"
        assert isinstance(topology['dependencies'], list), "dependencies should be a list"
        assert isinstance(topology['communication_matrix'], list), "communication_matrix should be a list"
        assert isinstance(topology['network_policies'], dict), "network_policies should be a dict"
        assert isinstance(topology['namespace_connectivity'], dict), "namespace_connectivity should be a dict"
        
        # Validate namespace_connectivity structure
        for ns, info in topology['namespace_connectivity'].items():
            assert isinstance(info, dict), f"namespace_connectivity[{ns}] should be a dict"
            assert 'can_access' in info, f"namespace_connectivity[{ns}] missing 'can_access'"
            assert isinstance(info['can_access'], list), f"can_access should be a list"
        
        print("  ✓ All data structures valid")
        
        # Sample output
        if topology['pods']:
            print(f"\n  Sample Pod: {topology['pods'][0]['name']} ({topology['pods'][0]['namespace']})")
        if topology['communication_matrix']:
            print(f"  Sample Connection: {topology['communication_matrix'][0]}")
        
        await k8s.disconnect()
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_aks_arc_diagnostics():
    """Test AKS Arc diagnostics functionality."""
    print("\n" + "="*60)
    print("TEST 3: AKS Arc Diagnostics")
    print("="*60)
    
    try:
        diagnostics = AksArcDiagnostics()
        
        # Test prerequisites check
        prereqs = await diagnostics.check_prerequisites()
        print(f"✓ PowerShell available: {prereqs['powershell_available']}")
        print(f"✓ Support.AksArc module: {prereqs['support_module_available']}")
        
        if not prereqs['powershell_available']:
            print("  ! PowerShell not available - diagnostic tests limited")
            return True
        
        if not prereqs['support_module_available']:
            print("  ! Support.AksArc module not installed - skipping diagnostic tests")
            print("  (This is expected on non-AKS Arc clusters)")
            return True
        
        # If we have the module, try running diagnostics
        print("\n  Running diagnostic checks...")
        results = await diagnostics.run_diagnostic_checks()
        print(f"  ✓ Diagnostic checks completed: {len(results)} issues found")
        
        for i, result in enumerate(results[:3], 1):
            print(f"    {i}. {result.get('issue', 'Unknown issue')}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_frontend_data_compatibility():
    """Test that backend data structure matches frontend expectations."""
    print("\n" + "="*60)
    print("TEST 4: Frontend Data Compatibility")
    print("="*60)
    
    try:
        k8s = KubernetesClient()
        await k8s.connect()
        
        analyzer = NetworkAnalyzer(k8s)
        topology = await analyzer.analyze_topology()
        
        # Simulate frontend code expectations
        print("  Testing frontend compatibility...")
        
        # Test 1: Safe array access
        pods = topology.get('pods') or []
        services = topology.get('services') or []
        dependencies = topology.get('dependencies') or []
        comm_matrix = topology.get('communication_matrix') or []
        
        print(f"  ✓ Arrays accessible: {len(pods)} pods, {len(services)} services")
        
        # Test 2: Namespace connectivity structure
        ns_connectivity = topology.get('namespace_connectivity', {})
        for ns, info in ns_connectivity.items():
            if not isinstance(info, dict):
                print(f"  ✗ ERROR: namespace_connectivity[{ns}] is not a dict: {type(info)}")
                return False
            if 'can_access' not in info:
                print(f"  ✗ ERROR: namespace_connectivity[{ns}] missing 'can_access' key")
                return False
            if not isinstance(info['can_access'], list):
                print(f"  ✗ ERROR: can_access is not a list: {type(info['can_access'])}")
                return False
        
        print(f"  ✓ Namespace connectivity structure valid for {len(ns_connectivity)} namespaces")
        
        # Test 3: Network policies structure
        policies = topology.get('network_policies', {})
        if 'unrestricted_namespaces' in policies:
            if not isinstance(policies['unrestricted_namespaces'], list):
                print(f"  ✗ ERROR: unrestricted_namespaces is not a list")
                return False
        
        print("  ✓ Network policies structure valid")
        
        # Test 4: Communication matrix has required fields
        if comm_matrix:
            required_fields = ['source', 'target', 'protocol', 'port']
            for field in required_fields:
                if field not in comm_matrix[0]:
                    print(f"  ✗ ERROR: communication_matrix missing field: {field}")
                    return False
            print(f"  ✓ Communication matrix fields valid")
        
        print("\n  ✓ All frontend compatibility checks passed")
        
        await k8s.disconnect()
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("COMPREHENSIVE AUTOMATED TESTING")
    print("AKS Arc Enhanced K8s AI Assistant")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Platform Detection", await test_platform_detection()))
    results.append(("Network Topology", await test_network_topology()))
    results.append(("AKS Arc Diagnostics", await test_aks_arc_diagnostics()))
    results.append(("Frontend Compatibility", await test_frontend_data_compatibility()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System ready for deployment.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
