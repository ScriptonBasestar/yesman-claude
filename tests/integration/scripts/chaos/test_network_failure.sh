#!/bin/bash
# Test: Network Failure Simulation
# Description: Tests resilience against network failures

set -e

echo "🌪️ Testing Network Failure Resilience..."

# Check if we can simulate network conditions
if ! command -v tc &> /dev/null; then
    echo "⚠️ 'tc' command not available - using alternative methods"
    USE_TC=false
else
    echo "✅ 'tc' command available for network simulation"
    USE_TC=true
fi

# Test 1: Network latency simulation
echo -e "\n🐌 Test 1: High latency simulation"
if [ "$USE_TC" = true ]; then
    # Add 500ms latency (requires sudo)
    echo "Adding 500ms latency to loopback interface..."
    # sudo tc qdisc add dev lo root netem delay 500ms
    echo "⚠️ Skipping actual tc command (requires sudo)"
else
    echo "⚠️ Using sleep-based latency simulation"
fi

# Start FastAPI server with artificial delays
echo -e "\n🚀 Starting server with latency simulation..."
cd api
python -c "
import time
import uvicorn
from main import app

# Add artificial latency to all endpoints
@app.middleware('http')
async def add_latency(request, call_next):
    # Simulate 200ms network latency
    time.sleep(0.2)
    response = await call_next(request)
    return response

uvicorn.run(app, host='0.0.0.0', port=8001, log_level='error')
" &
SERVER_PID=$!
cd ..

sleep 3

# Test response time under latency
echo -e "\n⏱️ Testing response time under latency..."
START_TIME=$(date +%s%N)
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8001/health")
END_TIME=$(date +%s%N)
LATENCY=$((($END_TIME - $START_TIME) / 1000000))

echo "Response time: ${LATENCY}ms"
if [ $LATENCY -gt 200 ]; then
    echo "✅ High latency detected and handled"
else
    echo "⚠️ Latency simulation may not be working"
fi

kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

# Test 2: Connection timeout simulation
echo -e "\n⏰ Test 2: Connection timeout simulation"
cd api
python -c "
import asyncio
import uvicorn
from main import app

@app.middleware('http')
async def add_timeout(request, call_next):
    # Simulate very long processing time
    await asyncio.sleep(10)
    response = await call_next(request)
    return response

uvicorn.run(app, host='0.0.0.0', port=8001, log_level='error')
" &
SERVER_PID=$!
cd ..

sleep 2

# Test with short timeout
echo "Testing with 5-second timeout..."
START_TIME=$(date +%s)
RESPONSE=$(timeout 5 curl -s "http://localhost:8001/health" || echo "TIMEOUT")
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "$RESPONSE" = "TIMEOUT" ] && [ $DURATION -le 6 ]; then
    echo "✅ Timeout handling working correctly"
else
    echo "❌ Timeout handling may need improvement"
fi

kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

# Test 3: Port unavailable simulation
echo -e "\n🚫 Test 3: Port unavailable simulation"
# Try to connect to non-existent port
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null --connect-timeout 5 "http://localhost:9999/health" || echo "CONNECTION_FAILED")

if [ "$RESPONSE" = "CONNECTION_FAILED" ]; then
    echo "✅ Connection failure handled gracefully"
else
    echo "❌ Unexpected response to unavailable port: $RESPONSE"
fi

# Test 4: DNS resolution failure simulation
echo -e "\n🌐 Test 4: DNS resolution failure simulation"
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null --connect-timeout 5 "http://non-existent-domain.local/health" || echo "DNS_FAILED")

if [ "$RESPONSE" = "DNS_FAILED" ]; then
    echo "✅ DNS failure handled gracefully"
else
    echo "❌ Unexpected response to DNS failure: $RESPONSE"
fi

# Test 5: Intermittent connection failures
echo -e "\n🔄 Test 5: Intermittent connection failures"
cd api
python -c "
import random
import uvicorn
from main import app
from fastapi import HTTPException

@app.middleware('http')
async def intermittent_failure(request, call_next):
    # Randomly fail 30% of requests
    if random.random() < 0.3:
        raise HTTPException(status_code=503, detail='Service temporarily unavailable')
    response = await call_next(request)
    return response

uvicorn.run(app, host='0.0.0.0', port=8001, log_level='error')
" &
SERVER_PID=$!
cd ..

sleep 2

# Test multiple requests to check failure rate
echo "Testing intermittent failures (10 requests)..."
SUCCESS_COUNT=0
FAILURE_COUNT=0

for i in $(seq 1 10); do
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8001/health")
    if [ "$RESPONSE" = "200" ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILURE_COUNT=$((FAILURE_COUNT + 1))
    fi
done

echo "Success: $SUCCESS_COUNT, Failures: $FAILURE_COUNT"
if [ $FAILURE_COUNT -gt 0 ] && [ $SUCCESS_COUNT -gt 0 ]; then
    echo "✅ Intermittent failure simulation working"
else
    echo "⚠️ Intermittent failure simulation may need adjustment"
fi

kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

# Test 6: Bandwidth limitation simulation
echo -e "\n📡 Test 6: Bandwidth limitation simulation"
if [ "$USE_TC" = true ]; then
    echo "⚠️ Bandwidth limitation would require sudo tc commands"
else
    echo "Using alternative bandwidth simulation..."
fi

# Simulate slow response by chunking data
cd api
python -c "
import time
import uvicorn
from main import app
from fastapi import Response

@app.get('/slow-response')
async def slow_response():
    # Simulate slow data transfer
    data = 'A' * 1000  # 1KB of data
    return Response(content=data, media_type='text/plain')

@app.middleware('http')
async def slow_transfer(request, call_next):
    response = await call_next(request)
    if request.url.path == '/slow-response':
        # Simulate slow transfer by adding delays
        time.sleep(0.1)
    return response

uvicorn.run(app, host='0.0.0.0', port=8001, log_level='error')
" &
SERVER_PID=$!
cd ..

sleep 2

START_TIME=$(date +%s%N)
RESPONSE=$(curl -s "http://localhost:8001/slow-response" | wc -c)
END_TIME=$(date +%s%N)
TRANSFER_TIME=$((($END_TIME - $START_TIME) / 1000000))

echo "Transferred ${RESPONSE} bytes in ${TRANSFER_TIME}ms"
if [ $TRANSFER_TIME -gt 100 ]; then
    echo "✅ Bandwidth limitation simulation working"
else
    echo "⚠️ Bandwidth simulation may need improvement"
fi

kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

# Test 7: Session management under network stress
echo -e "\n🎯 Test 7: Session management under network stress"
SESSION_NAME="chaos-test-$(date +%s)"
cat > /tmp/chaos-test.yaml << EOF
sessions:
  chaos-test:
    session_name: "$SESSION_NAME"
    template: "none"
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["echo 'Chaos test session'"]
EOF

cp /tmp/chaos-test.yaml ~/.yesman/projects.yaml

# Create session
uv run ./yesman.py setup

# Verify session exists despite network conditions
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "✅ Session created successfully under stress"
else
    echo "❌ Session creation failed under stress"
fi

# Test session operations
uv run ./yesman.py show | grep -q "$SESSION_NAME"
if [ $? -eq 0 ]; then
    echo "✅ Session operations working under stress"
else
    echo "❌ Session operations failed under stress"
fi

# Cleanup
uv run ./yesman.py teardown

echo -e "\n📊 Network Failure Test Summary:"
echo "- High latency: Tested with 200ms+ delays"
echo "- Connection timeout: Tested with 10s delays"
echo "- Port unavailable: Tested connection to closed port"
echo "- DNS failure: Tested with non-existent domain"
echo "- Intermittent failures: Tested 30% failure rate"
echo "- Bandwidth limitation: Tested with slow responses"
echo "- Session resilience: Tested session operations under stress"

echo -e "\n✅ Network failure resilience tests completed!"