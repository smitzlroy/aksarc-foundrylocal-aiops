"""
AKS Arc diagnostic service.

Integrates with Microsoft's Support.AksArc PowerShell module for
diagnostic checks and remediation.
"""

import asyncio
import json
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)


class AksArcDiagnostics:
    """Service for running AKS Arc diagnostics."""
    
    def __init__(self):
        """Initialize diagnostic service."""
        self._ps_available = False
        self._module_installed = False
    
    async def check_prerequisites(self) -> Dict:
        """Check if PowerShell and Support.AksArc module are available."""
        try:
            # Check if PowerShell is available
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', 'Get-Module -ListAvailable -Name Support.AksArc',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            self._ps_available = True
            self._module_installed = b'Support.AksArc' in stdout
            
            return {
                'powershell_available': self._ps_available,
                'module_installed': self._module_installed,
                'support_module_available': self._module_installed,
                'available': self._module_installed
            }
            
        except Exception as e:
            logger.error("failed_to_check_prerequisites", error=str(e))
            return {
                'powershell_available': False,
                'module_installed': False,
                'support_module_available': False,
                'available': False,
                'error': str(e)
            }
    
    async def install_support_module(self) -> Dict:
        """Install Support.AksArc PowerShell module."""
        try:
            ps_script = """
            Install-Module -Name Support.AksArc -Force -AllowClobber
            Import-Module Support.AksArc -Force
            Write-Output "Module installed successfully"
            """
            
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self._module_installed = True
                return {
                    'success': True,
                    'message': 'Support.AksArc module installed successfully',
                    'output': stdout.decode()
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to install: {stderr.decode()}',
                    'error': stderr.decode()
                }
                
        except Exception as e:
            logger.error("failed_to_install_module", error=str(e))
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    async def run_diagnostic_checks(self) -> List[Dict]:
        """Run Test-SupportAksArcKnownIssues diagnostic checks."""
        if not self._module_installed:
            prereq = await self.check_prerequisites()
            if not prereq['available']:
                return [{
                    'test_name': 'Prerequisites Check',
                    'status': 'Failed',
                    'message': 'Support.AksArc module not installed. Install it first.',
                    'recommendation': 'Run the "Install Module" action to install Support.AksArc'
                }]
        
        try:
            ps_script = """
            Import-Module Support.AksArc -Force
            $results = Test-SupportAksArcKnownIssues
            $jsonResults = $results | ForEach-Object {
                [PSCustomObject]@{
                    TestName = $_.'Test Name'
                    Status = $_.Status
                    Message = $_.Message
                }
            }
            $jsonResults | ConvertTo-Json -Depth 10
            """
            
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and stdout:
                try:
                    results = json.loads(stdout.decode())
                    # Handle single result (not array)
                    if isinstance(results, dict):
                        results = [results]
                    return self._parse_diagnostic_results(results)
                except json.JSONDecodeError:
                    logger.error("json_decode_error", stdout=stdout.decode())
                    return [{
                        'test_name': 'Diagnostic Execution',
                        'status': 'Failed',
                        'message': 'Failed to parse diagnostic results',
                        'recommendation': 'Check PowerShell output format'
                    }]
            else:
                error_msg = stderr.decode() if stderr else 'Unknown error'
                logger.error("diagnostic_check_failed", stderr=error_msg)
                return [{
                    'test_name': 'Diagnostic Execution',
                    'status': 'Failed',
                    'message': f'Failed to run diagnostics: {error_msg}',
                    'recommendation': 'Ensure you have proper permissions and are running on an AKS Arc node'
                }]
                
        except Exception as e:
            logger.error("failed_to_run_diagnostics", error=str(e))
            return [{
                'test_name': 'Diagnostic Execution',
                'status': 'Error',
                'message': f'Exception: {str(e)}',
                'recommendation': 'Check error logs'
            }]
    
    def _parse_diagnostic_results(self, raw_results: List[Dict]) -> List[Dict]:
        """Parse PowerShell diagnostic results into standardized format."""
        parsed = []
        
        for item in raw_results:
            test_name = item.get('TestName', 'Unknown')
            status = item.get('Status', 'Unknown')
            message = item.get('Message', '')
            
            parsed.append({
                'test_name': test_name,
                'status': status,
                'message': message,
                'recommendation': self._get_recommendation(test_name, status)
            })
        
        return parsed
    
    def _get_recommendation(self, test_name: str, status: str) -> str:
        """Get recommendation based on test name and status."""
        if status == 'Passed':
            return 'No action needed'
        
        recommendations = {
            'Validate MOC is on Latest Patch Version': 
                'Update MOC to the latest version using Update-Module or run Invoke-SupportAksArcRemediation',
            'Validate Failover Cluster Service Responsiveness':
                'Check cluster health with Get-ClusterResource and restart the service if needed',
            'Validate MOC Cloud Agent Running':
                'Restart MOC Cloud Agent service or run Invoke-SupportAksArcRemediation',
            'Validate Expired Certificates':
                'Renew certificates using the certificate renewal cmdlet',
            'Validate Missing MOC Cloud Agents':
                'Reinstall MOC cloud agents on affected nodes',
            'Validate Missing MOC Node Agents':
                'Reinstall MOC node agents on affected nodes',
            'Validate MOC Nodes Not Active':
                'Check node status and bring nodes back to active state',
            'Validate Windows Event Log Running':
                'Start the Windows Event Log service',
        }
        
        return recommendations.get(test_name, 'Check AKS Arc documentation for resolution steps at https://learn.microsoft.com/azure/aks/aksarc/aks-troubleshoot')
    
    async def run_remediation(self) -> Dict:
        """Run Invoke-SupportAksArcRemediation to fix common issues."""
        if not self._module_installed:
            prereq = await self.check_prerequisites()
            if not prereq['available']:
                return {
                    'success': False,
                    'message': 'Support.AksArc module not installed'
                }
        
        try:
            ps_script = """
            Import-Module Support.AksArc -Force
            Invoke-SupportAksArcRemediation -Verbose
            """
            
            result = await asyncio.create_subprocess_exec(
                'powershell', '-Command', ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            return {
                'success': result.returncode == 0,
                'message': 'Remediation completed successfully' if result.returncode == 0 else 'Remediation failed',
                'output': stdout.decode() if stdout else '',
                'error': stderr.decode() if stderr else ''
            }
            
        except Exception as e:
            logger.error("failed_to_run_remediation", error=str(e))
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
