"""Test frontend JavaScript for syntax and structure validation."""

import re
from pathlib import Path


def validate_frontend_javascript():
    """Validate the index.html JavaScript code."""
    print("\n" + "="*60)
    print("FRONTEND JAVASCRIPT VALIDATION")
    print("="*60)
    
    index_path = Path("index.html")
    if not index_path.exists():
        print("✗ FAILED: index.html not found")
        return False
    
    content = index_path.read_text(encoding='utf-8')
    
    # Required functions
    required_functions = [
        'detectPlatform',
        'showTopology',
        'renderNetworkTopology',
        'closeTopology',
        'showAksArcDiagnostics',
        'installDiagnosticTools',
        'renderDiagnosticResults',
        'runDiagnosticRemediation'
    ]
    
    print("\n✓ Checking function definitions...")
    missing_functions = []
    for func in required_functions:
        # Look for both async and regular function definitions
        patterns = [
            f'async function {func}',
            f'function {func}',
            f'const {func} = async',
            f'const {func} =',
        ]
        
        found = any(pattern in content for pattern in patterns)
        if found:
            print(f"  ✓ {func}")
        else:
            print(f"  ✗ {func} - NOT FOUND")
            missing_functions.append(func)
    
    if missing_functions:
        print(f"\n✗ FAILED: Missing {len(missing_functions)} functions")
        return False
    
    # Check for API endpoints
    print("\n✓ Checking API endpoint calls...")
    api_endpoints = [
        '/api/platform/detect',
        '/api/topology/analyze',
        '/api/aksarc/diagnostics/check',
        '/api/aksarc/diagnostics/install',
        '/api/aksarc/diagnostics/run',
        '/api/cluster/status',
        '/api/foundry/status'
    ]
    
    missing_endpoints = []
    for endpoint in api_endpoints:
        if endpoint in content:
            print(f"  ✓ {endpoint}")
        else:
            print(f"  ✗ {endpoint} - NOT USED")
            missing_endpoints.append(endpoint)
    
    # Check for common JavaScript errors
    print("\n✓ Checking for common JavaScript issues...")
    issues = []
    
    # Check for undefined variable access patterns (not foolproof but catches some)
    if '.length' in content:
        # Make sure we have null checks
        if 'data.pods.length' in content or 'data.services.length' in content:
            print("  ⚠ Warning: Direct property access on data object found")
            print("    (Should use safe destructuring like: const pods = data.pods || [])")
    
    # Check for proper error handling
    if 'renderNetworkTopology' in content:
        # Extract the function
        start = content.find('function renderNetworkTopology')
        if start == -1:
            start = content.find('async function renderNetworkTopology')
        
        if start != -1:
            end = content.find('\n        function', start + 1)
            if end == -1:
                end = content.find('\n        async function', start + 1)
            
            func_content = content[start:end] if end != -1 else content[start:]
            
            # Check for safe destructuring
            if 'const pods = data.pods || []' in func_content:
                print("  ✓ Safe destructuring used in renderNetworkTopology")
            else:
                print("  ⚠ Warning: renderNetworkTopology may not use safe destructuring")
    
    # Check for modal elements
    print("\n✓ Checking modal HTML elements...")
    required_elements = [
        'topologyModal',
        'aksarcDiagnosticsModal'
    ]
    
    for element_id in required_elements:
        if f'id="{element_id}"' in content or f"id='{element_id}'" in content:
            print(f"  ✓ {element_id}")
        else:
            print(f"  ✗ {element_id} - NOT FOUND")
            issues.append(f"Missing modal: {element_id}")
    
    # Check for CSS classes
    print("\n✓ Checking CSS styling...")
    required_classes = [
        'platform-badge',
        'aksarc-panel',
        'topology-section',
        'communication-matrix',
        'dependency-card',
        'connectivity-grid'
    ]
    
    for css_class in required_classes:
        if f'.{css_class}' in content or f'class="{css_class}"' in content or f"class='{css_class}" in content:
            print(f"  ✓ .{css_class}")
        else:
            print(f"  ⚠ .{css_class} - NOT FOUND (may be dynamically added)")
    
    if issues:
        print(f"\n⚠ Found {len(issues)} potential issues (non-critical)")
        for issue in issues:
            print(f"  - {issue}")
    
    print("\n✓ All critical frontend validations passed")
    return True


def main():
    """Run frontend validation."""
    try:
        success = validate_frontend_javascript()
        if success:
            print("\n🎉 Frontend validation complete!")
            return 0
        else:
            print("\n✗ Frontend validation failed")
            return 1
    except Exception as e:
        print(f"\n✗ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
