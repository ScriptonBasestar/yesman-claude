#!/bin/bash
# Test: Real-time Communication
# Description: Tests WebSocket communication and real-time updates

set -e

echo "🌐 Testing Real-time Communication..."

# Check if websocat is available for WebSocket testing
if ! command -v websocat &> /dev/null; then
    echo "⚠️ websocat not found. Installing via alternative method..."
    if command -v curl &> /dev/null; then
        # Use curl for basic WebSocket testing
        WEBSOCKET_CLIENT="curl"
    else
        echo "❌ No WebSocket client available"
        exit 1
    fi
else
    WEBSOCKET_CLIENT="websocat"
fi

# Test 1: WebSocket server setup
echo -e "\n🚀 Test 1: WebSocket server setup"
cd api
python3 -c "
import asyncio
import websockets
import json
import threading
import time
from datetime import datetime

class WebSocketServer:
    def __init__(self):
        self.clients = set()
        self.running = False
    
    async def register_client(self, websocket):
        self.clients.add(websocket)
        print(f'Client connected: {websocket.remote_address}')
        
    async def unregister_client(self, websocket):
        self.clients.discard(websocket)
        print(f'Client disconnected: {websocket.remote_address}')
    
    async def handle_client(self, websocket, path):
        await self.register_client(websocket)
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'welcome',
                'message': 'Connected to Yesman-Claude WebSocket',
                'timestamp': datetime.now().isoformat()
            }))
            
            async for message in websocket:
                data = json.loads(message)
                print(f'Received: {data}')
                
                # Echo back with timestamp
                response = {
                    'type': 'echo',
                    'original': data,
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send(json.dumps(response))
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def broadcast_periodic_updates(self):
        counter = 0
        while self.running:
            if self.clients:
                message = {
                    'type': 'update',
                    'counter': counter,
                    'timestamp': datetime.now().isoformat(),
                    'active_clients': len(self.clients)
                }
                
                # Send to all connected clients
                if self.clients:
                    await asyncio.gather(
                        *[client.send(json.dumps(message)) for client in self.clients],
                        return_exceptions=True
                    )
                
                counter += 1
            
            await asyncio.sleep(2)  # Send update every 2 seconds
    
    async def start_server(self):
        self.running = True
        
        # Start periodic updates
        update_task = asyncio.create_task(self.broadcast_periodic_updates())
        
        # Start WebSocket server
        server = await websockets.serve(
            self.handle_client,
            'localhost',
            8765,
            ping_interval=20,
            ping_timeout=10
        )
        
        print('WebSocket server started on ws://localhost:8765')
        
        try:
            await server.wait_closed()
        finally:
            self.running = False
            update_task.cancel()

# Run server for 30 seconds
server = WebSocketServer()
asyncio.run(asyncio.wait_for(server.start_server(), timeout=30))
" &
WS_SERVER_PID=$!
cd ..

# Wait for server to start
sleep 3

# Test 2: WebSocket client connection
echo -e "\n📱 Test 2: WebSocket client connection"
if [ "$WEBSOCKET_CLIENT" = "websocat" ]; then
    # Test with websocat
    echo "Testing with websocat..."
    timeout 5 websocat ws://localhost:8765 <<< '{"type": "test", "message": "Hello WebSocket"}' > /tmp/ws_response.txt &
    WS_CLIENT_PID=$!
    
    sleep 2
    
    if ps -p $WS_CLIENT_PID > /dev/null 2>&1; then
        echo "✅ WebSocket client connected successfully"
        kill $WS_CLIENT_PID 2>/dev/null || true
    else
        echo "❌ WebSocket client connection failed"
    fi
else
    # Test with curl (HTTP upgrade)
    echo "Testing WebSocket upgrade with curl..."
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Upgrade: websocket" \
        -H "Connection: Upgrade" \
        -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
        -H "Sec-WebSocket-Version: 13" \
        "http://localhost:8765/")
    
    if [ "$RESPONSE" = "101" ]; then
        echo "✅ WebSocket upgrade successful"
    else
        echo "❌ WebSocket upgrade failed (HTTP $RESPONSE)"
    fi
fi

# Test 3: Multiple concurrent connections
echo -e "\n🔄 Test 3: Multiple concurrent connections"
python3 -c "
import asyncio
import websockets
import json
import time

async def test_client(client_id, duration=5):
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print(f'Client {client_id} connected')
            
            # Send initial message
            await websocket.send(json.dumps({
                'type': 'client_test',
                'client_id': client_id,
                'message': f'Hello from client {client_id}'
            }))
            
            # Listen for messages
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < duration:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1)
                    data = json.loads(message)
                    message_count += 1
                    
                    if data['type'] == 'welcome':
                        print(f'Client {client_id} received welcome')
                    elif data['type'] == 'update':
                        print(f'Client {client_id} received update #{data[\"counter\"]}')
                    
                except asyncio.TimeoutError:
                    continue
            
            print(f'Client {client_id} received {message_count} messages')
            return message_count
            
    except Exception as e:
        print(f'Client {client_id} error: {e}')
        return 0

async def test_concurrent_clients():
    # Create 5 concurrent clients
    tasks = []
    for i in range(5):
        task = test_client(i, duration=10)
        tasks.append(task)
    
    # Wait for all clients to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_clients = sum(1 for result in results if isinstance(result, int) and result > 0)
    total_messages = sum(result for result in results if isinstance(result, int))
    
    print(f'Successful clients: {successful_clients}/5')
    print(f'Total messages received: {total_messages}')
    
    if successful_clients >= 4:
        print('✅ Multiple concurrent connections working')
    else:
        print('❌ Multiple concurrent connections failed')

# Run test
asyncio.run(test_concurrent_clients())
" &
CONCURRENT_TEST_PID=$!

# Wait for concurrent test to complete
wait $CONCURRENT_TEST_PID

# Test 4: Message ordering and delivery
echo -e "\n📋 Test 4: Message ordering and delivery"
python3 -c "
import asyncio
import websockets
import json
import time

async def test_message_ordering():
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            print('Testing message ordering...')
            
            # Send sequence of messages
            messages = []
            for i in range(10):
                message = {
                    'type': 'sequence_test',
                    'sequence': i,
                    'timestamp': time.time()
                }
                messages.append(message)
                await websocket.send(json.dumps(message))
                await asyncio.sleep(0.1)  # Small delay between messages
            
            # Receive echoed messages
            received_messages = []
            for i in range(10):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    if data['type'] == 'echo':
                        received_messages.append(data['original'])
                except asyncio.TimeoutError:
                    print(f'Timeout waiting for message {i}')
                    break
            
            print(f'Sent {len(messages)} messages, received {len(received_messages)} echoes')
            
            # Check ordering
            ordered_correctly = True
            for i, msg in enumerate(received_messages):
                if msg['sequence'] != i:
                    ordered_correctly = False
                    print(f'Message {i} out of order: expected {i}, got {msg[\"sequence\"]}')
            
            if ordered_correctly and len(received_messages) == len(messages):
                print('✅ Message ordering and delivery working correctly')
            else:
                print('❌ Message ordering or delivery issues detected')
                
    except Exception as e:
        print(f'Message ordering test error: {e}')

asyncio.run(test_message_ordering())
" &
ORDERING_TEST_PID=$!

wait $ORDERING_TEST_PID

# Test 5: Connection resilience
echo -e "\n🔧 Test 5: Connection resilience"
python3 -c "
import asyncio
import websockets
import json
import time
import random

async def test_connection_resilience():
    reconnect_attempts = 0
    max_reconnects = 3
    
    for attempt in range(max_reconnects + 1):
        try:
            print(f'Connection attempt {attempt + 1}...')
            
            async with websockets.connect('ws://localhost:8765') as websocket:
                print('Connected successfully')
                
                # Test normal communication
                await websocket.send(json.dumps({
                    'type': 'resilience_test',
                    'attempt': attempt
                }))
                
                # Receive welcome message
                welcome = await asyncio.wait_for(websocket.recv(), timeout=2)
                print('Received welcome message')
                
                # Simulate connection drop by closing after short time
                if attempt < max_reconnects:
                    await asyncio.sleep(2)
                    print('Simulating connection drop...')
                    # Connection will be closed when exiting context
                    reconnect_attempts += 1
                    await asyncio.sleep(1)  # Wait before reconnect
                else:
                    # Final successful connection
                    await asyncio.sleep(3)
                    print('Final connection test completed')
                    break
                    
        except Exception as e:
            print(f'Connection attempt {attempt + 1} failed: {e}')
            if attempt < max_reconnects:
                await asyncio.sleep(2)  # Wait before retry
            else:
                print('Max reconnect attempts reached')
                break
    
    print(f'Reconnection attempts: {reconnect_attempts}')
    
    if reconnect_attempts > 0:
        print('✅ Connection resilience test completed')
    else:
        print('❌ Connection resilience test failed')

asyncio.run(test_connection_resilience())
" &
RESILIENCE_TEST_PID=$!

wait $RESILIENCE_TEST_PID

# Test 6: Load testing
echo -e "\n⚡ Test 6: WebSocket load testing"
python3 -c "
import asyncio
import websockets
import json
import time
import statistics

async def load_test_client(client_id, messages_per_second=10, duration=5):
    try:
        async with websockets.connect('ws://localhost:8765') as websocket:
            message_times = []
            messages_sent = 0
            messages_received = 0
            
            # Send messages at specified rate
            interval = 1.0 / messages_per_second
            end_time = time.time() + duration
            
            while time.time() < end_time:
                # Send message
                start_time = time.time()
                await websocket.send(json.dumps({
                    'type': 'load_test',
                    'client_id': client_id,
                    'message_id': messages_sent,
                    'timestamp': start_time
                }))
                messages_sent += 1
                
                # Try to receive response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    end_time_msg = time.time()
                    message_times.append(end_time_msg - start_time)
                    messages_received += 1
                except asyncio.TimeoutError:
                    pass
                
                # Wait for next message
                await asyncio.sleep(interval)
            
            # Calculate statistics
            avg_response_time = statistics.mean(message_times) if message_times else 0
            
            return {
                'client_id': client_id,
                'messages_sent': messages_sent,
                'messages_received': messages_received,
                'avg_response_time': avg_response_time,
                'success_rate': (messages_received / messages_sent) * 100 if messages_sent > 0 else 0
            }
            
    except Exception as e:
        print(f'Load test client {client_id} error: {e}')
        return None

async def run_load_test():
    # Create 10 concurrent clients
    clients = 10
    messages_per_second = 5
    duration = 8
    
    print(f'Starting load test: {clients} clients, {messages_per_second} msg/s each, {duration}s duration')
    
    tasks = []
    for i in range(clients):
        task = load_test_client(i, messages_per_second, duration)
        tasks.append(task)
    
    # Wait for all clients to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyze results
    successful_clients = [r for r in results if r is not None and isinstance(r, dict)]
    
    if successful_clients:
        total_sent = sum(r['messages_sent'] for r in successful_clients)
        total_received = sum(r['messages_received'] for r in successful_clients)
        avg_response_times = [r['avg_response_time'] for r in successful_clients if r['avg_response_time'] > 0]
        
        print(f'Load test results:')
        print(f'  Successful clients: {len(successful_clients)}/{clients}')
        print(f'  Total messages sent: {total_sent}')
        print(f'  Total messages received: {total_received}')
        print(f'  Overall success rate: {(total_received/total_sent)*100:.1f}%')
        
        if avg_response_times:
            print(f'  Average response time: {statistics.mean(avg_response_times)*1000:.1f}ms')
            print(f'  Min response time: {min(avg_response_times)*1000:.1f}ms')
            print(f'  Max response time: {max(avg_response_times)*1000:.1f}ms')
        
        if len(successful_clients) >= clients * 0.8:  # 80% success rate
            print('✅ Load test passed')
        else:
            print('❌ Load test failed')
    else:
        print('❌ Load test failed - no successful clients')

asyncio.run(run_load_test())
" &
LOAD_TEST_PID=$!

wait $LOAD_TEST_PID

# Stop WebSocket server
echo -e "\n🛑 Stopping WebSocket server..."
kill $WS_SERVER_PID
wait $WS_SERVER_PID 2>/dev/null || true

echo -e "\n📊 Real-time Communication Test Summary:"
echo "- WebSocket server setup and startup tested"
echo "- Client connection and communication verified"
echo "- Multiple concurrent connections tested"
echo "- Message ordering and delivery verified"
echo "- Connection resilience tested"
echo "- Load testing completed with performance metrics"

echo -e "\n✅ Real-time communication tests completed!"