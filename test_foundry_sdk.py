"""Test Foundry SDK integration."""

import asyncio
import sys
sys.path.insert(0, 'c:/AI/aksarc-foundrylocal-aiops/backend')

from src.services.foundry_manager import get_foundry_manager


async def test_status():
    """Test getting status."""
    print("\n🔍 Testing Foundry SDK Status...")
    print("=" * 50)
    
    manager = get_foundry_manager()
    status = await manager.get_status()
    
    print(f"\n✅ Running: {status['running']}")
    print(f"✅ Installed: {status['installed']}")
    print(f"📦 Message: {status['message']}")
    
    if status.get('available_models'):
        downloaded = [m for m in status['available_models'] if m['downloaded']]
        total = len(status['available_models'])
        
        print(f"\n📊 Models: {len(downloaded)} downloaded out of {total} total")
        print("\n🔽 Downloaded Models:")
        for model in downloaded[:5]:
            print(f"  • {model['name']} ({model['size']})")
    
    return status


async def test_start(model_name="qwen2.5-0.5b"):
    """Test starting a model."""
    print(f"\n🚀 Testing Model Start: {model_name}...")
    print("=" * 50)
    
    manager = get_foundry_manager()
    result = await manager.start_model(model_name)
    
    if result['success']:
        print(f"\n✅ SUCCESS: {result['message']}")
        print(f"🌐 Endpoint: {result.get('endpoint')}")
        print(f"🤖 Model: {result.get('model')}")
        
        # Test query
        print(f"\n💬 Testing Query...")
        try:
            response = await manager.query_model("What is Kubernetes?")
            print(f"✅ Response: {response[:200]}...")
        except Exception as e:
            print(f"❌ Query Error: {e}")
        
    else:
        print(f"\n❌ FAILED: {result['message']}")
    
    return result


async def main():
    """Main test function."""
    print("\n" + "=" * 50)
    print("🧪 Foundry SDK Integration Test")
    print("=" * 50)
    
    # Test 1: Status
    status = await test_status()
    
    # Test 2: Start model (optional - only if user wants)
    # Uncomment to test starting:
    # if not status['running']:
    #     await test_start("qwen2.5-0.5b")
    
    print("\n" + "=" * 50)
    print("✅ Test Complete!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
