# 🗑️ Phase 3: 캐시 핵심 파일 제거

**태스크 ID**: CACHE-003  
**예상 시간**: 1시간  
**선행 조건**: CACHE-002 완료  
**후행 태스크**: CACHE-004

## 🎯 목표
캐시 시스템의 핵심 파일들을 안전하게 제거하고 관련 의존성을 완전히 정리

## 📋 실행 단계

### Step 0: 남은 Phase 2 의존성 완료 (20분)

#### 0.1 남은 cache 의존성 제거
```bash
# 현재 상태 확인 - 아직 남은 의존성들이 있음
echo "=== Remaining Phase 2 Dependencies ===" >> phase3_verification.txt
echo "Found dependencies in:" >> phase3_verification.txt
echo "- libs/core/__init__.py (SessionCache import)" >> phase3_verification.txt
echo "- libs/tmux_manager.py (SessionCache import and usage)" >> phase3_verification.txt
echo "- Various test files (cache imports)" >> phase3_verification.txt
echo "" >> phase3_verification.txt
```

#### 0.2 TmuxManager 캐시 제거
- [x] `libs/tmux_manager.py`에서 SessionCache import 제거
- [x] TmuxManager.__init__에서 session_cache 초기화 제거  
- [x] 캐시 메서드 호출들을 직접 libtmux 호출로 교체

#### 0.3 __init__.py 정리
- [x] `libs/core/__init__.py`에서 SessionCache import 및 export 제거

#### 0.4 테스트 파일 수정
- [x] 캐시 관련 테스트 import 제거 (일시적으로 skip 처리)

### Step 1: 제거 전 최종 의존성 확인 (10분)

#### 1.1 현재 상태 백업
```bash
git add -A
git commit -m "checkpoint: before cache core files removal

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 1.2 캐시 파일 사용처 최종 확인
```bash
echo "=== Final Cache Dependencies Check ===" > phase3_verification.txt
echo "Date: $(date)" >> phase3_verification.txt
echo "" >> phase3_verification.txt

# 제거 대상 파일들
cache_files=(
    "libs/core/cache_analytics.py"
    "libs/core/cache_core.py" 
    "libs/core/cache_manager.py"
    "libs/core/cache_storage.py"
    "libs/core/session_cache.py"
)

# 각 파일이 아직 사용되는지 확인
for file in "${cache_files[@]}"; do
    echo "Checking dependencies for: $file" >> phase3_verification.txt
    
    # 파일명에서 모듈명 추출
    module_name=$(basename "$file" .py)
    
    # 해당 모듈을 import하는 파일 검색
    echo "Files importing $module_name:" >> phase3_verification.txt
    grep -r "from.*$module_name import\|import.*$module_name" --include="*.py" . 2>/dev/null >> phase3_verification.txt || echo "No imports found" >> phase3_verification.txt
    echo "" >> phase3_verification.txt
done

echo "Dependencies check completed. Review phase3_verification.txt before proceeding."
```

#### 1.3 안전성 검증
```bash
# 의존성이 남아있는지 확인
if grep -q "libs/core/cache" phase3_verification.txt; then
    echo "⚠️  WARNING: Dependencies still exist. Review before proceeding."
    echo "Check phase3_verification.txt for details."
else
    echo "✅ Safe to proceed with file removal"
fi
```

### Step 2: 캐시 핵심 파일 제거 (20분)

#### 2.1 점진적 파일 제거
```bash
# 제거 대상 파일 목록 확인
echo "Files to be removed:"
ls -la libs/core/cache_*.py libs/core/session_cache.py 2>/dev/null || echo "Some files may already be missing"

# 백업 디렉토리 생성
mkdir -p .backup/cache_files_$(date +%Y%m%d_%H%M%S)
backup_dir=".backup/cache_files_$(date +%Y%m%d_%H%M%S)"

# 파일들을 백업한 후 제거
cache_files=(
    "libs/core/cache_analytics.py"
    "libs/core/cache_core.py" 
    "libs/core/cache_manager.py"
    "libs/core/cache_storage.py"
    "libs/core/session_cache.py"
)

for file in "${cache_files[@]}"; do
    if [ -f "$file" ]; then
        echo "Backing up and removing: $file"
        cp "$file" "$backup_dir/"
        rm "$file"
        echo "✅ Removed: $file"
    else
        echo "⚠️  File not found: $file"
    fi
done

echo "Backup location: $backup_dir"
```

#### 2.2 __init__.py 파일 정리
```bash
# libs/core/__init__.py에서 캐시 관련 export 제거
echo "Cleaning libs/core/__init__.py..."

if [ -f "libs/core/__init__.py" ]; then
    # 백업 생성
    cp libs/core/__init__.py libs/core/__init__.py.backup
    
    # 캐시 관련 export 제거
    sed -i '/cache/d' libs/core/__init__.py
    sed -i '/Cache/d' libs/core/__init__.py
    
    echo "✅ Cleaned libs/core/__init__.py"
else
    echo "⚠️  libs/core/__init__.py not found"
fi
```

### Step 3: Import 구문 정리 (20분)

#### 3.1 전체 프로젝트 Import 정리
```bash
echo "=== Cleaning import statements ===" >> phase3_verification.txt

# 캐시 관련 import 찾기 및 제거
echo "Searching for cache-related imports..."

# 모든 Python 파일에서 캐시 import 제거
find . -name "*.py" -not -path "./.venv/*" -not -path "./.backup/*" -exec grep -l "from.*cache\|import.*cache" {} \; > temp_files_with_cache_imports.txt

if [ -s temp_files_with_cache_imports.txt ]; then
    echo "Files with cache imports found:"
    cat temp_files_with_cache_imports.txt
    
    # 각 파일에서 캐시 import 제거
    while read -r file; do
        echo "Cleaning imports in: $file"
        
        # 백업 생성
        cp "$file" "$file.import_backup"
        
        # 캐시 관련 import 제거
        sed -i '/from.*cache.*import/d' "$file"
        sed -i '/import.*cache/d' "$file"
        sed -i '/from.*Cache.*import/d' "$file"
        
        echo "✅ Cleaned imports in: $file" >> phase3_verification.txt
    done < temp_files_with_cache_imports.txt
    
    rm temp_files_with_cache_imports.txt
else
    echo "✅ No cache imports found"
fi
```

#### 3.2 Import 정리 검증
```bash
# 정리 후 남은 캐시 참조 확인
echo "=== Remaining cache references ===" >> phase3_verification.txt
grep -r "cache\|Cache" --include="*.py" . 2>/dev/null | grep -v ".backup" | grep -v "__pycache__" >> phase3_verification.txt || echo "No remaining cache references" >> phase3_verification.txt
```

### Step 4: 의존성 최종 검증 (10분)

#### 4.1 Python 모듈 구문 검증
```bash
echo "=== Module syntax verification ==="

# 주요 모듈들이 정상적으로 import되는지 확인
modules_to_test=(
    "libs.core.session_manager"
    "libs.dashboard.widgets.session_browser"
    "libs.dashboard.widgets.project_health"
    "commands.ls"
    "commands.show"
    "commands.status"
)

for module in "${modules_to_test[@]}"; do
    python -c "
try:
    import $module
    print('✅ $module import successful')
except Exception as e:
    print('❌ $module import failed:', str(e))
    exit(1)
" || echo "Module verification failed for $module"
done
```

#### 4.2 CLI 기본 동작 확인
```bash
echo "=== CLI functionality verification ==="

# CLI 도움말 동작 확인
if uv run ./yesman.py --help > /dev/null 2>&1; then
    echo "✅ CLI help function works"
else
    echo "❌ CLI help function failed"
fi

# 주요 명령어 기본 동작 확인 (실제 실행은 하지 않고 파싱만)
commands=("ls" "show" "status")
for cmd in "${commands[@]}"; do
    if uv run ./yesman.py "$cmd" --help > /dev/null 2>&1; then
        echo "✅ Command '$cmd' help works"
    else
        echo "❌ Command '$cmd' help failed"
    fi
done
```

## ✅ 완료 기준

### 필수 제거 사항
- [ ] 5개 캐시 핵심 파일 완전 제거
- [ ] `libs/core/__init__.py`에서 캐시 export 제거
- [ ] 전체 프로젝트에서 캐시 import 구문 제거
- [ ] 남은 캐시 참조 0개 확인

### 동작 검증
```bash
# 최종 검증 스크립트
echo "=== Phase 3 Final Verification ==="

# 1. 파일 제거 확인
removed_files=("libs/core/cache_analytics.py" "libs/core/cache_core.py" "libs/core/cache_manager.py" "libs/core/cache_storage.py" "libs/core/session_cache.py")
for file in "${removed_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "✅ $file successfully removed"
    else
        echo "❌ $file still exists"
    fi
done

# 2. Import 구문 정리 확인
if ! grep -r "from.*cache.*import\|import.*cache" --include="*.py" . 2>/dev/null | grep -v ".backup"; then
    echo "✅ All cache imports removed"
else
    echo "❌ Some cache imports remain"
fi

# 3. 기본 기능 동작 확인
python -c "from libs.core.session_manager import SessionManager; SessionManager()" && echo "✅ SessionManager works without cache"
uv run ./yesman.py --help > /dev/null && echo "✅ CLI basic function maintained"
```

## 📄 결과 확인

제거 완료 후 확인사항:
1. **파일 제거**: 5개 캐시 파일 완전 삭제
2. **백업 생성**: `.backup/cache_files_[timestamp]/` 디렉토리에 백업 완료
3. **Import 정리**: 모든 캐시 import 구문 제거
4. **기능 유지**: 기본 CLI 및 모듈 기능 정상 동작

## 🔄 다음 단계
검증 완료 후 `CACHE-004 Phase 4: 테스트 정리` 진행

## 🚨 롤백 절차
문제 발생 시:
```bash
# 1. 파일 복원
cp .backup/cache_files_*/cache_*.py libs/core/
cp .backup/cache_files_*/session_cache.py libs/core/

# 2. Import 백업 복원
find . -name "*.import_backup" -exec sh -c 'mv "$0" "${0%.import_backup}"' {} \;

# 3. __init__.py 복원
cp libs/core/__init__.py.backup libs/core/__init__.py

# 4. 검증
python -c "from libs.core.session_manager import SessionManager; SessionManager()"
```

## 📝 작업 기록
```bash
# 진행사항 기록
echo "Phase 3 completed: $(date)" >> phase3_verification.txt
echo "Files removed: ${#cache_files[@]}" >> phase3_verification.txt
echo "Backup location: $backup_dir" >> phase3_verification.txt
```