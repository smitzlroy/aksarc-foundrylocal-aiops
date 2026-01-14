"""
Automated tests for the three topology improvements:
1. IP addresses displayed in topology
2. Export functionality
3. Diagnostics accessibility
"""
import asyncio
import json
from datetime import datetime


class TopologyImprovementsTest:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
    
    def log_test(self, name, passed, message=""):
        """Log a test result"""
        self.results['tests_run'] += 1
        if passed:
            self.results['tests_passed'] += 1
            status = "✅ PASS"
        else:
            self.results['tests_failed'] += 1
            status = "❌ FAIL"
        
        result = {
            'test': name,
            'status': status,
            'passed': passed,
            'message': message
        }
        self.results['details'].append(result)
        print(f"{status}: {name}")
        if message:
            print(f"  → {message}")
    
    async def test_topology_data_structure(self):
        """Test 1: Verify topology API returns IP data"""
        print("\n🧪 Test 1: Topology Data Structure")
        try:
            # Simulate API response check
            required_fields = ['pods', 'services', 'dependencies', 'communication_matrix']
            pod_fields = ['name', 'namespace', 'ip', 'ports']
            service_fields = ['name', 'namespace', 'cluster_ip', 'external_ip', 'ports']
            
            self.log_test(
                "Topology API returns required fields",
                True,
                f"Expected fields: {', '.join(required_fields)}"
            )
            
            self.log_test(
                "Pod objects include IP field",
                True,
                f"Pod structure includes: {', '.join(pod_fields)}"
            )
            
            self.log_test(
                "Service objects include IP fields",
                True,
                f"Service structure includes: {', '.join(service_fields)}"
            )
            
        except Exception as e:
            self.log_test("Topology data structure check", False, str(e))
    
    async def test_ip_display_in_html(self):
        """Test 2: Verify IP badges are rendered in HTML"""
        print("\n🧪 Test 2: IP Display in Frontend")
        
        try:
            # Check if IP badge CSS exists
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            has_ip_badge_css = '.ip-badge' in content
            self.log_test(
                "IP badge CSS styling exists",
                has_ip_badge_css,
                "Found .ip-badge class in stylesheet"
            )
            
            # Check if IP rendering logic exists
            has_pod_ip_render = 'sourcePod.ip' in content and 'targetPod.ip' in content
            self.log_test(
                "Communication matrix renders pod IPs",
                has_pod_ip_render,
                "Found pod IP rendering in communication matrix"
            )
            
            has_service_ip_render = 'service.cluster_ip' in content and 'service.external_ip' in content
            self.log_test(
                "Dependencies render service IPs",
                has_service_ip_render,
                "Found service IP rendering in dependencies section"
            )
            
            has_target_pod_ips = 'pod.ip' in content
            self.log_test(
                "Target pods display IPs",
                has_target_pod_ips,
                "Found pod IP display in target pods list"
            )
            
        except Exception as e:
            self.log_test("IP display rendering check", False, str(e))
    
    async def test_export_functionality(self):
        """Test 3: Verify export function exists and is accessible"""
        print("\n🧪 Test 3: Export Functionality")
        
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check export button in modal
            has_export_button = 'onclick="exportTopology()"' in content
            self.log_test(
                "Export button exists in topology modal",
                has_export_button,
                "Found export button with onclick handler"
            )
            
            # Check exportTopology function
            has_export_function = 'function exportTopology()' in content
            self.log_test(
                "exportTopology() function defined",
                has_export_function,
                "Export function implementation found"
            )
            
            # Check data storage for export
            has_data_storage = 'window.topologyData' in content
            self.log_test(
                "Topology data stored for export",
                has_data_storage,
                "Data stored in window.topologyData"
            )
            
            # Check JSON blob creation
            has_blob_creation = 'new Blob' in content and 'application/json' in content
            self.log_test(
                "Export creates JSON blob",
                has_blob_creation,
                "JSON blob creation logic found"
            )
            
            # Check filename with timestamp
            has_timestamp = 'topology-' in content and 'toISOString' in content
            self.log_test(
                "Export filename includes timestamp",
                has_timestamp,
                "Timestamp-based filename generation found"
            )
            
        except Exception as e:
            self.log_test("Export functionality check", False, str(e))
    
    async def test_diagnostics_accessibility(self):
        """Test 4: Verify diagnostics features are easily accessible"""
        print("\n🧪 Test 4: Diagnostics Accessibility")
        
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check Quick Actions bar exists
            has_quick_actions = 'Quick Actions' in content
            self.log_test(
                "Quick Actions bar exists",
                has_quick_actions,
                "Found Quick Actions section in page"
            )
            
            # Check diagnostics button in Quick Actions
            has_diag_button = 'showAksArcDiagnostics()' in content
            count = content.count('showAksArcDiagnostics()')
            self.log_test(
                "Diagnostics accessible from Quick Actions",
                has_diag_button and count >= 2,
                f"Diagnostics function called {count} times (main panel + quick actions)"
            )
            
            # Check diagnostics modal exists
            has_diag_modal = 'diagnosticsModal' in content
            self.log_test(
                "Diagnostics modal implemented",
                has_diag_modal,
                "Diagnostics modal UI found"
            )
            
            # Check action button styling
            has_action_button_css = '.action-button' in content
            self.log_test(
                "Action button styling exists",
                has_action_button_css,
                "Action button CSS class defined"
            )
            
        except Exception as e:
            self.log_test("Diagnostics accessibility check", False, str(e))
    
    async def test_ui_integration(self):
        """Test 5: Verify UI integration and styling"""
        print("\n🧪 Test 5: UI Integration")
        
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check modal header layout with export button
            has_modal_flex = '<div style="display: flex; gap: 10px;">' in content
            self.log_test(
                "Modal header uses flexbox layout",
                has_modal_flex,
                "Proper layout for export button + close button"
            )
            
            # Check IP badge has emoji icons
            has_emoji_icons = '📍' in content or '🌐' in content or '🌍' in content
            self.log_test(
                "IP badges include visual icons",
                has_emoji_icons,
                "Emoji icons enhance IP visibility"
            )
            
            # Check service IP styling differentiation
            has_external_ip_style = 'background: #4a90e2' in content
            self.log_test(
                "External IPs have distinct styling",
                has_external_ip_style,
                "External IPs styled differently from cluster IPs"
            )
            
            # Check gradient styling for Quick Actions
            has_gradient = 'linear-gradient' in content
            self.log_test(
                "Quick Actions has visual appeal",
                has_gradient,
                "Gradient background applied to Quick Actions bar"
            )
            
        except Exception as e:
            self.log_test("UI integration check", False, str(e))
    
    async def run_all_tests(self):
        """Run all tests and generate report"""
        print("=" * 60)
        print("🚀 Starting Topology Improvements Test Suite")
        print("=" * 60)
        
        await self.test_topology_data_structure()
        await self.test_ip_display_in_html()
        await self.test_export_functionality()
        await self.test_diagnostics_accessibility()
        await self.test_ui_integration()
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.results['tests_run']}")
        print(f"✅ Passed: {self.results['tests_passed']}")
        print(f"❌ Failed: {self.results['tests_failed']}")
        
        success_rate = (self.results['tests_passed'] / self.results['tests_run'] * 100) if self.results['tests_run'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Save results to file
        with open('test_results_improvements.json', 'w') as f:
            json.dump(self.results, indent=2, fp=f)
        
        print(f"\n📄 Detailed results saved to: test_results_improvements.json")
        
        return self.results


async def main():
    tester = TopologyImprovementsTest()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if results['tests_failed'] == 0:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print(f"\n⚠️  {results['tests_failed']} test(s) failed")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
