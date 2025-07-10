"""Test background tasks and WebSocket updates"""

import asyncio
import websockets
import json
import requests
from datetime import datetime
import time


def check_task_status():
    """Check the status of background tasks via API"""
    response = requests.get("http://localhost:8000/api/tasks/status")
    if response.status_code == 200:
        data = response.json()
        print("\n📊 Background Task Status:")
        print(f"   Running: {data['is_running']}")
        print("\n   Task Details:")
        for task_name, task_info in data['tasks'].items():
            print(f"   - {task_name}:")
            print(f"     Running: {task_info['is_running']}")
            print(f"     Last Run: {task_info['last_run']}")
            print(f"     Errors: {task_info['error_count']}")
            print(f"     Interval: {task_info['interval']}s")
    else:
        print(f"❌ Failed to get task status: {response.status_code}")


async def monitor_updates(duration: int = 60):
    """Monitor WebSocket updates for a specified duration"""
    uri = "ws://localhost:8000/ws/dashboard"
    
    print(f"\n🔌 Connecting to WebSocket for {duration} seconds...")
    
    update_counts = {
        "session_update": 0,
        "health_update": 0,
        "activity_update": 0,
        "initial_data": 0,
        "ping": 0
    }
    
    start_time = time.time()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to dashboard WebSocket")
            
            while time.time() - start_time < duration:
                try:
                    # Set timeout to avoid blocking forever
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    msg_type = data.get('type', 'unknown')
                    update_counts[msg_type] = update_counts.get(msg_type, 0) + 1
                    
                    if msg_type == 'ping':
                        # Respond to ping
                        await websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                    elif msg_type in ['session_update', 'health_update', 'activity_update']:
                        print(f"\n📥 Received {msg_type}:")
                        print(f"   Timestamp: {data.get('timestamp')}")
                        
                        if msg_type == 'session_update':
                            sessions = data.get('data', [])
                            print(f"   Sessions: {len(sessions)}")
                            for session in sessions[:3]:  # Show first 3
                                print(f"     - {session.get('session_name')}: {session.get('status')}")
                        
                        elif msg_type == 'health_update':
                            health = data.get('data', {})
                            print(f"   Overall Score: {health.get('overall_score')}")
                            
                        elif msg_type == 'activity_update':
                            activity = data.get('data', {})
                            print(f"   Active Days: {activity.get('active_days')}")
                            print(f"   Max Activity: {activity.get('max_activity')}")
                    
                except asyncio.TimeoutError:
                    # No message received in 1 second, continue
                    pass
                    
            print(f"\n📊 Update Summary ({duration}s):")
            for update_type, count in update_counts.items():
                if count > 0:
                    print(f"   {update_type}: {count}")
                    
    except Exception as e:
        print(f"❌ WebSocket error: {str(e)}")


async def trigger_session_change():
    """Simulate a session change to trigger updates"""
    print("\n🔄 Simulating session change...")
    
    # This would normally be done by creating/stopping a tmux session
    # For testing, we'll just wait and let the monitor detect any changes
    
    print("   Waiting for background tasks to detect changes...")
    await asyncio.sleep(5)


async def main():
    """Run background task tests"""
    print("🚀 Testing Background Tasks and Real-time Updates")
    print("=" * 50)
    
    # Check initial task status
    check_task_status()
    
    # Monitor updates for 60 seconds
    await monitor_updates(60)
    
    # Check final task status
    print("\n" + "=" * 50)
    check_task_status()
    
    print("\n✅ Test completed!")


if __name__ == "__main__":
    print("🔧 Background Task Test")
    print("Make sure the API server is running at http://localhost:8000")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")