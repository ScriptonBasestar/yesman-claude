# Copyright notice.

import asyncio
import contextlib
import json
import time
from datetime import UTC, datetime
import requests
import websockets

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test background tasks and WebSocket updates."""




def check_task_status() -> None:
    """Check the status of background tasks via API.

    """
    response = requests.get("http://localhost:8000/api/tasks/status", timeout=5)
    if response.status_code == 200:
        data = response.json()
        for task_info in data["tasks"].values():
            pass
    else:
        pass


async def monitor_updates(duration: int = 60) -> None:
    """Monitor WebSocket updates for a specified duration."""
    uri = "ws://localhost:8000/ws/dashboard"

    update_counts = {
        "session_update": 0,
        "health_update": 0,
        "activity_update": 0,
        "initial_data": 0,
        "ping": 0,
    }

    start_time = time.time()

    try:
        async with websockets.connect(uri) as websocket:
            while time.time() - start_time < duration:
                try:
                    # Set timeout to avoid blocking forever
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)

                    msg_type = data.get("type", "unknown")
                    update_counts[msg_type] = update_counts.get(msg_type, 0) + 1

                    if msg_type == "ping":
                        # Respond to ping
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "pong",
                                    "timestamp": datetime.now(UTC).isoformat(),
                                }
                            )
                        )

                    elif msg_type in {
                        "session_update",
                        "health_update",
                        "activity_update",
                    }:
                        if msg_type == "session_update":
                            sessions = data.get("data", [])
                            for session in sessions[:3]:  # Show first 3
                                pass

                        elif msg_type in {"health_update", "activity_update"}:
                            data.get("data", {})

                except TimeoutError:
                    # No message received in 1 second, continue
                    pass

            for count in update_counts.values():
                if count > 0:
                    pass

    except Exception:
        pass


async def trigger_session_change() -> None:
    """Simulate a session change to trigger updates."""
    # This would normally be done by creating/stopping a tmux session
    # For testing, we'll just wait and let the monitor detect any changes

    await asyncio.sleep(5)


async def main() -> None:
    """Run background task tests."""
    # Check initial task status
    check_task_status()

    # Monitor updates for 60 seconds
    await monitor_updates(60)

    # Check final task status
    check_task_status()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
