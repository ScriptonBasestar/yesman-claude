#!/bin/bash
# 스크립트명: Tauri 대시보드 무결성 검증
# 용도: git clean 사고 방지를 위한 Tauri 대시보드 핵심 파일들의 존재 여부 확인
# 사용법: ./check_tauri_integrity.sh
# 예시: ./check_tauri_integrity.sh

set -e

echo "=== Tauri 대시보드 무결성 검증 ==="
echo "검증 시간: $(date)"
echo "현재 위치: $(pwd)"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 검증 결과 카운터
SUCCESS_COUNT=0
FAILURE_COUNT=0
WARNING_COUNT=0

# 함수: 성공 메시지
success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((SUCCESS_COUNT++))
}

# 함수: 실패 메시지
failure() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILURE_COUNT++))
}

# 함수: 경고 메시지
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNING_COUNT++))
}

# Tauri 대시보드 디렉토리 확인
if [ ! -d "tauri-dashboard" ]; then
    failure "tauri-dashboard 디렉토리가 존재하지 않습니다!"
    exit 1
fi

cd tauri-dashboard

echo "1. 핵심 디렉토리 확인"
echo "─────────────────────"

# 필수 디렉토리 확인
DIRS=("src/lib" "src/routes" "src/lib/components" "src/lib/stores" "src/lib/utils")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        success "$dir 디렉토리 존재"
    else
        failure "$dir 디렉토리 누락!"
    fi
done

# 권장 디렉토리 확인
OPTIONAL_DIRS=("static" "tests" "docs")
for dir in "${OPTIONAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        success "$dir 디렉토리 존재"
    else
        warning "$dir 디렉토리 누락 (권장)"
    fi
done

echo ""
echo "2. 핵심 설정 파일 확인"
echo "─────────────────────"

# 필수 파일 확인
FILES=("package.json" "tsconfig.json" "vite.config.ts" "svelte.config.js")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file 파일 존재"
    else
        failure "$file 파일 누락!"
    fi
done

# Tauri 설정 파일 확인
TAURI_FILES=("src-tauri/Cargo.toml" "src-tauri/tauri.conf.json")
for file in "${TAURI_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file 파일 존재"
    else
        failure "$file 파일 누락!"
    fi
done

echo ""
echo "3. 핵심 컴포넌트 파일 확인"
echo "─────────────────────────"

# 핵심 컴포넌트 파일들
COMPONENT_FILES=(
    "src/lib/stores/health.ts"
    "src/lib/utils/api.ts"
    "src/lib/components/common/ConnectionStatusBadge.svelte"
    "src/lib/components/common/HealthStatusIndicator.svelte"
    "src/lib/components/troubleshooting/TroubleshootingWidget.svelte"
    "src/lib/components/help/OnboardingWizard.svelte"
)

for file in "${COMPONENT_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$(basename "$file") 존재"
    else
        failure "$(basename "$file") 누락!"
    fi
done

echo ""
echo "4. Rust 소스 파일 확인"
echo "─────────────────────"

# Rust 소스 파일들
RUST_FILES=("src-tauri/src/main.rs" "src-tauri/src/python_bridge.rs")
for file in "${RUST_FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$(basename "$file") 존재"
    else
        failure "$(basename "$file") 누락!"
    fi
done

echo ""
echo "5. 빌드 테스트"
echo "─────────────"

# 의존성 확인
if [ -f "package.json" ] && command -v pnpm &> /dev/null; then
    echo "의존성 설치 상태 확인 중..."
    if [ ! -d "node_modules" ]; then
        warning "node_modules가 없습니다. pnpm install을 실행해주세요."
    else
        success "node_modules 존재"
        
        # 빌드 테스트
        echo "빌드 테스트 실행 중..."
        if pnpm run build > /tmp/build_test.log 2>&1; then
            success "빌드 테스트 성공"
        else
            failure "빌드 테스트 실패 (로그: /tmp/build_test.log)"
            echo "빌드 오류 요약:"
            tail -5 /tmp/build_test.log | sed 's/^/  /'
        fi
    fi
else
    warning "pnpm이 설치되지 않았거나 package.json이 없습니다"
fi

echo ""
echo "6. .gitignore 보호 설정 확인"
echo "──────────────────────────"

cd ..  # 루트 디렉토리로 이동

if [ -f ".gitignore" ]; then
    if grep -q "!tauri-dashboard/src/lib/" ".gitignore"; then
        success ".gitignore에 Tauri 보호 설정 존재"
    else
        warning ".gitignore에 Tauri 보호 설정이 없습니다"
        echo "  다음 설정을 .gitignore에 추가하는 것을 권장합니다:"
        echo "  !tauri-dashboard/src/lib/"
        echo "  !tauri-dashboard/src/lib/**"
    fi
else
    warning ".gitignore 파일이 없습니다"
fi

echo ""
echo "7. Git 상태 확인"
echo "──────────────"

if git rev-parse --git-dir > /dev/null 2>&1; then
    # Git 저장소인지 확인
    success "Git 저장소입니다"
    
    # 추적되지 않는 중요 파일 확인
    UNTRACKED_IMPORTANT=$(git ls-files --others --exclude-standard tauri-dashboard/src/lib/ 2>/dev/null | head -5)
    if [ -n "$UNTRACKED_IMPORTANT" ]; then
        warning "추적되지 않는 중요 파일들이 있습니다:"
        echo "$UNTRACKED_IMPORTANT" | sed 's/^/  /'
    else
        success "모든 중요 파일이 Git에 추적되고 있습니다"
    fi
else
    warning "Git 저장소가 아닙니다"
fi

echo ""
echo "=== 검증 결과 요약 ==="
echo "성공: ${SUCCESS_COUNT}개"
echo "실패: ${FAILURE_COUNT}개"
echo "경고: ${WARNING_COUNT}개"

if [ $FAILURE_COUNT -eq 0 ]; then
    if [ $WARNING_COUNT -eq 0 ]; then
        echo -e "${GREEN}🎉 모든 검증을 통과했습니다!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  일부 권장사항이 충족되지 않았습니다.${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ 중요한 파일이나 설정이 누락되었습니다!${NC}"
    echo ""
    echo "복구 방법:"
    echo "1. SAFE_CLEANUP_WORKFLOW.md 문서를 참조하세요"
    echo "2. git checkout HEAD -- tauri-dashboard/src/lib/ 명령으로 복구를 시도하세요"
    echo "3. 필요시 이전 커밋에서 파일을 복구하세요"
    exit 2
fi