# 🔧 Phase 2: 캐시 시스템 점진적 제거

**태스크 ID**: CACHE-002  
**예상 시간**: 2-3시간  
**선행 조건**: CACHE-001 완료  
**후행 태스크**: CACHE-003

## 🎯 목표
캐시 의존성을 단계적으로 제거하고 직접 데이터 조회 방식으로 변경

## 📋 실행 단계

### Step 1: SessionManager 캐시 제거 (45분)

#### 1.1 현재 상태 백업
```bash
git add -A
git commit -m "checkpoint: before SessionManager cache removal

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

#### 1.2 SessionManager 수정
```bash
# 백업 생성
cp libs/core/session_manager.py libs/core/session_manager.py.backup

# 수정 사항을 정확히 적용하기 위해 파일 내용 확인
echo "Current SessionManager imports:"
head -30 libs/core/session_manager.py | grep -E "import|from"
```

**수정할 코드 블록들**:

1. **Import 구문 수정** (`libs/core/session_manager.py` 라인 23):
```python
# 제거: from .session_cache import SessionCache
# 유지: 다른 import들
```

2. **OperationMode enum 제거** (라인 28-33):
```python
# 전체 OperationMode 클래스 제거
```

3. **__init__ 메서드 수정** (라인 38-50):
```python
def __init__(self):  # operation_mode 파라미터 제거
    self.config = YesmanConfig()
    from libs.tmux_manager import TmuxManager
    self.tmux_manager = TmuxManager(self.config)
    self.server = libtmux.Server()
    self.logger = self._setup_logger()
    # 캐시 관련 코드 모두 제거
```

4. **캐시 메서드들 제거/수정**:
```bash
# 다음 패턴의 코드를 직접 조회로 변경
# self.cache.get() -> 직접 조회
# self.cache.put() -> 제거
```

#### 1.3 수정 내용 적용
```bash
# 1. Import 제거
sed -i '/from \.session_cache import SessionCache/d' libs/core/session_manager.py

# 2. OperationMode enum 제거 (라인 28-33)
sed -i '/^class OperationMode/,/^$/d' libs/core/session_manager.py

# 3. __init__ 메서드 파라미터 수정
sed -i 's/def __init__(self, operation_mode: Optional\[OperationMode\] = None):/def __init__(self):/' libs/core/session_manager.py

# 4. 캐시 관련 라인들 제거
sed -i '/operation_mode/d' libs/core/session_manager.py
sed -i '/cache.*=/d' libs/core/session_manager.py
sed -i '/self\.cache/d' libs/core/session_manager.py
```

#### 1.4 동작 검증
```bash
# 구문 오류 확인
python -m py_compile libs/core/session_manager.py
echo "SessionManager syntax check: $?"

# 기본 기능 테스트
python -c "
from libs.core.session_manager import SessionManager
sm = SessionManager()
print('SessionManager initialized successfully')
"
```

### Step 2: Dashboard 위젯 수정 (45분)

#### 2.1 위젯 파일별 캐시 제거

```bash
# 영향받는 위젯 파일 확인
echo "Dashboard widgets with cache usage:"
grep -l "cache" libs/dashboard/widgets/*.py || echo "No cache usage found"
```

**각 위젯 파일 수정**:

1. **session_browser.py**:
```bash
# 캐시 관련 import 제거
sed -i '/cache/Id' libs/dashboard/widgets/session_browser.py

# 캐시 호출을 직접 호출로 변경
sed -i 's/self\.cache\.get(\([^)]*\))/self._fetch_direct(\1)/g' libs/dashboard/widgets/session_browser.py
```

2. **project_health.py**:
```bash
# 캐시 로직 제거 및 직접 조회로 변경
sed -i '/cache/d' libs/dashboard/widgets/project_health.py
```

3. **activity_heatmap.py**:
```bash
# 캐시 관련 코드 정리
sed -i '/cache/d' libs/dashboard/widgets/activity_heatmap.py
```

#### 2.2 위젯 동작 검증
```bash
# 각 위젯 import 테스트
for widget in session_browser project_health activity_heatmap progress_tracker git_activity; do
    python -c "
try:
    from libs.dashboard.widgets.$widget import *
    print('✅ $widget import successful')
except Exception as e:
    print('❌ $widget import failed:', e)
" || echo "Widget $widget verification failed"
done
```

### Step 3: API 엔드포인트 수정 (30분)

#### 3.1 API 파일 수정
```bash
# API 라우터에서 캐시 사용 확인
echo "API files with cache usage:"
grep -l "cache" api/routers/*.py || echo "No cache usage in API"

# sessions.py 수정 (캐시 의존성 제거)
if grep -q "cache" api/routers/sessions.py; then
    sed -i '/cache/d' api/routers/sessions.py
    echo "Cache removed from sessions.py"
fi
```

#### 3.2 API 엔드포인트 테스트
```bash
# FastAPI 서버 구문 검사
cd api
python -c "
import main
print('✅ FastAPI app loads successfully')
" || echo "❌ FastAPI app failed to load"
cd ..
```

### Step 4: CLI 명령어 수정 (30분)

#### 4.1 명령어 파일 캐시 제거
```bash
# CLI 명령어에서 캐시 사용 확인
echo "CLI commands with cache usage:"
grep -l "cache" commands/*.py || echo "No cache usage in commands"

# 각 명령어 파일에서 캐시 관련 코드 제거
for cmd_file in commands/*.py; do
    if grep -q "cache" "$cmd_file"; then
        echo "Removing cache from $cmd_file"
        sed -i '/cache/d' "$cmd_file"
    fi
done
```

#### 4.2 CLI 명령어 동작 검증
```bash
# 주요 CLI 명령어 테스트
echo "Testing CLI commands after cache removal:"
uv run ./yesman.py ls || echo "❌ ls command failed"
uv run ./yesman.py show || echo "❌ show command failed"
echo "CLI commands basic test completed"
```

## ✅ 완료 기준

### 필수 수정 사항
- [ ] SessionManager에서 캐시 의존성 완전 제거
- [ ] Dashboard 위젯 3개 이상에서 캐시 제거
- [ ] API 엔드포인트 캐시 의존성 제거
- [ ] CLI 명령어 캐시 참조 제거

### 동작 검증
```bash
# 전체 검증 스크립트
echo "=== Phase 2 Verification ==="

# 1. Python 구문 검증
python -m py_compile libs/core/session_manager.py && echo "✅ SessionManager syntax OK"
python -m py_compile libs/dashboard/widgets/*.py && echo "✅ Widgets syntax OK"

# 2. Import 검증
python -c "from libs.core.session_manager import SessionManager; SessionManager()" && echo "✅ SessionManager import OK"

# 3. CLI 기본 동작 확인
uv run ./yesman.py --help > /dev/null && echo "✅ CLI basic function OK"

# 4. 캐시 참조 제거 확인
! grep -r "SessionCache\|cache\." libs/core/session_manager.py && echo "✅ Cache references removed"
```

## 📄 중간 점검

이 단계 완료 후 확인사항:
1. **코드 컴파일**: 모든 수정된 파일이 구문 오류 없이 컴파일
2. **기본 기능**: CLI 명령어 기본 동작 유지
3. **Import 성공**: 주요 모듈들이 정상적으로 import
4. **캐시 참조 제거**: 캐시 관련 코드 완전 제거

## 🔄 다음 단계
검증 완료 후 `CACHE-003 Phase 3: 핵심 파일 제거` 진행

## 🚨 문제 발생 시 대응
1. **구문 오류**: 즉시 백업 파일로 복원
2. **Import 실패**: 의존성 확인 후 수정
3. **CLI 동작 실패**: 이전 커밋으로 롤백 후 재시작

## 📝 작업 노트
```bash
# 작업 진행사항 기록
echo "Phase 2 Progress Log:" > phase2_progress.txt
echo "Started: $(date)" >> phase2_progress.txt
echo "SessionManager: [완료시각]" >> phase2_progress.txt
echo "Widgets: [완료시각]" >> phase2_progress.txt
echo "API: [완료시각]" >> phase2_progress.txt
echo "CLI: [완료시각]" >> phase2_progress.txt
```