"""WebSocket connection test script"""

import asyncio
import json
from datetime import datetime

import websockets


async def test_websocket_connection(uri: str, channel: str):
    """Test WebSocket connection to a specific channel"""
    print(f"\n🔌 Connecting to {uri} (channel: {channel})...")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to {channel} channel")

            # Create a task to receive messages
            async def receive_messages():
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        print(f"\n📥 Received ({channel}):")
                        print(f"   Type: {data.get('type')}")
                        print(f"   Timestamp: {data.get('timestamp')}")

                        if data.get("type") == "ping":
                            # Respond to ping
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "pong",
                                        "timestamp": datetime.now().isoformat(),
                                    }
                                )
                            )
                            print("   → Sent pong response")

                        elif data.get("type") == "initial_data":
                            print(f"   Data keys: {list(data.get('data', {}).keys())}")

                    except websockets.exceptions.ConnectionClosed:
                        print(f"\n❌ Connection closed for {channel}")
                        break
                    except Exception as e:
                        print(f"\n❌ Error receiving message: {str(e)}")
                        break

            # Start receiving messages
            receive_task = asyncio.create_task(receive_messages())

            # Test different message types
            if channel == "dashboard":
                # Test subscribe message
                await asyncio.sleep(1)
                print("\n📤 Sending subscribe message...")
                await websocket.send(
                    json.dumps(
                        {
                            "type": "subscribe",
                            "channels": ["sessions", "health"],
                        }
                    )
                )

                # Test unsubscribe message
                await asyncio.sleep(2)
                print("\n📤 Sending unsubscribe message...")
                await websocket.send(
                    json.dumps(
                        {
                            "type": "unsubscribe",
                            "channels": ["health"],
                        }
                    )
                )

            else:
                # Test refresh message for specific channels
                await asyncio.sleep(1)
                print("\n📤 Sending refresh request...")
                await websocket.send(
                    json.dumps(
                        {
                            "type": "refresh",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                )

            # Keep connection alive for testing
            await asyncio.sleep(10)

            # Cancel receive task
            receive_task.cancel()

            print(f"\n👋 Closing {channel} connection...")

    except websockets.exceptions.WebSocketException as e:
        print(f"\n❌ WebSocket error: {str(e)}")
    except Exception as e:
        print(f"\n❌ Connection error: {str(e)}")


async def test_multiple_connections():
    """Test multiple simultaneous WebSocket connections"""
    base_url = "ws://localhost:8000/ws"

    channels = [
        ("dashboard", f"{base_url}/dashboard"),
        ("sessions", f"{base_url}/sessions"),
        ("health", f"{base_url}/health"),
        ("activity", f"{base_url}/activity"),
    ]

    # Create tasks for all connections
    tasks = []
    for channel, uri in channels:
        task = asyncio.create_task(test_websocket_connection(uri, channel))
        tasks.append(task)

    # Wait for all connections to complete
    await asyncio.gather(*tasks, return_exceptions=True)


async def stress_test_connections(num_connections: int = 10):
    """Stress test with multiple dashboard connections"""
    print(f"\n🔥 Stress testing with {num_connections} connections...")

    uri = "ws://localhost:8000/ws/dashboard"
    connections = []

    try:
        # Create multiple connections
        for i in range(num_connections):
            ws = await websockets.connect(uri)
            connections.append(ws)
            print(f"   Connected client {i + 1}/{num_connections}")

        print(f"\n✅ Successfully created {num_connections} connections")

        # Keep connections alive for a bit
        await asyncio.sleep(5)

        # Close all connections
        for i, ws in enumerate(connections):
            await ws.close()
            print(f"   Closed client {i + 1}/{num_connections}")

    except Exception as e:
        print(f"\n❌ Stress test error: {str(e)}")
    finally:
        # Ensure all connections are closed
        for ws in connections:
            if not ws.closed:
                await ws.close()


async def main():
    """Run all WebSocket tests"""
    print("🚀 Starting WebSocket tests...")
    print("=" * 50)

    # Test 1: Individual channel connections
    print("\n📋 Test 1: Testing individual channel connections")
    await test_multiple_connections()

    # Small delay between tests
    await asyncio.sleep(2)

    # Test 2: Stress test
    print("\n📋 Test 2: Stress testing connections")
    await stress_test_connections(20)

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    print("🔧 WebSocket Test Client")
    print("Make sure the API server is running at http://localhost:8000")
    print("-" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
