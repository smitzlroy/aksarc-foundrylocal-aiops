"""Quick test script for Kubernetes connection."""

import asyncio
import os
import sys
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

# Also ensure we're in the right directory for .env
os.chdir(Path(__file__).parent / "backend")

# Import after path is set
if True:  # Hack to avoid issues
    from core.exceptions import KubernetesConnectionError
    from services.kubernetes import KubernetesClient


async def main():
    """Test Kubernetes connection and cluster status."""
    client = KubernetesClient()
    
    print("🔌 Connecting to Kubernetes cluster...")
    try:
        await client.connect()
        print("✅ Connected successfully!\n")
        
        print("📊 Fetching cluster status...")
        status = await client.get_cluster_status()
        
        print(f"📦 Found {len(status.pods)} pods:")
        for pod in status.pods[:10]:  # Show first 10
            print(f"  • {pod.namespace}/{pod.name} - {pod.phase.value} ({pod.ready}/{pod.total} ready)")
        
        print(f"\n📢 Found {len(status.events)} recent events:")
        for event in status.events[:5]:  # Show first 5
            print(f"  • [{event.type}] {event.reason}: {event.message[:80]}")
        
        await client.disconnect()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
