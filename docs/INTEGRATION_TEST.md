# Yesman-Claude 통합 테스트 가이드

## 🎯 테스트 목표

실제 프로젝트 환경에서 yesman-claude의 모든 기능을 검증하고 실사용 환경에서의 안정성과 성능을 확인합니다.

## 📋 테스트 체크리스트

### Phase 1: 기본 설정 및 환경 검증

#### 1.1 설치 및 초기 설정
```bash
# 1. 개발 모드 설치
make dev-install
# 또는
pip install -e . --config-settings editable_mode=compat

# 2. 기본 동작 확인
uv run ./yesman.py --help

# 3. 설정 디렉토리 생성 확인
ls -la ~/.yesman/
```

**검증 포인트**:
- [ ] 설치 과정에서 에러 없음
- [ ] 모든 명령어가 help에 표시됨
- [ ] `~/.yesman/` 디렉토리 생성됨

#### 1.2 기본 구성 파일 설정
```bash
# 1. 전역 설정 파일 생성
cat > ~/.yesman/yesman.yaml << 'EOF'
logging:
  level: INFO
  file: ~/.yesman/logs/yesman.log
  
default_choices:
  auto_next: true
  
cache:
  ttl: 5
  max_entries: 100
EOF

# 2. 프로젝트 설정 파일 생성 (테스트용)
cat > ~/.yesman/projects.yaml << 'EOF'
sessions:
  test-project:
    session_name: "yesman-test"
    template: "none"
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["cd /path/to/your/test/project"]
        - window_name: "claude"
          panes:
            - shell_command: ["cd /path/to/your/test/project", "claude"]
EOF
```

**검증 포인트**:
- [ ] 설정 파일이 올바르게 로드됨
- [ ] 로그 파일이 생성됨

### Phase 2: 기본 세션 관리 기능 테스트

#### 2.1 템플릿 및 프로젝트 목록 확인
```bash
# 1. 사용 가능한 템플릿 확인
uv run ./yesman.py ls

# 2. 현재 실행 중인 세션 확인
uv run ./yesman.py show
```

**검증 포인트**:
- [ ] 프로젝트 목록이 올바르게 표시됨
- [ ] 기존 tmux 세션들이 정확히 감지됨

#### 2.2 세션 생성 및 관리
```bash
# 1. 테스트 세션 생성
uv run ./yesman.py setup

# 2. 세션 생성 확인
tmux list-sessions
uv run ./yesman.py show

# 3. 세션 접속 테스트
uv run ./yesman.py enter  # 인터랙티브 선택

# 4. 세션 정리
uv run ./yesman.py teardown
```

**검증 포인트**:
- [ ] 세션이 올바른 구조로 생성됨
- [ ] 윈도우와 팬 구조가 설정과 일치함
- [ ] 세션 접속이 정상 동작함
- [ ] 세션 정리가 완전히 수행됨

### Phase 3: 캐싱 시스템 성능 테스트

#### 3.1 캐시 성능 측정
```bash
# 1. 캐시 통계 확인
uv run ./yesman.py setup  # 세션 생성

# 2. 캐시 성능 측정
time uv run ./yesman.py show  # 첫 번째 호출 (캐시 미스)
time uv run ./yesman.py show  # 두 번째 호출 (캐시 히트)
time uv run ./yesman.py show  # 세 번째 호출 (캐시 히트)

# 3. REST API를 통한 캐시 통계 확인
# API 서버 실행 (별도 터미널)
cd api && python -m uvicorn main:app --reload --port 8001

# 캐시 통계 조회
curl http://localhost:8001/sessions/cache/stats
```

**검증 포인트**:
- [ ] 두 번째 호출부터 응답 시간이 현저히 줄어듦
- [ ] 캐시 히트율이 올바르게 계산됨
- [ ] 캐시 통계 API가 정상 동작함

#### 3.2 캐시 무효화 테스트
```bash
# 1. 새 세션 생성으로 캐시 무효화 테스트
uv run ./yesman.py show  # 캐시된 상태 확인
tmux new-session -d -s "manual-test"  # 수동으로 세션 생성
uv run ./yesman.py show  # 캐시가 업데이트 되는지 확인

# 2. API를 통한 캐시 무효화
curl -X POST http://localhost:8001/sessions/cache/invalidate
```

**검증 포인트**:
- [ ] 수동 세션 생성 시 목록이 업데이트됨
- [ ] API 캐시 무효화가 정상 동작함

### Phase 4: 인터랙티브 브라우저 기능 테스트

#### 4.1 세션 브라우저 기능 테스트
```bash
# 1. 여러 세션 생성 (테스트 데이터)
uv run ./yesman.py setup
tmux new-session -d -s "test-session-1" 
tmux new-session -d -s "test-session-2"
tmux new-session -d -s "test-session-3"

# 2. 인터랙티브 브라우저 실행
uv run ./yesman.py browse --update-interval 2.0
```

**검증 포인트**:
- [ ] 모든 세션이 브라우저에 표시됨
- [ ] 세션 상태가 정확히 표시됨 (실행 중, 유휴 등)
- [ ] 활동 히트맵이 렌더링됨
- [ ] 키보드 네비게이션이 동작함 (↑↓, Tab, Enter)
- [ ] 실시간 업데이트가 작동함

#### 4.2 다양한 뷰 모드 테스트
```bash
# 브라우저 실행 중 키보드 테스트:
# - Tab: Tree → List → Grid 뷰 전환
# - ↑↓: 세션 선택 이동  
# - Enter: 세션 연결 시도
# - R: 새로고침
# - Q: 종료
```

**검증 포인트**:
- [ ] Tree, List, Grid 뷰가 모두 정상 렌더링됨
- [ ] 뷰 전환이 부드럽게 동작함
- [ ] 각 뷰에서 정보가 적절히 표시됨

### Phase 5: AI 학습 시스템 테스트

#### 5.1 AI 시스템 초기 상태 확인
```bash
# 1. AI 시스템 상태 확인
uv run ./yesman.py ai status

# 2. 학습 히스토리 확인
uv run ./yesman.py ai history --limit 10

# 3. AI 설정 조정
uv run ./yesman.py ai config --threshold 0.7 --auto-response
```

**검증 포인트**:
- [ ] AI 시스템이 초기화됨
- [ ] 설정 변경이 올바르게 적용됨
- [ ] 학습 데이터 디렉토리가 생성됨

#### 5.2 AI 응답 예측 테스트
```bash
# 1. 다양한 프롬프트로 예측 테스트
uv run ./yesman.py ai predict "Do you want to overwrite the file? (y/n)"
uv run ./yesman.py ai predict "Select an option: 1) Yes 2) No 3) Cancel"
uv run ./yesman.py ai predict "Continue with the operation? (yes/no)"

# 2. 컨텍스트가 포함된 예측
uv run ./yesman.py ai predict "Run tests? (y/n)" --context "test_context" --project "yesman-claude"
```

**검증 포인트**:
- [ ] 각 프롬프트 타입이 올바르게 분류됨
- [ ] 신뢰도 점수가 합리적 범위임
- [ ] 컨텍스트가 예측에 영향을 줌

### Phase 6: 프로젝트 상태 대시보드 테스트

#### 6.1 기본 상태 확인
```bash
# 1. 빠른 상태 확인
uv run ./yesman.py status

# 2. 상세 상태 확인  
uv run ./yesman.py status --detailed

# 3. 인터랙티브 대시보드
uv run ./yesman.py status --interactive --update-interval 3.0
```

**검증 포인트**:
- [ ] 프로젝트 건강도가 계산됨
- [ ] Git 활동이 올바르게 감지됨
- [ ] TODO 진행률이 표시됨
- [ ] 실시간 업데이트가 동작함

#### 6.2 다양한 프로젝트 타입 테스트
```bash
# Node.js 프로젝트에서 테스트
cd /path/to/nodejs/project
uv run /path/to/yesman-claude/yesman.py status --detailed

# Python 프로젝트에서 테스트  
cd /path/to/python/project
uv run /path/to/yesman-claude/yesman.py status --detailed

# Git 저장소가 아닌 디렉토리에서 테스트
cd /tmp
uv run /path/to/yesman-claude/yesman.py status
```

**검증 포인트**:
- [ ] 각 프로젝트 타입에서 적절한 정보가 표시됨
- [ ] Git 저장소가 아닌 경우 graceful degradation
- [ ] 빌드/테스트 상태가 올바르게 감지됨

### Phase 7: 로그 시스템 테스트

#### 7.1 로그 설정 및 기본 동작 테스트
```bash
# 1. 로그 시스템 설정
uv run ./yesman.py logs configure --output-dir ~/.yesman/logs --format json --compression

# 2. 로그 생성 활동 수행
uv run ./yesman.py setup
uv run ./yesman.py browse &  # 백그라운드 실행
sleep 10
kill %1  # 브라우저 종료

# 3. 로그 분석
uv run ./yesman.py logs analyze --last-hours 1

# 4. 실시간 로그 확인
uv run ./yesman.py logs tail --follow &
# 다른 터미널에서 활동 수행
uv run ./yesman.py show
```

**검증 포인트**:
- [ ] 로그 파일이 올바른 형식으로 생성됨
- [ ] 압축이 설정된 경우 .gz 파일이 생성됨
- [ ] 로그 분석이 의미있는 결과를 제공함
- [ ] 실시간 로그 tail이 동작함

#### 7.2 로그 성능 테스트
```bash
# 고부하 상황에서 로그 성능 테스트
for i in {1..5}; do
  uv run ./yesman.py browse --update-interval 0.5 &
done

# 10초 후 모든 프로세스 종료
sleep 10
pkill -f "yesman.py browse"

# 로그 성능 분석
uv run ./yesman.py logs analyze --last-hours 1
```

**검증 포인트**:
- [ ] 동시 실행 시에도 로그가 누락되지 않음
- [ ] 로그 파일이 손상되지 않음
- [ ] 성능 저하가 허용 범위 내임

### Phase 8: 자동화 시스템 테스트

#### 8.1 컨텍스트 감지 테스트
```bash
# 1. Git 프로젝트에서 테스트 (실제 git 저장소 필요)
cd /path/to/git/project

# 2. 컨텍스트 감지 실행
uv run /path/to/yesman-claude/yesman.py automate detect

# 3. Git 커밋 시뮬레이션
echo "test change" >> test_file.txt
git add test_file.txt
git commit -m "Test commit for automation"

# 4. 다시 컨텍스트 감지
uv run /path/to/yesman-claude/yesman.py automate detect
```

**검증 포인트**:
- [ ] Git 커밋이 감지됨
- [ ] 다른 컨텍스트 타입들이 적절히 감지됨
- [ ] 신뢰도 점수가 합리적임

#### 8.2 자동화 모니터링 테스트
```bash
# 1. 워크플로우 설정 생성
uv run ./yesman.py automate config --output ~/.yesman/workflows.json

# 2. 실시간 모니터링 시작
uv run ./yesman.py automate monitor --interval 5 &

# 3. 다양한 액션 수행 (다른 터미널에서)
cd /path/to/git/project
echo "automation test" >> test_file.txt
git add test_file.txt
git commit -m "Automation monitoring test"

# 4. 빌드/테스트 시뮬레이션
npm test  # 또는 pytest, make test 등

# 5. 모니터링 중지
pkill -f "automate monitor"
```

**검증 포인트**:
- [ ] 실시간 컨텍스트 감지가 동작함
- [ ] 워크플로우 트리거가 감지됨
- [ ] 자동화 로그가 올바르게 기록됨

### Phase 9: 전체 시스템 통합 테스트

#### 9.1 실제 개발 워크플로우 시뮬레이션
```bash
# 1. 전체 시스템 시작
uv run ./yesman.py setup  # 세션 생성

# 2. 모니터링 시스템 시작
uv run ./yesman.py automate monitor --interval 10 &
uv run ./yesman.py status --interactive &

# 3. 실제 개발 작업 시뮬레이션
# - 코드 변경
# - 테스트 실행  
# - 커밋
# - 빌드

# 4. AI 학습 효과 확인
uv run ./yesman.py ai status
uv run ./yesman.py ai history --limit 20
```

**검증 포인트**:
- [ ] 모든 시스템이 동시에 안정적으로 동작함
- [ ] 메모리 사용량이 적정 수준임
- [ ] CPU 사용량이 허용 범위 내임
- [ ] 시스템 간 상호작용이 올바름

#### 9.2 장시간 안정성 테스트
```bash
# 장시간 실행 테스트 (1시간)
#!/bin/bash
START_TIME=$(date +%s)
END_TIME=$((START_TIME + 3600))  # 1시간

uv run ./yesman.py status --interactive --update-interval 5 &
STATUS_PID=$!

uv run ./yesman.py automate monitor --interval 15 &
AUTOMATE_PID=$!

while [ $(date +%s) -lt $END_TIME ]; do
    # 주기적인 활동 시뮬레이션
    echo "Test activity at $(date)" >> stability_test.log
    sleep 60
done

kill $STATUS_PID $AUTOMATE_PID
```

**검증 포인트**:
- [ ] 1시간 동안 크래시 없이 실행됨
- [ ] 메모리 누수가 없음
- [ ] 로그 파일이 과도하게 커지지 않음

### Phase 10: 성능 벤치마크

#### 10.1 응답 시간 측정
```bash
# 1. 캐시 없는 상태에서 측정
uv run ./yesman.py logs configure  # 로그 초기화

# 2. 명령어별 성능 측정
time uv run ./yesman.py show
time uv run ./yesman.py ai status  
time uv run ./yesman.py status
time uv run ./yesman.py automate detect

# 3. 반복 측정으로 캐시 효과 확인
for i in {1..10}; do
    echo "Iteration $i:"
    time uv run ./yesman.py show
done
```

#### 10.2 동시 사용자 시뮬레이션
```bash
# 동시 접근 테스트
for i in {1..5}; do
    (
        echo "User $i starting..."
        uv run ./yesman.py show
        uv run ./yesman.py ai status
        uv run ./yesman.py status  
        echo "User $i completed"
    ) &
done
wait
```

**검증 포인트**:
- [ ] 모든 명령어가 2초 이내에 응답함
- [ ] 캐시 히트 시 응답 시간이 50% 이상 개선됨
- [ ] 동시 사용자 환경에서 안정적임

## 🚨 알려진 제한사항 및 주의사항

### 환경 요구사항
- **tmux 버전**: 2.0 이상
- **Python 버전**: 3.8 이상  
- **터미널**: 컬러 지원 터미널 (iTerm2, Gnome Terminal 등)
- **운영체제**: macOS, Linux (Windows WSL2 지원)

### 테스트 시 주의사항
- Claude Code 세션이 실행 중인 경우 간섭 가능성
- 대용량 로그 파일 생성 시 디스크 공간 확인
- tmux 세션이 많은 경우 성능 영향 가능
- Git 저장소에서 테스트 시 실제 커밋 발생 주의

## 📊 성공 기준

### 기능적 요구사항
- [ ] 모든 명령어가 오류 없이 실행됨
- [ ] 캐시 시스템이 40% 이상 성능 개선 제공
- [ ] AI 학습 시스템이 의미있는 패턴 학습
- [ ] 자동화 시스템이 프로젝트 이벤트 감지

### 성능 요구사항  
- [ ] 명령어 응답 시간 < 2초
- [ ] 메모리 사용량 < 200MB
- [ ] CPU 사용량 < 10% (평균)
- [ ] 1시간 연속 실행 시 안정성 유지

### 사용성 요구사항
- [ ] 직관적인 UI/UX
- [ ] 명확한 에러 메시지
- [ ] 풍부한 도움말 정보
- [ ] 인터랙티브 요소의 반응성

## 🔧 문제 해결 가이드

### 일반적인 문제들

#### Q: 세션 생성이 실패하는 경우
```bash
# tmux 서버 상태 확인
tmux list-sessions
ps aux | grep tmux

# 설정 파일 문법 확인
python -c "import yaml; yaml.safe_load(open('~/.yesman/projects.yaml'))"
```

#### Q: 캐시가 업데이트되지 않는 경우
```bash
# 캐시 강제 무효화
curl -X POST http://localhost:8001/sessions/cache/invalidate

# 캐시 디렉토리 확인
ls -la ~/.yesman/cache/
```

#### Q: AI 학습이 동작하지 않는 경우
```bash
# 학습 데이터 디렉토리 확인
ls -la ~/.yesman/ai_data/

# 권한 확인
chmod -R 755 ~/.yesman/ai_data/
```

#### Q: 로그 파일이 너무 큰 경우
```bash
# 로그 정리
uv run ./yesman.py logs cleanup --days 7

# 로그 로테이션 설정
uv run ./yesman.py logs configure --max-size 100MB
```

## 📝 테스트 보고서 템플릿

```markdown
# Yesman-Claude 통합 테스트 보고서

**테스트 날짜**: YYYY-MM-DD
**테스터**: [이름]  
**환경**: [OS, Python 버전, tmux 버전]
**테스트 대상 프로젝트**: [프로젝트 설명]

## 테스트 결과 요약
- ✅ 성공: XX개
- ❌ 실패: XX개  
- ⚠️ 경고: XX개

## 상세 테스트 결과
[각 Phase별 결과 기록]

## 성능 측정 결과
- 평균 응답 시간: XXms
- 캐시 히트율: XX%
- 메모리 사용량: XXMB
- CPU 사용량: XX%

## 발견된 이슈
1. [이슈 설명]
2. [이슈 설명]

## 개선 제안
1. [제안 내용]
2. [제안 내용]

## 결론
[전체적인 평가 및 추천 사항]
```

이 가이드를 통해 실제 프로젝트 환경에서 yesman-claude의 모든 기능을 체계적으로 검증할 수 있습니다. 각 단계를 순서대로 진행하면서 문제점을 발견하고 개선점을 식별하세요.