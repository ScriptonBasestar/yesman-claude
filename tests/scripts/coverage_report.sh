#!/bin/bash
# Coverage report generation script for Yesman-Claude

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MIN_COVERAGE=80
COVERAGE_DIR="htmlcov"
COVERAGE_FILE=".coverage"

echo -e "${BLUE}🔍 Yesman-Claude Coverage Report Generator${NC}"
echo "=========================================="

# Check if pytest and coverage are installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}Installing pytest...${NC}"
    pip install pytest
fi

if ! python -c "import pytest_cov" 2>/dev/null; then
    echo -e "${YELLOW}Installing pytest-cov...${NC}"
    pip install pytest-cov
fi

# Clean previous coverage data
echo -e "${BLUE}Cleaning previous coverage data...${NC}"
rm -rf $COVERAGE_DIR $COVERAGE_FILE

# Run tests with coverage
echo -e "${BLUE}Running tests with coverage analysis...${NC}"
python -m pytest tests/ \
    --cov=libs \
    --cov=commands \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=json \
    --cov-fail-under=$MIN_COVERAGE \
    -v

# Check if coverage passed
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Coverage threshold ($MIN_COVERAGE%) met!${NC}"
else
    echo -e "${RED}❌ Coverage below threshold ($MIN_COVERAGE%)${NC}"
fi

# Generate additional reports
echo -e "${BLUE}Generating additional reports...${NC}"

# XML report for CI integration
python -m coverage xml -o coverage.xml

# JSON report for badges
python -m coverage json -o coverage.json

# Create coverage summary
echo -e "${BLUE}Coverage Summary:${NC}"
python -m coverage report --skip-covered --precision=2

# Generate uncovered lines report
echo -e "${BLUE}Uncovered Code Summary:${NC}"
python -m coverage report --show-missing --skip-covered | grep -E "TOTAL|libs/|commands/" | head -20

# Create coverage badge (if coverage-badge is installed)
if command -v coverage-badge &> /dev/null; then
    echo -e "${BLUE}Generating coverage badge...${NC}"
    coverage-badge -o coverage.svg
fi

# Open HTML report
if [ -d "$COVERAGE_DIR" ]; then
    echo -e "${GREEN}✅ HTML coverage report generated: $COVERAGE_DIR/index.html${NC}"
    
    # Ask if user wants to open in browser
    read -p "Open coverage report in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open "$COVERAGE_DIR/index.html"
        elif command -v open &> /dev/null; then
            open "$COVERAGE_DIR/index.html"
        else
            echo -e "${YELLOW}Please open $COVERAGE_DIR/index.html manually${NC}"
        fi
    fi
fi

# Save coverage stats to file
COVERAGE_PERCENT=$(python -m coverage report | grep TOTAL | awk '{print $4}')
echo "Coverage: $COVERAGE_PERCENT" > coverage_stats.txt
echo "Generated: $(date)" >> coverage_stats.txt

echo -e "${BLUE}Coverage analysis complete!${NC}"