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

### Phase 11: 보안 테스트

#### 11.1 API 인증 및 권한 테스트

```bash
# 1. API 서버 시작
cd api && python -m uvicorn main:app --reload --port 8001 &
API_PID=$!

# 2. 인증 없이 API 접근 시도
curl -X GET http://localhost:8001/sessions
curl -X POST http://localhost:8001/sessions/test-project/setup
curl -X DELETE http://localhost:8001/sessions/teardown-all

# 3. 잘못된 입력으로 API 공격 시도
curl -X POST http://localhost:8001/sessions/../../etc/passwd/setup
curl -X POST http://localhost:8001/sessions/test%00null/setup
curl -X POST http://localhost:8001/sessions/$(echo -n "'; DROP TABLE sessions; --")/setup

# 4. API 서버 종료
kill $API_PID
```

**검증 포인트**:

- [ ] 인증되지 않은 요청이 적절히 처리됨
- [ ] 경로 탐색 공격이 차단됨
- [ ] SQL 인젝션 시도가 무효화됨
- [ ] 에러 메시지에 민감한 정보가 노출되지 않음

#### 11.2 Tmux 세션 격리 테스트

```bash
# 1. 다중 사용자 시뮬레이션
# 사용자 1 세션 생성
YESMAN_USER=user1 uv run ./yesman.py setup

# 사용자 2가 사용자 1의 세션에 접근 시도
YESMAN_USER=user2 uv run ./yesman.py enter yesman-test

# 2. 세션 이름 충돌 테스트
uv run ./yesman.py setup
uv run ./yesman.py setup  # 동일한 세션 이름으로 재생성 시도

# 3. 권한 에스컬레이션 방지 테스트
echo "sudo rm -rf /" > malicious.sh
chmod +x malicious.sh
# projects.yaml에 악의적인 명령 주입 시도
cat > ~/.yesman/projects-test.yaml << 'EOF'
sessions:
  malicious:
    override:
      windows:
        - window_name: "exploit"
          panes:
            - shell_command: ["./malicious.sh"]
EOF
```

**검증 포인트**:

- [ ] 다른 사용자의 세션에 접근할 수 없음
- [ ] 세션 이름 충돌이 적절히 처리됨
- [ ] 악의적인 명령이 실행되지 않음
- [ ] 권한 상승이 발생하지 않음

#### 11.3 민감 정보 보호 테스트

```bash
# 1. 환경 변수에 민감 정보 설정
export SECRET_API_KEY="super-secret-key-12345"
export DATABASE_PASSWORD="db-password-xyz"

# 2. 로그에 민감 정보 노출 확인
uv run ./yesman.py logs configure --output-dir ~/.yesman/logs --format json
uv run ./yesman.py setup
uv run ./yesman.py ai predict "Enter API key:" --context "api_context"

# 3. 로그 파일에서 민감 정보 검색
grep -r "SECRET_API_KEY\|DATABASE_PASSWORD\|super-secret\|db-password" ~/.yesman/logs/

# 4. 캐시에 민감 정보 저장 확인
find ~/.yesman -name "*.cache" -o -name "*.json" | xargs grep -l "password\|secret\|key"
```

**검증 포인트**:

- [ ] 환경 변수가 로그에 노출되지 않음
- [ ] 패스워드가 평문으로 저장되지 않음
- [ ] 캐시 파일에 민감 정보가 없음
- [ ] AI 학습 데이터에 민감 정보가 포함되지 않음

### Phase 12: 카오스 엔지니어링 테스트

#### 12.1 네트워크 장애 시뮬레이션

```bash
# 1. 네트워크 지연 시뮬레이션 (macOS)
# sudo dnctl pipe 1 config delay 1000ms plr 0.1
# sudo pfctl -f /etc/pf.conf

# Linux에서는 tc 사용
# sudo tc qdisc add dev lo root netem delay 1000ms loss 10%

# 2. API 서버 연결 끊김 테스트
cd api && python -m uvicorn main:app --port 8001 &
API_PID=$!
sleep 5

# API 서버 강제 종료
kill -9 $API_PID

# 클라이언트 동작 확인
uv run ./yesman.py show
uv run ./yesman.py status

# 3. 간헐적 연결 실패 시뮬레이션
for i in {1..10}; do
    if [ $((i % 3)) -eq 0 ]; then
        # API 서버 재시작
        cd api && python -m uvicorn main:app --port 8001 &
        API_PID=$!
    else
        # API 서버 종료
        kill -9 $API_PID 2>/dev/null
    fi
    
    uv run ./yesman.py show
    sleep 2
done
```

**검증 포인트**:

- [ ] 네트워크 장애 시 graceful degradation
- [ ] 재시도 메커니즘이 작동함
- [ ] 오프라인 모드로 전환됨
- [ ] 연결 복구 시 자동 재연결됨

#### 12.2 프로세스 강제 종료 복구 테스트

```bash
# 1. Claude 프로세스 강제 종료
uv run ./yesman.py setup
tmux send-keys -t yesman-test:claude "claude" Enter
sleep 5

# Claude 프로세스 찾아서 강제 종료
CLAUDE_PID=$(pgrep -f "claude")
kill -9 $CLAUDE_PID

# 자동 복구 확인
uv run ./yesman.py status
sleep 10
uv run ./yesman.py status

# 2. 모니터링 프로세스 강제 종료
uv run ./yesman.py automate monitor --interval 5 &
MONITOR_PID=$!
sleep 10
kill -9 $MONITOR_PID

# 상태 확인
uv run ./yesman.py automate status
```

**검증 포인트**:

- [ ] Claude 프로세스가 자동으로 재시작됨
- [ ] 세션 상태가 올바르게 복구됨
- [ ] 모니터링이 중단되어도 시스템이 안정적임
- [ ] 복구 과정이 로그에 기록됨

#### 12.3 리소스 부족 상황 테스트

```bash
# 1. 디스크 공간 부족 시뮬레이션
# 대용량 더미 파일 생성
dd if=/dev/zero of=~/.yesman/logs/dummy_large.log bs=1M count=1000

# 로그 생성 시도
uv run ./yesman.py logs configure --output-dir ~/.yesman/logs
for i in {1..100}; do
    uv run ./yesman.py show
done

# 2. 메모리 부족 시뮬레이션
# 많은 수의 세션 동시 생성
for i in {1..20}; do
    cat > ~/.yesman/projects-stress-$i.yaml << EOF
sessions:
  stress-test-$i:
    override:
      windows:
        - window_name: "main"
          panes:
            - shell_command: ["yes"]
EOF
    uv run ./yesman.py setup -f ~/.yesman/projects-stress-$i.yaml &
done

# 메모리 사용량 모니터링
ps aux | grep yesman
top -l 1 | grep yesman

# 3. CPU 과부하 테스트
for i in {1..10}; do
    uv run ./yesman.py browse --update-interval 0.1 &
done

# CPU 사용률 확인
top -l 1 | head -20
```

**검증 포인트**:

- [ ] 디스크 공간 부족 시 적절한 에러 메시지
- [ ] 로그 로테이션이 작동함
- [ ] 메모리 부족 시 graceful degradation
- [ ] CPU 과부하 시에도 응답성 유지

### Phase 13: 실시간 통신 테스트

#### 13.1 WebSocket 연결 안정성 테스트

```bash
# 1. WebSocket 테스트 클라이언트 작성
cat > test_websocket.py << 'EOF'
import asyncio
import websockets
import json
import time

async def test_websocket_stability():
    uri = "ws://localhost:8001/ws"
    connection_count = 0
    error_count = 0
    
    while connection_count < 100:
        try:
            async with websockets.connect(uri) as websocket:
                connection_count += 1
                print(f"Connection {connection_count} established")
                
                # 메시지 송수신 테스트
                await websocket.send(json.dumps({"type": "ping"}))
                response = await websocket.recv()
                
                # 의도적으로 연결 유지
                await asyncio.sleep(10)
                
        except Exception as e:
            error_count += 1
            print(f"Error: {e}")
            
    print(f"Total connections: {connection_count}, Errors: {error_count}")

asyncio.run(test_websocket_stability())
EOF

python test_websocket.py
```

**검증 포인트**:

- [ ] 장시간 WebSocket 연결이 유지됨
- [ ] 연결 끊김 후 자동 재연결됨
- [ ] 메모리 누수가 없음
- [ ] 동시 연결 수 제한이 적절함

#### 13.2 메시지 순서 보장 테스트

```bash
# 1. 다중 메시지 전송 테스트
cat > test_message_order.py << 'EOF'
import asyncio
import aiohttp
import json

async def send_rapid_messages():
    async with aiohttp.ClientSession() as session:
        messages = []
        for i in range(100):
            data = {"id": i, "timestamp": time.time()}
            async with session.post('http://localhost:8001/api/message', json=data) as resp:
                result = await resp.json()
                messages.append(result)
        
        # 순서 검증
        for i in range(1, len(messages)):
            if messages[i]["id"] != messages[i-1]["id"] + 1:
                print(f"Order violation at index {i}")
                
asyncio.run(send_rapid_messages())
EOF

python test_message_order.py
```

**검증 포인트**:

- [ ] 메시지 순서가 보장됨
- [ ] 동시 요청에서도 순서 유지
- [ ] 메시지 누락이 없음
- [ ] 중복 메시지가 없음

### Phase 14: AI/ML 시스템 고급 테스트

#### 14.1 패턴 분류 정확도 테스트

```bash
# 1. 테스트 데이터셋 생성
cat > test_prompts.json << 'EOF'
{
  "test_cases": [
    {
      "prompt": "Do you want to overwrite the file? (y/n)",
      "expected_type": "yes_no",
      "expected_response": "y"
    },
    {
      "prompt": "Select an option:\n1) Create new\n2) Update existing\n3) Delete",
      "expected_type": "numbered_selection",
      "expected_response": "1"
    },
    {
      "prompt": "Trust this workspace? (yes/no)",
      "expected_type": "trust_confirmation",
      "expected_response": "yes"
    }
  ]
}
EOF

# 2. 정확도 측정 스크립트
cat > test_ai_accuracy.py << 'EOF'
import json
import subprocess

def test_ai_predictions():
    with open('test_prompts.json') as f:
        test_data = json.load(f)
    
    correct = 0
    total = 0
    
    for case in test_data['test_cases']:
        # AI 예측 실행
        result = subprocess.run([
            'uv', 'run', './yesman.py', 'ai', 'predict', 
            case['prompt']
        ], capture_output=True, text=True)
        
        # 결과 파싱 및 비교
        # ... 정확도 계산 로직
        
    print(f"Accuracy: {correct/total*100:.2f}%")

test_ai_predictions()
EOF

python test_ai_accuracy.py
```

**검증 포인트**:

- [ ] 분류 정확도 > 90%
- [ ] 각 프롬프트 타입별 정확도 측정
- [ ] False positive/negative 비율
- [ ] 신뢰도 점수의 신뢰성

#### 14.2 모델 드리프트 감지 테스트

```bash
# 1. 시간 경과 시뮬레이션
# 과거 데이터로 학습
uv run ./yesman.py ai config --threshold 0.7

# 다양한 패턴으로 학습 데이터 생성
for i in {1..100}; do
    if [ $((i % 2)) -eq 0 ]; then
        # 일반적인 패턴
        echo "y" | uv run ./yesman.py ai predict "Continue? (y/n)"
    else
        # 비정상적인 패턴
        echo "n" | uv run ./yesman.py ai predict "Continue? (y/n)"
    fi
done

# 2. 성능 변화 측정
uv run ./yesman.py ai status
uv run ./yesman.py ai export --output ai_metrics_before.json

# 시간 경과 후 (새로운 패턴 도입)
sleep 3600  # 또는 시뮬레이션

uv run ./yesman.py ai export --output ai_metrics_after.json

# 드리프트 분석
python -c "
import json
with open('ai_metrics_before.json') as f1, open('ai_metrics_after.json') as f2:
    before = json.load(f1)
    after = json.load(f2)
    # 드리프트 계산 로직
"
```

**검증 포인트**:

- [ ] 성능 저하가 감지됨
- [ ] 드리프트 알림이 발생함
- [ ] 재학습 권장사항이 제시됨
- [ ] 성능 지표가 추적됨

#### 14.3 개인정보 보호 테스트

```bash
# 1. 민감한 정보가 포함된 프롬프트 테스트
SENSITIVE_PROMPTS=(
    "Enter password for user john.doe@example.com:"
    "API key (sk-1234567890abcdef):"
    "Credit card number (4111-1111-1111-1111):"
)

for prompt in "${SENSITIVE_PROMPTS[@]}"; do
    uv run ./yesman.py ai predict "$prompt"
done

# 2. 학습 데이터에서 민감 정보 확인
find ~/.yesman/ai_data -type f -name "*.json" | xargs grep -E "(password|api[_-]key|credit[_-]card|ssn|email)"

# 3. 익명화 확인
uv run ./yesman.py ai export --output ai_export.json
python -c "
import json
with open('ai_export.json') as f:
    data = json.load(f)
    # PII 검사 로직
"
```

**검증 포인트**:

- [ ] 민감 정보가 마스킹됨
- [ ] 학습 데이터에 PII가 없음
- [ ] 익명화가 적절히 수행됨
- [ ] GDPR 준수 확인

### Phase 15: 관찰성(Observability) 테스트

#### 15.1 분산 추적 테스트

```bash
# 1. 추적 ID 전파 확인
# 요청에 추적 ID 추가
curl -H "X-Trace-ID: test-trace-123" http://localhost:8001/sessions

# 로그에서 추적 ID 확인
grep "test-trace-123" ~/.yesman/logs/*.log

# 2. 요청 경로 추적
cat > trace_request.py << 'EOF'
import time
import requests

trace_id = f"trace-{int(time.time())}"
headers = {"X-Trace-ID": trace_id}

# API → SessionManager → TmuxManager → Cache
response = requests.get("http://localhost:8001/sessions", headers=headers)

# 각 컴포넌트 로그에서 추적
components = ["api", "session_manager", "tmux_manager", "cache"]
for comp in components:
    log_file = f"~/.yesman/logs/{comp}.log"
    # grep trace_id log_file
EOF

python trace_request.py
```

**검증 포인트**:

- [ ] 추적 ID가 모든 컴포넌트에 전파됨
- [ ] 요청 경로를 재구성할 수 있음
- [ ] 지연 시간이 각 단계별로 측정됨
- [ ] 오류 발생 지점을 정확히 파악 가능

#### 15.2 메트릭 수집 정확성 테스트

```bash
# 1. 메트릭 엔드포인트 확인
curl http://localhost:8001/metrics

# 2. 부하 생성 및 메트릭 변화 관찰
# 초기 메트릭 저장
curl -s http://localhost:8001/metrics > metrics_before.txt

# 부하 생성
for i in {1..100}; do
    uv run ./yesman.py show &
done
wait

# 변경된 메트릭 확인
curl -s http://localhost:8001/metrics > metrics_after.txt

# 메트릭 비교
diff metrics_before.txt metrics_after.txt
```

**검증 포인트**:

- [ ] 요청 수가 정확히 카운트됨
- [ ] 응답 시간 분포가 올바름
- [ ] 에러율이 정확히 계산됨
- [ ] 리소스 사용량이 실제와 일치함

#### 15.3 알람 시스템 테스트

```bash
# 1. 임계값 설정
cat > alert_config.yaml << 'EOF'
alerts:
  - name: high_error_rate
    condition: error_rate > 0.1
    action: notify
  - name: slow_response
    condition: p95_latency > 2000
    action: log
  - name: memory_usage
    condition: memory_mb > 500
    action: alert
EOF

# 2. 알람 트리거 시뮬레이션
# 높은 에러율 생성
for i in {1..20}; do
    curl -X POST http://localhost:8001/invalid-endpoint
done

# 느린 응답 시뮬레이션
curl -X POST http://localhost:8001/sessions/slow-test/setup

# 3. 알람 발생 확인
grep "ALERT" ~/.yesman/logs/alerts.log
```

**검증 포인트**:

- [ ] 임계값 초과 시 알람 발생
- [ ] 알람이 중복되지 않음
- [ ] 복구 시 알람 해제됨
- [ ] 알람 히스토리가 기록됨

### Phase 16: 테스트 자동화 인프라

#### 16.1 CI/CD 파이프라인 구성

```yaml
# .github/workflows/integration-test.yml
name: Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # 매일 새벽 2시

jobs:
  integration-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12, 3.13]
        
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Install tmux
      run: sudo apt-get install -y tmux
    
    - name: Run integration tests
      run: |
        # 전체 통합 테스트 실행
        ./scripts/run-integration-tests.sh
      
    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: test-results-${{ matrix.python-version }}
        path: test-results/
    
    - name: Generate coverage report
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

#### 16.2 테스트 데이터 관리

```bash
# 테스트 데이터 구조 생성
mkdir -p test-data/{fixtures,generators,snapshots}

# 고정 테스트 데이터
cat > test-data/fixtures/test_sessions.yaml << 'EOF'
test_sessions:
  - name: basic_session
    windows: 2
    panes_per_window: 2
  - name: complex_session
    windows: 5
    panes_per_window: 4
EOF

# 동적 데이터 생성기
cat > test-data/generators/generate_prompts.py << 'EOF'
import random
import json

def generate_test_prompts(count=100):
    prompt_templates = [
        "Do you want to {action}? (y/n)",
        "Select an option: 1) {opt1} 2) {opt2} 3) {opt3}",
        "Continue with {operation}? (yes/no)"
    ]
    
    prompts = []
    for _ in range(count):
        template = random.choice(prompt_templates)
        # ... 동적 생성 로직
        
    return prompts
EOF

# UI 스냅샷 저장
mkdir -p test-data/snapshots/ui
# 각 명령어 실행 결과를 스냅샷으로 저장
```

#### 16.3 테스트 환경 격리

```bash
# Docker 기반 테스트 환경
cat > Dockerfile.test << 'EOF'
FROM python:3.12-slim

# tmux 및 의존성 설치
RUN apt-get update && apt-get install -y \
    tmux \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 테스트 사용자 생성
RUN useradd -m -s /bin/bash testuser

# 애플리케이션 복사
COPY . /app
WORKDIR /app

# 의존성 설치
RUN pip install -e .
RUN pip install pytest pytest-asyncio pytest-cov

# 테스트 스크립트
COPY scripts/run-tests.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/run-tests.sh

USER testuser
CMD ["/usr/local/bin/run-tests.sh"]
EOF

# Docker Compose 구성
cat > docker-compose.test.yml << 'EOF'
version: '3.8'

services:
  yesman-test:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - ./test-results:/app/test-results
    environment:
      - PYTHONPATH=/app
      - TEST_ENV=docker
    networks:
      - test-network

  api-test:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    networks:
      - test-network

networks:
  test-network:
    driver: bridge
EOF

# 테스트 실행 스크립트
cat > scripts/run-integration-tests.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting integration tests..."

# Docker 환경 시작
docker-compose -f docker-compose.test.yml up -d

# 테스트 실행
docker-compose -f docker-compose.test.yml exec yesman-test pytest tests/integration/

# 결과 수집
docker-compose -f docker-compose.test.yml logs > test-results/docker-logs.txt

# 정리
docker-compose -f docker-compose.test.yml down

echo "Integration tests completed!"
EOF

chmod +x scripts/run-integration-tests.sh
```

## 🎯 향상된 테스트 전략

### 테스트 우선순위 매트릭스

| 테스트 영역       | 중요도  | 자동화 가능성 | 실행 빈도 |
| ----------------- | ------- | ------------- | --------- |
| 보안 테스트       | 🔴 높음 | ✅ 가능       | 매 커밋   |
| 카오스 엔지니어링 | 🟡 중간 | ⚠️ 부분적     | 주간      |
| 성능 회귀         | 🟡 중간 | ✅ 가능       | 매일      |
| AI/ML 정확도      | 🔴 높음 | ✅ 가능       | 매 릴리즈 |
| 관찰성            | 🟡 중간 | ✅ 가능       | 매일      |

### 테스트 실행 체크리스트

- [ ] 단위 테스트 통과
- [ ] 통합 테스트 Phase 1-10 완료
- [ ] 보안 취약점 스캔 통과
- [ ] 성능 벤치마크 기준 충족
- [ ] AI 모델 정확도 > 90%
- [ ] 카오스 테스트 통과
- [ ] 메모리 누수 없음
- [ ] 문서 업데이트 완료

## 📊 테스트 메트릭 대시보드

```bash
# 테스트 결과 집계 스크립트
cat > scripts/test-metrics.py << 'EOF'
import json
import glob
from datetime import datetime

def generate_test_report():
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "test_coverage": calculate_coverage(),
        "security_score": calculate_security_score(),
        "performance_metrics": get_performance_metrics(),
        "ai_accuracy": get_ai_accuracy(),
        "chaos_test_results": get_chaos_results()
    }
    
    # HTML 리포트 생성
    generate_html_report(metrics)
    
    # Slack 알림
    if metrics["test_coverage"] < 80:
        send_slack_alert("Test coverage below threshold!")

generate_test_report()
EOF
```

이 가이드를 통해 실제 프로젝트 환경에서 yesman-claude의 모든 기능을 체계적으로 검증할 수 있습니다. 각 단계를 순서대로 진행하면서 문제점을 발견하고 개선점을 식별하세요.
