# 안전한 정리 워크플로우 (Safe Cleanup Workflow)

> ⚠️ **경고**: 이 문서는 `git clean -dfx` 사고를 방지하기 위한 필수 가이드입니다.

## 🚨 사고 요약

2025년 8월 13일, `git clean -dfx` 명령으로 인해 다음 파일들이 삭제되었습니다:

### 삭제된 중요 파일들

- `tauri-dashboard/src/lib/**` - Tauri 대시보드 핵심 라이브러리
- `tauri-dashboard/static/` - 정적 자원
- `tauri-dashboard/tests/` - 테스트 파일
- `tauri-dashboard/docs/` - 문서 파일
- 기타 임시 및 빌드 파일들

### 근본 원인

- `.gitignore`의 글로벌 `lib/` 패턴이 Tauri의 `src/lib/` 디렉토리까지 영향을 미침
- 안전한 정리 프로세스 없이 `git clean -dfx` 사용

## 🛡️ 예방 조치

### 1. .gitignore 개선 완료

```gitignore
# =============================================================================
# TAURI DASHBOARD PROTECTION
# Critical Tauri dashboard files that should never be ignored
# =============================================================================

# NEVER ignore these critical Tauri dashboard directories
!tauri-dashboard/src/lib/
!tauri-dashboard/src/lib/**
!tauri-dashboard/src/routes/
!tauri-dashboard/src/routes/**
!tauri-dashboard/static/
!tauri-dashboard/static/**
!tauri-dashboard/tests/
!tauri-dashboard/tests/**
!tauri-dashboard/docs/
!tauri-dashboard/docs/**

# NEVER ignore these critical files
!tauri-dashboard/package.json
!tauri-dashboard/tsconfig.json
!tauri-dashboard/vite.config.ts
!tauri-dashboard/svelte.config.js
!tauri-dashboard/tailwind.config.js
!tauri-dashboard/src-tauri/Cargo.toml
!tauri-dashboard/src-tauri/tauri.conf.json
!tauri-dashboard/src-tauri/src/**
```

### 2. 안전한 Python lib 패턴

```gitignore
# Python lib directories (SPECIFIC PATTERNS ONLY - DO NOT USE GLOBAL lib/)
# IMPORTANT: Global lib/ pattern was causing Tauri dashboard files to be ignored
# Only ignore Python-specific lib directories
/lib/  # Root level Python lib only
libs/**/lib/  # Python lib inside libs directory
**/python/lib/  # Python lib directories
**/venv/lib/  # Virtual environment lib
**/virtualenv/lib/  # Virtual environment lib
**/.venv/lib/  # Virtual environment lib
**/site-packages/  # Python packages
**/__pycache__/lib/  # Cached Python lib
```

## 📋 안전한 정리 프로세스

### 🔍 1단계: 사전 확인

```bash
# 현재 git 상태 확인
git status

# 무시될 파일들 미리 확인 (중요!)
git clean -n -d -x

# 특정 디렉토리만 확인
git clean -n -d -x tauri-dashboard/
```

### 🎯 2단계: 선택적 정리

```bash
# 안전한 선택적 정리 (권장)
git clean -f -d -x --exclude=tauri-dashboard/

# 또는 특정 패턴만 정리
git clean -f -d -x "*.log" "*.tmp" "*_cache/"

# Python 관련 파일만 정리
git clean -f -d -x "**/python/" "**/__pycache__/" "**/lib/" --exclude=tauri-dashboard/
```

### ⚡ 3단계: 단계별 정리 (가장 안전)

```bash
# 1. 로그 파일만 정리
git clean -f -x "*.log"

# 2. 캐시 디렉토리 정리
git clean -f -d "__pycache__/"

# 3. 임시 파일 정리
find . -name "*.tmp" -type f -delete
find . -name "temp_*" -type f -delete

# 4. Python 빌드 아티팩트 정리
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

## ⛔ 절대 금지 명령어

```bash
# ❌ 절대 사용하지 말 것
git clean -dfx  # 모든 무시된 파일 삭제 (위험!)
git clean -dfX  # 모든 무시된 파일만 삭제 (여전히 위험!)

# ❌ 백업 없이 전체 정리
rm -rf build/ lib/ tmp/  # 글로벌 삭제 위험

# ❌ 와일드카드 사용 시 주의
rm -rf */lib/  # Tauri lib도 삭제될 위험
```

## ✅ 권장 명령어

```bash
# ✅ 미리보기 후 실행
git clean -n -d -x  # 먼저 확인
git clean -f -d -x --exclude=tauri-dashboard/  # 안전한 실행

# ✅ 백업 후 정리
cp -r tauri-dashboard/src/lib /tmp/lib_backup
# 정리 작업 수행
# 문제 발생 시 복원: cp -r /tmp/lib_backup tauri-dashboard/src/lib

# ✅ 특정 패턴만 정리
find . -name "*.log" -not -path "./tauri-dashboard/*" -delete
find . -name "__pycache__" -not -path "./tauri-dashboard/*" -type d -exec rm -rf {} +
```

## 🔧 복구 절차

### 즉시 복구 체크리스트

1. **빌드 테스트**

   ```bash
   cd tauri-dashboard
   pnpm run build
   ```

1. **누락 파일 확인**

   ```bash
   # 필수 디렉토리 확인
   ls -la src/lib/
   ls -la static/
   ls -la tests/
   ls -la docs/
   ```

1. **Git 히스토리에서 복구**

   ```bash
   # 특정 파일 복구
   git checkout HEAD -- tauri-dashboard/src/lib/

   # 특정 커밋에서 복구
   git checkout <commit-hash> -- tauri-dashboard/src/lib/
   ```

### 완전 복구 프로세스

1. **git log 확인**

   ```bash
   git log --oneline --name-only -- tauri-dashboard/src/lib/
   ```

1. **마지막 정상 커밋 찾기**

   ```bash
   git show --name-only <commit-hash>
   ```

1. **파일별 복구**

   ```bash
   git checkout <commit-hash> -- tauri-dashboard/src/lib/stores/health.ts
   git checkout <commit-hash> -- tauri-dashboard/src/lib/utils/api.ts
   # ... 기타 파일들
   ```

## 🔍 모니터링 및 검증

### 정기 검증 스크립트

```bash
#!/bin/bash
# check_tauri_integrity.sh

echo "=== Tauri 대시보드 무결성 검증 ==="

# 필수 디렉토리 확인
DIRS=("src/lib" "src/routes" "static" "tests" "docs")
for dir in "${DIRS[@]}"; do
    if [ -d "tauri-dashboard/$dir" ]; then
        echo "✅ $dir 존재"
    else
        echo "❌ $dir 누락!"
    fi
done

# 필수 파일 확인
FILES=("package.json" "tsconfig.json" "vite.config.ts")
for file in "${FILES[@]}"; do
    if [ -f "tauri-dashboard/$file" ]; then
        echo "✅ $file 존재"
    else
        echo "❌ $file 누락!"
    fi
done

# 빌드 테스트
echo "=== 빌드 테스트 ==="
cd tauri-dashboard
if pnpm run build > /dev/null 2>&1; then
    echo "✅ 빌드 성공"
else
    echo "❌ 빌드 실패"
fi
```

### 자동화된 백업

```bash
#!/bin/bash
# backup_critical_files.sh

BACKUP_DIR="/tmp/yesman_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 중요 디렉토리 백업
cp -r tauri-dashboard/src/lib "$BACKUP_DIR/"
cp -r tauri-dashboard/src/routes "$BACKUP_DIR/"
cp -r tauri-dashboard/static "$BACKUP_DIR/"
cp -r tauri-dashboard/tests "$BACKUP_DIR/"
cp -r tauri-dashboard/docs "$BACKUP_DIR/"

echo "백업 완료: $BACKUP_DIR"
```

## 📚 참고 자료

### Git Clean 옵션 설명

- `-n, --dry-run`: 미리보기 (실제 삭제 안함)
- `-f, --force`: 강제 실행
- `-d`: 디렉토리도 포함
- `-x`: .gitignore 무시된 파일 포함
- `-X`: .gitignore 무시된 파일만
- `--exclude=pattern`: 특정 패턴 제외

### 안전한 대안 도구

- `find` 명령어로 선택적 삭제
- IDE의 정리 기능 사용
- 프로젝트별 정리 스크립트 작성

## 🚀 미래 개선 사항

1. **CI/CD 파이프라인에 무결성 체크 추가**
1. **Pre-commit hook으로 중요 파일 보호**
1. **자동 백업 시스템 구축**
1. **정리 작업 전 자동 알림 시스템**

______________________________________________________________________

**⚠️ 기억하세요**: `git clean -dfx`는 복구 불가능한 파일 삭제를 수행합니다. 항상 `-n` 옵션으로 미리 확인하고, 중요 파일은 백업하세요!
