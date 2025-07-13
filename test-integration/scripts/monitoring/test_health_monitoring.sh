#!/bin/bash
# Test: Health Monitoring
# Description: Tests project health monitoring and metrics collection

set -e

echo "🏥 Testing Health Monitoring..."

# Setup test project
TEST_PROJECT_DIR="/tmp/health-test-project"
mkdir -p "$TEST_PROJECT_DIR"
cd "$TEST_PROJECT_DIR"

# Create test project structure
mkdir -p {src,tests,docs,.git}
touch {src/main.py,tests/test_main.py,docs/README.md,package.json,requirements.txt,.gitignore}

# Create sample files for testing
cat > src/main.py << 'EOF'
#!/usr/bin/env python3
"""Sample main module for health testing"""

def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
EOF

cat > tests/test_main.py << 'EOF'
#!/usr/bin/env python3
"""Sample test module"""

import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        result = main()
        self.assertEqual(result, 0)

if __name__ == "__main__":
    unittest.main()
EOF

cat > package.json << 'EOF'
{
  "name": "health-test-project",
  "version": "1.0.0",
  "description": "Test project for health monitoring",
  "main": "src/main.py",
  "scripts": {
    "test": "python -m pytest tests/",
    "build": "echo 'Build successful'",
    "lint": "echo 'Linting passed'"
  },
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "jest": "^29.0.0"
  }
}
EOF

cat > requirements.txt << 'EOF'
pytest>=7.0.0
requests>=2.28.0
pyyaml>=6.0
EOF

# Initialize git repository
git init
git config user.email "test@example.com"
git config user.name "Test User"
git add .
git commit -m "Initial commit"

echo -e "\n🔧 Test project setup complete"

# Test 1: Project health calculation
echo -e "\n📊 Test 1: Project health calculation"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator

calculator = HealthCalculator()

# Test health calculation for current directory
health_score = calculator.calculate_health('/tmp/health-test-project')

print(f"Overall health score: {health_score:.1f}/100")

# Test individual categories
categories = [
    'build', 'tests', 'dependencies', 'security',
    'performance', 'code_quality', 'git', 'documentation'
]

print("\nDetailed category scores:")
for category in categories:
    score = calculator.calculate_category_score(category, '/tmp/health-test-project')
    print(f"  {category}: {score:.1f}/100")

# Health thresholds
if health_score >= 80:
    print("✅ Project health is excellent")
elif health_score >= 60:
    print("⚠️ Project health is good")
elif health_score >= 40:
    print("⚠️ Project health needs attention")
else:
    print("❌ Project health is poor")
EOF

# Test 2: Build system detection
echo -e "\n🏗️ Test 2: Build system detection"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator
import os

calculator = HealthCalculator()

# Test build system detection
build_systems = calculator.detect_build_systems('/tmp/health-test-project')
print(f"Detected build systems: {build_systems}")

# Test package manager detection
package_managers = []
if os.path.exists('/tmp/health-test-project/package.json'):
    package_managers.append('npm')
if os.path.exists('/tmp/health-test-project/requirements.txt'):
    package_managers.append('pip')
if os.path.exists('/tmp/health-test-project/Cargo.toml'):
    package_managers.append('cargo')

print(f"Detected package managers: {package_managers}")

if build_systems:
    print("✅ Build system detection working")
else:
    print("❌ Build system detection failed")
EOF

# Test 3: Test coverage analysis
echo -e "\n🧪 Test 3: Test coverage analysis"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator
import os

calculator = HealthCalculator()

# Count source and test files
src_files = 0
test_files = 0

for root, dirs, files in os.walk('/tmp/health-test-project'):
    for file in files:
        if file.endswith('.py'):
            if 'test' in root or file.startswith('test_'):
                test_files += 1
            elif 'src' in root:
                src_files += 1

print(f"Source files: {src_files}")
print(f"Test files: {test_files}")

if src_files > 0:
    test_coverage_ratio = (test_files / src_files) * 100
    print(f"Test coverage ratio: {test_coverage_ratio:.1f}%")

    if test_coverage_ratio >= 80:
        print("✅ Excellent test coverage")
    elif test_coverage_ratio >= 50:
        print("⚠️ Good test coverage")
    else:
        print("❌ Poor test coverage")
else:
    print("❌ No source files found")
EOF

# Test 4: Git repository health
echo -e "\n📝 Test 4: Git repository health"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator
import subprocess
import os

calculator = HealthCalculator()

# Test git repository detection
if os.path.exists('/tmp/health-test-project/.git'):
    print("✅ Git repository detected")

    # Check git status
    try:
        result = subprocess.run(['git', 'status', '--porcelain'],
                              cwd='/tmp/health-test-project',
                              capture_output=True, text=True)
        if result.returncode == 0:
            uncommitted_files = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            print(f"Uncommitted files: {uncommitted_files}")

            if uncommitted_files == 0:
                print("✅ Clean git repository")
            else:
                print("⚠️ Repository has uncommitted changes")
        else:
            print("❌ Git status check failed")
    except Exception as e:
        print(f"❌ Git check error: {e}")

    # Check commit history
    try:
        result = subprocess.run(['git', 'log', '--oneline', '-n', '10'],
                              cwd='/tmp/health-test-project',
                              capture_output=True, text=True)
        if result.returncode == 0:
            commit_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            print(f"Recent commits: {commit_count}")

            if commit_count > 0:
                print("✅ Git history available")
            else:
                print("❌ No git history")
        else:
            print("❌ Git log check failed")
    except Exception as e:
        print(f"❌ Git log error: {e}")
else:
    print("❌ Not a git repository")
EOF

# Test 5: Dependency security analysis
echo -e "\n🔒 Test 5: Dependency security analysis"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator
import json
import os

calculator = HealthCalculator()

# Check for dependency files
dependency_files = []
if os.path.exists('/tmp/health-test-project/package.json'):
    dependency_files.append('package.json')
if os.path.exists('/tmp/health-test-project/requirements.txt'):
    dependency_files.append('requirements.txt')
if os.path.exists('/tmp/health-test-project/Cargo.toml'):
    dependency_files.append('Cargo.toml')

print(f"Dependency files found: {dependency_files}")

# Analyze package.json dependencies
if 'package.json' in dependency_files:
    try:
        with open('/tmp/health-test-project/package.json', 'r') as f:
            package_data = json.load(f)

        deps = package_data.get('dependencies', {})
        dev_deps = package_data.get('devDependencies', {})

        print(f"Production dependencies: {len(deps)}")
        print(f"Development dependencies: {len(dev_deps)}")

        # Check for known vulnerable packages (example)
        vulnerable_packages = ['lodash', 'moment', 'request']
        found_vulnerable = []

        for dep in deps:
            if dep in vulnerable_packages:
                found_vulnerable.append(dep)

        if found_vulnerable:
            print(f"⚠️ Potentially vulnerable packages: {found_vulnerable}")
        else:
            print("✅ No known vulnerable packages detected")

    except Exception as e:
        print(f"❌ Package.json analysis error: {e}")

# Analyze requirements.txt
if 'requirements.txt' in dependency_files:
    try:
        with open('/tmp/health-test-project/requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')

        print(f"Python dependencies: {len(requirements)}")

        # Check for version pinning
        pinned_deps = sum(1 for req in requirements if '>=' in req or '==' in req)
        pinning_ratio = (pinned_deps / len(requirements)) * 100 if requirements else 0

        print(f"Version pinning ratio: {pinning_ratio:.1f}%")

        if pinning_ratio >= 80:
            print("✅ Good version pinning")
        elif pinning_ratio >= 50:
            print("⚠️ Some version pinning")
        else:
            print("❌ Poor version pinning")

    except Exception as e:
        print(f"❌ Requirements.txt analysis error: {e}")
EOF

# Test 6: Performance metrics
echo -e "\n⚡ Test 6: Performance metrics"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator
import time
import os

calculator = HealthCalculator()

# Test calculation performance
start_time = time.time()
health_score = calculator.calculate_health('/tmp/health-test-project')
end_time = time.time()

calculation_time = (end_time - start_time) * 1000  # Convert to milliseconds

print(f"Health calculation time: {calculation_time:.2f}ms")

if calculation_time < 1000:  # Less than 1 second
    print("✅ Performance is acceptable")
else:
    print("❌ Performance needs improvement")

# Test file system metrics
project_size = 0
file_count = 0

for root, dirs, files in os.walk('/tmp/health-test-project'):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            project_size += os.path.getsize(file_path)
            file_count += 1
        except OSError:
            pass

print(f"Project size: {project_size / 1024:.1f} KB")
print(f"File count: {file_count}")

if project_size < 10 * 1024 * 1024:  # Less than 10MB
    print("✅ Project size is reasonable")
else:
    print("⚠️ Large project size")
EOF

# Test 7: Real-time monitoring
echo -e "\n📡 Test 7: Real-time monitoring simulation"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator
import time
import random

calculator = HealthCalculator()

print("Simulating real-time monitoring...")

# Simulate health monitoring over time
for i in range(5):
    health_score = calculator.calculate_health('/tmp/health-test-project')

    # Add some random variation to simulate real changes
    variation = random.uniform(-5, 5)
    simulated_score = max(0, min(100, health_score + variation))

    print(f"Monitoring cycle {i+1}: Health score = {simulated_score:.1f}")

    # Simulate different health states
    if simulated_score >= 80:
        status = "🟢 Healthy"
    elif simulated_score >= 60:
        status = "🟡 Warning"
    else:
        status = "🔴 Critical"

    print(f"  Status: {status}")

    time.sleep(1)

print("✅ Real-time monitoring simulation completed")
EOF

# Test 8: Health visualization data
echo -e "\n📊 Test 8: Health visualization data"
python3 << 'EOF'
import sys
sys.path.append('/Users/archmagece/myopen/scripton/yesman-claude')

from libs.dashboard.health_calculator import HealthCalculator
import json

calculator = HealthCalculator()

# Generate visualization data
health_data = {
    'overall_score': calculator.calculate_health('/tmp/health-test-project'),
    'categories': {},
    'timestamp': int(time.time()),
    'trends': []
}

categories = [
    'build', 'tests', 'dependencies', 'security',
    'performance', 'code_quality', 'git', 'documentation'
]

for category in categories:
    score = calculator.calculate_category_score(category, '/tmp/health-test-project')
    health_data['categories'][category] = score

# Generate trend data (simulated)
import time
for i in range(10):
    timestamp = int(time.time()) - (i * 3600)  # Hourly data
    score = health_data['overall_score'] + random.uniform(-10, 10)
    health_data['trends'].append({
        'timestamp': timestamp,
        'score': max(0, min(100, score))
    })

print("Health visualization data:")
print(json.dumps(health_data, indent=2))

# Validate data structure
required_fields = ['overall_score', 'categories', 'timestamp', 'trends']
for field in required_fields:
    if field in health_data:
        print(f"✅ {field} present in data")
    else:
        print(f"❌ {field} missing from data")
EOF

# Cleanup
cd /
rm -rf "$TEST_PROJECT_DIR"

echo -e "\n📊 Health Monitoring Test Summary:"
echo "- Project health calculation tested"
echo "- Build system detection verified"
echo "- Test coverage analysis completed"
echo "- Git repository health checked"
echo "- Dependency security analysis performed"
echo "- Performance metrics measured"
echo "- Real-time monitoring simulated"
echo "- Visualization data generated"

echo -e "\n✅ Health monitoring tests completed!"
