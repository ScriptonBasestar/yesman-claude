# 🧪 Phase 4: 캐시 테스트 파일 정리

**태스크 ID**: CACHE-004  
**예상 시간**: 1시간  
**선행 조건**: CACHE-003 완료  
**후행 태스크**: CACHE-005

## 🎯 목표
캐시 관련 테스트 파일들을 제거하고 기존 테스트에서 캐시 관련 코드를 정리

## 📋 실행 단계

### Step 1: 테스트 파일 현황 분석 (10분)

#### 1.1 현재 상태 백업
```bash
git add -A
git commit -m "checkpoint: before cache test cleanup

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 1.2 캐시 테스트 파일 목록 생성
```bash
echo "=== Cache Test Files Analysis ===" > phase4_test_analysis.txt
echo "Date: $(date)" >> phase4_test_analysis.txt
echo "" >> phase4_test_analysis.txt

# 캐시 전용 테스트 파일 찾기
echo "=== Dedicated Cache Test Files ===" >> phase4_test_analysis.txt
find tests/ -name "*cache*" -type f >> phase4_test_analysis.txt
echo "" >> phase4_test_analysis.txt

# 각 파일의 크기 확인
echo "=== Cache Test Files Size ===" >> phase4_test_analysis.txt
find tests/ -name "*cache*" -type f -exec wc -l {} \; >> phase4_test_analysis.txt
echo "" >> phase4_test_analysis.txt

# 총 라인 수 계산
total_lines=$(find tests/ -name "*cache*.py" -exec wc -l {} \; | awk '{sum += $1} END {print sum}')
echo "Total cache test lines to be removed: $total_lines" >> phase4_test_analysis.txt
echo "" >> phase4_test_analysis.txt

# 테스트 함수 개수 확인
echo "=== Cache Test Functions Count ===" >> phase4_test_analysis.txt
find tests/ -name "*cache*.py" -exec grep -c "def test_" {} \; | paste -d: <(find tests/ -name "*cache*.py") - >> phase4_test_analysis.txt
echo "" >> phase4_test_analysis.txt
```

#### 1.3 혼합 테스트 파일에서 캐시 사용 확인
```bash
# 캐시 전용이 아닌 파일에서 캐시 테스트 확인
echo "=== Mixed Test Files with Cache Usage ===" >> phase4_test_analysis.txt
grep -r "cache\|Cache" tests/ --include="*.py" -l | grep -v -E "cache\.(py|md)" >> phase4_test_analysis.txt || echo "No mixed files found" >> phase4_test_analysis.txt
echo "" >> phase4_test_analysis.txt
```

### Step 2: 캐시 전용 테스트 파일 제거 (20분)

#### 2.1 백업 생성
```bash
# 테스트 파일 백업 디렉토리 생성
backup_test_dir=".backup/cache_tests_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_test_dir"

echo "Creating backup of cache test files..."
```

#### 2.2 캐시 테스트 디렉토리 제거
```bash
# 캐시 전용 테스트 디렉토리가 있는지 확인 후 제거
cache_test_dirs=(
    "tests/unit/core/cache"
    "tests/integration/cache"
)

for dir in "${cache_test_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "Backing up and removing directory: $dir"
        cp -r "$dir" "$backup_test_dir/"
        rm -rf "$dir"
        echo "✅ Removed directory: $dir"
    else
        echo "⚠️  Directory not found: $dir"
    fi
done
```

#### 2.3 개별 캐시 테스트 파일 제거
```bash
# 루트 tests/ 디렉토리의 캐시 테스트 파일들
cache_test_files=(
    "tests/test_session_cache.py"
    "tests/test_session_manager_cache.py"
    "tests/test_session_cache_integration.py"
    "tests/test_dashboard_cache_integration.py"
    "tests/test_advanced_cache_strategies.py"
    "tests/test_cache_visualization.py"
)

for file in "${cache_test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "Backing up and removing: $file"
        cp "$file" "$backup_test_dir/"
        rm "$file"
        echo "✅ Removed: $file"
    else
        echo "⚠️  File not found: $file"
    fi
done

echo "Test files backup location: $backup_test_dir"
```

### Step 3: 기존 테스트에서 캐시 코드 정리 (20분)

#### 3.1 혼합 테스트 파일 정리
```bash
echo "=== Cleaning cache references from mixed test files ===" >> phase4_test_analysis.txt

# 캐시 사용하는 혼합 테스트 파일 찾기
mixed_test_files=$(grep -r "cache\|Cache" tests/ --include="*.py" -l | grep -v -E "cache\.(py|md)" || echo "")

if [ -n "$mixed_test_files" ]; then
    echo "Mixed test files with cache usage:"
    echo "$mixed_test_files"
    
    # 각 파일에서 캐시 관련 테스트 제거
    echo "$mixed_test_files" | while read -r file; do
        if [ -f "$file" ]; then
            echo "Processing mixed test file: $file"
            
            # 백업 생성
            cp "$file" "$file.cache_cleanup_backup"
            
            # 캐시 관련 import 제거
            sed -i '/from.*cache.*import/d' "$file"
            sed -i '/import.*cache/d' "$file"
            
            # 캐시 관련 테스트 함수 제거 (def test_.*cache로 시작하는 함수)
            sed -i '/def test_.*cache/,/^def \|^class \|^$/{ /^def \|^class /!d; }' "$file"
            
            # 캐시 관련 assert 구문 제거
            sed -i '/assert.*cache/d' "$file"
            sed -i '/\.cache\./d' "$file"
            
            echo "✅ Cleaned cache references from: $file" >> phase4_test_analysis.txt
        fi
    done
else
    echo "✅ No mixed test files with cache usage found"
fi
```

#### 3.2 conftest.py 및 fixtures 정리
```bash
# conftest.py에서 캐시 관련 fixture 제거
if [ -f "tests/conftest.py" ]; then
    echo "Cleaning cache fixtures from conftest.py..."
    
    # 백업 생성
    cp tests/conftest.py tests/conftest.py.cache_cleanup_backup
    
    # 캐시 관련 fixture 제거
    sed -i '/cache.*fixture/,/^@\|^def \|^$/{ /^@\|^def /!d; }' tests/conftest.py
    sed -i '/cache/d' tests/conftest.py
    
    echo "✅ Cleaned cache fixtures from conftest.py"
fi

# fixtures 디렉토리에서 캐시 관련 mock 제거
if [ -d "tests/fixtures" ]; then
    echo "Cleaning cache mocks from fixtures..."
    
    find tests/fixtures -name "*.py" -exec grep -l "cache\|Cache" {} \; | while read -r file; do
        echo "Cleaning cache mocks from: $file"
        cp "$file" "$file.cache_cleanup_backup"
        sed -i '/cache/d' "$file"
        sed -i '/Cache/d' "$file"
    done
fi
```

### Step 4: 테스트 구성 정리 (10분)

#### 4.1 pytest 설정 정리
```bash
# pytest.ini 또는 pyproject.toml에서 캐시 테스트 관련 설정 제거
if [ -f "pytest.ini" ]; then
    echo "Checking pytest.ini for cache test configurations..."
    if grep -q "cache" pytest.ini; then
        cp pytest.ini pytest.ini.backup
        sed -i '/cache/d' pytest.ini
        echo "✅ Cleaned cache configurations from pytest.ini"
    fi
fi

if [ -f "pyproject.toml" ]; then
    echo "Checking pyproject.toml for cache test configurations..."
    if grep -q "cache" pyproject.toml; then
        cp pyproject.toml pyproject.toml.backup
        sed -i '/cache/d' pyproject.toml
        echo "✅ Cleaned cache configurations from pyproject.toml"
    fi
fi
```

#### 4.2 테스트 실행 스크립트 정리
```bash
# 테스트 실행 관련 스크립트에서 캐시 테스트 제거
if [ -f "run_tests.sh" ]; then
    echo "Cleaning cache tests from run_tests.sh..."
    sed -i '/cache/d' run_tests.sh
fi

# Makefile에서 캐시 테스트 제거
if [ -f "Makefile" ]; then
    echo "Cleaning cache tests from Makefile..."
    sed -i '/cache/d' Makefile
fi
```

## ✅ 완료 기준

### 필수 제거 사항
- [x] 캐시 전용 테스트 디렉토리 제거 (tests/unit/core/cache/, tests/integration/cache/)
- [x] 개별 캐시 테스트 파일 6개 제거
- [x] 혼합 테스트 파일에서 캐시 관련 코드 정리
- [x] conftest.py 및 fixtures에서 캐시 코드 제거

### 백업 및 검증
```bash
# 제거 검증 스크립트
echo "=== Phase 4 Test Cleanup Verification ==="

# 1. 캐시 테스트 파일 제거 확인
if ! find tests/ -name "*cache*" -type f | grep -q .; then
    echo "✅ All dedicated cache test files removed"
else
    echo "❌ Some cache test files remain:"
    find tests/ -name "*cache*" -type f
fi

# 2. 캐시 테스트 디렉토리 제거 확인
cache_dirs=("tests/unit/core/cache" "tests/integration/cache")
for dir in "${cache_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "✅ Directory removed: $dir"
    else
        echo "❌ Directory still exists: $dir"
    fi
done

# 3. 혼합 파일에서 캐시 참조 제거 확인
remaining_cache_refs=$(grep -r "cache\|Cache" tests/ --include="*.py" | grep -v ".backup" | wc -l)
echo "Remaining cache references in tests: $remaining_cache_refs"
if [ "$remaining_cache_refs" -eq 0 ]; then
    echo "✅ All cache references removed from tests"
else
    echo "⚠️  Some cache references remain (may be legitimate non-cache usage)"
fi

# 4. 백업 확인
if [ -d "$backup_test_dir" ]; then
    backup_count=$(find "$backup_test_dir" -name "*.py" | wc -l)
    echo "✅ Backup created with $backup_count files in $backup_test_dir"
else
    echo "❌ Backup directory not created"
fi
```

## 📄 정리 결과

제거 완료 후 확인사항:
1. **테스트 파일 제거**: 예상 1,484줄의 캐시 테스트 코드 제거
2. **백업 완료**: 모든 제거된 파일이 백업 디렉토리에 보관
3. **기존 테스트 정리**: 캐시 관련 코드 완전 제거
4. **설정 파일 정리**: pytest 설정에서 캐시 관련 내용 제거

## 🔄 다음 단계
정리 완료 후 `CACHE-005 Phase 5: 성능 검증` 진행

## 🚨 롤백 절차
문제 발생 시:
```bash
# 1. 테스트 파일 복원
cp -r "$backup_test_dir"/* tests/

# 2. 백업된 개별 파일 복원
find tests/ -name "*.cache_cleanup_backup" -exec sh -c 'mv "$0" "${0%.cache_cleanup_backup}"' {} \;

# 3. 설정 파일 복원
[ -f pytest.ini.backup ] && mv pytest.ini.backup pytest.ini
[ -f pyproject.toml.backup ] && mv pyproject.toml.backup pyproject.toml

# 4. 테스트 실행으로 복원 확인
python -m pytest tests/ --tb=short
```

## 📝 정리 통계
```bash
# 최종 통계 기록
echo "=== Phase 4 Test Cleanup Statistics ===" >> phase4_test_analysis.txt
echo "Completed: $(date)" >> phase4_test_analysis.txt
echo "Cache test files removed: $(find "$backup_test_dir" -name "*.py" | wc -l)" >> phase4_test_analysis.txt
echo "Total test lines removed: $total_lines" >> phase4_test_analysis.txt
echo "Backup location: $backup_test_dir" >> phase4_test_analysis.txt
```