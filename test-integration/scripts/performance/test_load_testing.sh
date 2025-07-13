#!/bin/bash
# Test: Load Testing
# Description: Tests performance under load conditions

set -e

echo "⚡ Testing Performance Under Load..."

# Configuration
MAX_SESSIONS=10
CONCURRENT_OPERATIONS=5
CACHE_TTL=1

# Setup temporary config with shorter cache TTL
cat > /tmp/perf-config.yaml << EOF
logging:
  level: ERROR

cache:
  ttl: $CACHE_TTL
  max_entries: 100

default_choices:
  auto_next: true
EOF

cp /tmp/perf-config.yaml ~/.yesman/yesman.yaml

# Test 1: Session creation load test
echo -e "\n🏗️ Test 1: Creating multiple sessions"
START_TIME=$(date +%s)

for i in $(seq 1 $MAX_SESSIONS); do
    SESSION_NAME="perf-test-$i"
    cat > /tmp/perf-project-$i.yaml << EOF
sessions:
  perf-test-$i:
    session_name: "$SESSION_NAME"
    template: "none"
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["echo 'Session $i created'"]
EOF

    cp /tmp/perf-project-$i.yaml ~/.yesman/projects.yaml
    uv run ./yesman.py setup &

    # Limit concurrent operations
    if [ $((i % CONCURRENT_OPERATIONS)) -eq 0 ]; then
        wait
    fi
done

wait
END_TIME=$(date +%s)
CREATION_TIME=$((END_TIME - START_TIME))

echo "✅ Created $MAX_SESSIONS sessions in ${CREATION_TIME}s"

# Test 2: Concurrent show operations
echo -e "\n👀 Test 2: Concurrent show operations"
START_TIME=$(date +%s%N)

for i in $(seq 1 20); do
    uv run ./yesman.py show > /dev/null &
done

wait
END_TIME=$(date +%s%N)
SHOW_TIME=$((($END_TIME - $START_TIME) / 1000000))

echo "✅ Completed 20 concurrent show operations in ${SHOW_TIME}ms"

# Test 3: Memory usage monitoring
echo -e "\n💾 Test 3: Memory usage monitoring"
MEMORY_BEFORE=$(ps -o rss= -p $$ 2>/dev/null || echo "0")

# Perform intensive operations
for i in $(seq 1 100); do
    uv run ./yesman.py show > /dev/null
done

MEMORY_AFTER=$(ps -o rss= -p $$ 2>/dev/null || echo "0")
MEMORY_DIFF=$((MEMORY_AFTER - MEMORY_BEFORE))

echo "Memory usage: Before: ${MEMORY_BEFORE}KB, After: ${MEMORY_AFTER}KB, Diff: ${MEMORY_DIFF}KB"

if [ $MEMORY_DIFF -lt 50000 ]; then
    echo "✅ Memory usage is acceptable"
else
    echo "⚠️ High memory usage detected"
fi

# Test 4: Cache effectiveness
echo -e "\n🚀 Test 4: Cache effectiveness"
echo "Cache TTL: ${CACHE_TTL}s"

# First run (cache miss)
START_TIME=$(date +%s%N)
uv run ./yesman.py show > /dev/null
END_TIME=$(date +%s%N)
FIRST_RUN=$((($END_TIME - $START_TIME) / 1000000))

# Second run (cache hit)
START_TIME=$(date +%s%N)
uv run ./yesman.py show > /dev/null
END_TIME=$(date +%s%N)
SECOND_RUN=$((($END_TIME - $START_TIME) / 1000000))

# Wait for cache to expire
sleep $((CACHE_TTL + 1))

# Third run (cache expired)
START_TIME=$(date +%s%N)
uv run ./yesman.py show > /dev/null
END_TIME=$(date +%s%N)
THIRD_RUN=$((($END_TIME - $START_TIME) / 1000000))

echo "Cache miss: ${FIRST_RUN}ms, Cache hit: ${SECOND_RUN}ms, Cache expired: ${THIRD_RUN}ms"

if [ $SECOND_RUN -lt $FIRST_RUN ] && [ $THIRD_RUN -gt $SECOND_RUN ]; then
    echo "✅ Cache is working effectively"
else
    echo "⚠️ Cache may not be working as expected"
fi

# Test 5: Bulk teardown performance
echo -e "\n🗑️ Test 5: Bulk teardown performance"
START_TIME=$(date +%s)

# Create a single projects.yaml with all sessions
cat > ~/.yesman/projects.yaml << EOF
sessions:
EOF

for i in $(seq 1 $MAX_SESSIONS); do
    cat >> ~/.yesman/projects.yaml << EOF
  perf-test-$i:
    session_name: "perf-test-$i"
    template: "none"
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["echo 'Session $i'"]
EOF
done

uv run ./yesman.py teardown

END_TIME=$(date +%s)
TEARDOWN_TIME=$((END_TIME - START_TIME))

echo "✅ Tore down $MAX_SESSIONS sessions in ${TEARDOWN_TIME}s"

# Performance summary
echo -e "\n📊 Performance Summary:"
echo "- Session creation: ${CREATION_TIME}s for $MAX_SESSIONS sessions"
echo "- Concurrent operations: ${SHOW_TIME}ms for 20 operations"
echo "- Memory overhead: ${MEMORY_DIFF}KB"
echo "- Cache speedup: $((FIRST_RUN - SECOND_RUN))ms improvement"
echo "- Teardown time: ${TEARDOWN_TIME}s"

echo -e "\n✅ Performance tests completed!"
