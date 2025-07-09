# 📊 Phase 1: 캐시 시스템 영향도 분석

**태스크 ID**: CACHE-001  
**예상 시간**: 1시간  
**선행 조건**: 없음  
**후행 태스크**: CACHE-002

## 🎯 목표
캐시 시스템 제거 전 전체 영향도를 분석하고 안전한 제거를 위한 기반 데이터를 수집

## 📋 실행 단계

### Step 1: 백업 및 기준점 설정 (10분)

```bash
# 1.1 작업 브랜치 생성
git checkout -b cache-removal-analysis
git push -u origin cache-removal-analysis

# 1.2 현재 상태 백업
git add -A
git commit -m "backup: before cache removal analysis

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 1.3 성능 기준점 측정
echo "=== Performance Baseline ===" > cache_analysis_results.txt
echo "Date: $(date)" >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt

# CLI 명령어 성능 측정
for cmd in "ls" "show" "status"; do
    echo "Testing: uv run ./yesman.py $cmd" >> cache_analysis_results.txt
    { time uv run ./yesman.py $cmd; } 2>&1 | grep real >> cache_analysis_results.txt
    echo "" >> cache_analysis_results.txt
done
```

### Step 2: 캐시 사용 패턴 분석 (20분)

```bash
# 2.1 캐시 관련 파일 목록 생성
echo "=== Cache Related Files ===" >> cache_analysis_results.txt
find . -name "*.py" -path "./libs/*" -exec grep -l "cache\|Cache" {} \; | sort >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt

# 2.2 캐시 사용 위치 상세 분석
echo "=== Cache Usage Patterns ===" >> cache_analysis_results.txt
rg "cache\.|Cache\(" --type py libs/ commands/ api/ -n >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt

# 2.3 import 구문 분석
echo "=== Cache Import Statements ===" >> cache_analysis_results.txt
rg "from.*cache|import.*cache" --type py -n >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt

# 2.4 캐시 핵심 파일 라인 수 측정
echo "=== Cache Core Files Line Count ===" >> cache_analysis_results.txt
wc -l libs/core/cache_*.py libs/core/session_cache.py >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt
```

### Step 3: 의존성 매핑 (20분)

```bash
# 3.1 캐시 의존성 트리 생성
echo "=== Cache Dependency Tree ===" >> cache_analysis_results.txt

# SessionManager에서 캐시 사용 패턴
echo "--- SessionManager Cache Usage ---" >> cache_analysis_results.txt
rg "cache" libs/core/session_manager.py -n -A 2 -B 2 >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt

# Dashboard 위젯에서 캐시 사용
echo "--- Dashboard Widgets Cache Usage ---" >> cache_analysis_results.txt
for file in libs/dashboard/widgets/*.py; do
    if grep -q "cache" "$file"; then
        echo "File: $file" >> cache_analysis_results.txt
        rg "cache" "$file" -n >> cache_analysis_results.txt
        echo "" >> cache_analysis_results.txt
    fi
done

# API에서 캐시 사용
echo "--- API Cache Usage ---" >> cache_analysis_results.txt
rg "cache" api/ --type py -n >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt
```

### Step 4: 테스트 파일 분석 (10분)

```bash
# 4.1 캐시 테스트 파일 목록
echo "=== Cache Test Files ===" >> cache_analysis_results.txt
find tests/ -name "*cache*" -type f >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt

# 4.2 테스트 파일 라인 수
echo "=== Cache Test Files Size ===" >> cache_analysis_results.txt
find tests/ -name "*cache*" -type f -exec wc -l {} \; >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt

# 4.3 캐시 관련 테스트 함수 수
echo "=== Cache Test Functions Count ===" >> cache_analysis_results.txt
find tests/ -name "*cache*.py" -exec grep -c "def test_" {} \; | paste -d: <(find tests/ -name "*cache*.py") - >> cache_analysis_results.txt
echo "" >> cache_analysis_results.txt
```

## ✅ 완료 기준

### 필수 산출물
- [x] `cache_analysis_results.txt` 파일 생성 완료
- [x] 성능 기준점 데이터 수집 완료
- [x] 캐시 사용 패턴 18개 파일 분석 완료
- [x] 의존성 매핑 완료
- [x] 테스트 파일 영향도 분석 완료

### 검증 체크리스트
```bash
# 결과 파일 검증
[ -f cache_analysis_results.txt ] && echo "✅ Analysis file created"
[ $(wc -l < cache_analysis_results.txt) -gt 50 ] && echo "✅ Sufficient analysis data"

# 키 데이터 존재 확인
grep -q "Performance Baseline" cache_analysis_results.txt && echo "✅ Performance data collected"
grep -q "Cache Related Files" cache_analysis_results.txt && echo "✅ File list generated"
grep -q "Cache Dependency Tree" cache_analysis_results.txt && echo "✅ Dependency mapping done"
```

## 📄 결과물 검토

분석 완료 후 다음을 확인:

1. **영향받는 파일 수**: 예상 18개 파일
2. **제거 대상 코드량**: 약 962줄 + 테스트 1,484줄
3. **주요 의존성**: SessionManager, Dashboard widgets, API endpoints
4. **성능 기준점**: 각 CLI 명령어별 실행시간

## 🔄 다음 단계
분석 완료 후 `CACHE-002 Phase 2: 점진적 제거` 진행

## 🚨 주의사항
- 분석 과정에서 코드 수정 금지
- 결과 데이터는 정확히 기록
- 의문 사항 발생 시 분석 중단 후 검토