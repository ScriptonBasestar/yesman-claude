# Copyright notice.

import asyncio
import contextlib
import json
from datetime import UTC, datetime

import websockets

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""WebSocket connection test script."""


async def test_websocket_connection(uri: str, channel: str) -> None:
    """Test WebSocket connection to a specific channel."""
    try:
        async with websockets.connect(uri) as websocket:
            # Create a task to receive messages
            async def receive_messages() -> None:
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)

                        if data.get("type") == "ping":
                            # Respond to ping
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "pong",
                                        "timestamp": datetime.now(UTC).isoformat(),
                                    }
                                )
                            )

                        elif data.get("type") == "initial_data":
                            pass

                    except websockets.exceptions.ConnectionClosed:
                        break
                    except Exception:
                        break

            # Start receiving messages
            receive_task = asyncio.create_task(receive_messages())

            # Test different message types
            if channel == "dashboard":
                # Test subscribe message
                await asyncio.sleep(1)
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
                await websocket.send(
                    json.dumps(
                        {
                            "type": "refresh",
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )
                )

            # Keep connection alive for testing
            await asyncio.sleep(10)

            # Cancel receive task
            receive_task.cancel()

    except websockets.exceptions.WebSocketException:
        pass
    except Exception:
        pass


async def test_multiple_connections() -> None:
    """Test multiple simultaneous WebSocket connections."""
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


async def stress_test_connections(num_connections: int = 10) -> None:
    """Stress test with multiple dashboard connections."""
    uri = "ws://localhost:8000/ws/dashboard"
    connections = []

    try:
        # Create multiple connections
        for i in range(num_connections):
            ws = await websockets.connect(uri)
            connections.append(ws)

        # Keep connections alive for a bit
        await asyncio.sleep(5)

        # Close all connections
        for i, ws in enumerate(connections):
            await ws.close()

    except Exception:
        pass
    finally:
        # Ensure all connections are closed
        for ws in connections:
            if not ws.closed:
                await ws.close()


async def main() -> None:
    """Run all WebSocket tests."""
    # Test 1: Individual channel connections
    await test_multiple_connections()

    # Small delay between tests
    await asyncio.sleep(2)

    # Test 2: Stress test
    await stress_test_connections(20)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
