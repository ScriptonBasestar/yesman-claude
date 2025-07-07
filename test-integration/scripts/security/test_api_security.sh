#!/bin/bash
# Test: API Security
# Description: Tests API security and authentication

set -e

echo "🔒 Testing API Security..."

# Start FastAPI server in background
echo -e "\n🚀 Starting FastAPI server..."
cd api
python -m uvicorn main:app --host 0.0.0.0 --port 8001 &
SERVER_PID=$!
cd ..

# Wait for server to start
sleep 3

# Test 1: Basic endpoint accessibility
echo -e "\n📡 Test 1: Testing basic endpoint accessibility"
if curl -s http://localhost:8001/health | grep -q "ok"; then
    echo "✅ Health endpoint accessible"
else
    echo "❌ Health endpoint not accessible"
    kill $SERVER_PID
    exit 1
fi

# Test 2: Path traversal attack attempts
echo -e "\n🎯 Test 2: Path traversal attack attempts"
ATTACK_PATHS=(
    "../../etc/passwd"
    "..\\..\\windows\\system32\\config\\sam"
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd"
    "....//....//etc/passwd"
)

for path in "${ATTACK_PATHS[@]}"; do
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8001/sessions/$path/setup")
    if [ "$RESPONSE" = "404" ] || [ "$RESPONSE" = "400" ]; then
        echo "✅ Path traversal blocked: $path"
    else
        echo "❌ Path traversal not blocked: $path (HTTP $RESPONSE)"
    fi
done

# Test 3: SQL injection attempts
echo -e "\n💉 Test 3: SQL injection attempts"
SQL_PAYLOADS=(
    "'; DROP TABLE sessions; --"
    "1' OR '1'='1"
    "'; SELECT * FROM information_schema.tables; --"
    "1; DELETE FROM users; --"
)

for payload in "${SQL_PAYLOADS[@]}"; do
    ENCODED_PAYLOAD=$(echo -n "$payload" | python3 -c "import urllib.parse; print(urllib.parse.quote(input()))")
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8001/sessions/$ENCODED_PAYLOAD/setup")
    if [ "$RESPONSE" = "404" ] || [ "$RESPONSE" = "400" ] || [ "$RESPONSE" = "422" ]; then
        echo "✅ SQL injection blocked: ${payload:0:20}..."
    else
        echo "❌ SQL injection not blocked: ${payload:0:20}... (HTTP $RESPONSE)"
    fi
done

# Test 4: XSS attempt
echo -e "\n🕷️ Test 4: XSS attempts"
XSS_PAYLOADS=(
    "<script>alert('xss')</script>"
    "javascript:alert('xss')"
    "<img src=x onerror=alert('xss')>"
    "';alert('xss');//"
)

for payload in "${XSS_PAYLOADS[@]}"; do
    ENCODED_PAYLOAD=$(echo -n "$payload" | python3 -c "import urllib.parse; print(urllib.parse.quote(input()))")
    RESPONSE=$(curl -s "http://localhost:8001/sessions/$ENCODED_PAYLOAD/status" | grep -o "<script>" || echo "")
    if [ -z "$RESPONSE" ]; then
        echo "✅ XSS blocked: ${payload:0:20}..."
    else
        echo "❌ XSS not blocked: ${payload:0:20}..."
    fi
done

# Test 5: Rate limiting (if implemented)
echo -e "\n🚦 Test 5: Rate limiting test"
RATE_LIMIT_RESPONSES=()
for i in $(seq 1 20); do
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8001/health")
    RATE_LIMIT_RESPONSES+=("$RESPONSE")
done

# Check if any requests were rate limited (429 status)
if echo "${RATE_LIMIT_RESPONSES[@]}" | grep -q "429"; then
    echo "✅ Rate limiting detected"
else
    echo "⚠️ Rate limiting not detected (may not be implemented)"
fi

# Test 6: Invalid HTTP methods
echo -e "\n🔧 Test 6: Invalid HTTP methods"
INVALID_METHODS=("DELETE" "PATCH" "PUT")

for method in "${INVALID_METHODS[@]}"; do
    RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X "$method" "http://localhost:8001/sessions/test")
    if [ "$RESPONSE" = "405" ]; then
        echo "✅ Invalid method $method properly rejected"
    else
        echo "❌ Invalid method $method not properly rejected (HTTP $RESPONSE)"
    fi
done

# Test 7: Large payload test
echo -e "\n📦 Test 7: Large payload handling"
LARGE_PAYLOAD=$(python3 -c "print('A' * 10000)")
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST -H "Content-Type: application/json" -d "{\"data\":\"$LARGE_PAYLOAD\"}" "http://localhost:8001/sessions/test/setup")

if [ "$RESPONSE" = "413" ] || [ "$RESPONSE" = "400" ]; then
    echo "✅ Large payload properly rejected"
else
    echo "⚠️ Large payload handling may need review (HTTP $RESPONSE)"
fi

# Test 8: Content-Type validation
echo -e "\n📋 Test 8: Content-Type validation"
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST -H "Content-Type: text/plain" -d "malicious data" "http://localhost:8001/sessions/test/setup")

if [ "$RESPONSE" = "415" ] || [ "$RESPONSE" = "400" ]; then
    echo "✅ Invalid Content-Type rejected"
else
    echo "⚠️ Content-Type validation may need improvement (HTTP $RESPONSE)"
fi

# Test 9: Session isolation
echo -e "\n🏠 Test 9: Session isolation test"
# Create test session
SESSION_NAME="security-test-$(date +%s)"
cat > /tmp/security-test.yaml << EOF
sessions:
  security-test:
    session_name: "$SESSION_NAME"
    template: "none"
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["echo 'Security test session'"]
EOF

cp /tmp/security-test.yaml ~/.yesman/projects.yaml
uv run ./yesman.py setup

# Try to access other sessions
RESPONSE=$(curl -s "http://localhost:8001/sessions/non-existent/status")
if echo "$RESPONSE" | grep -q "error\|not found"; then
    echo "✅ Session isolation working"
else
    echo "❌ Session isolation may be compromised"
fi

# Cleanup
uv run ./yesman.py teardown

# Test 10: Header injection
echo -e "\n📤 Test 10: Header injection test"
RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -H "X-Forwarded-For: 127.0.0.1%0d%0aSet-Cookie: malicious=true" "http://localhost:8001/health")

if [ "$RESPONSE" = "200" ]; then
    echo "✅ Header injection test passed"
else
    echo "⚠️ Header injection handling may need review"
fi

# Stop server
echo -e "\n🛑 Stopping test server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true

echo -e "\n✅ API security tests completed!"