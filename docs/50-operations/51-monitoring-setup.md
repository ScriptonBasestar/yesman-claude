# 모니터링 및 운영 가이드

Yesman-Agent의 모니터링, 로깅, 성능 관리를 위한 완전한 운영 가이드입니다.

## 📚 목차

1. [모니터링 개요](#%EB%AA%A8%EB%8B%88%ED%84%B0%EB%A7%81-%EA%B0%9C%EC%9A%94)
1. [대시보드 설정](#%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C-%EC%84%A4%EC%A0%95)
1. [로깅 시스템](#%EB%A1%9C%EA%B9%85-%EC%8B%9C%EC%8A%A4%ED%85%9C)
1. [성능 모니터링](#%EC%84%B1%EB%8A%A5-%EB%AA%A8%EB%8B%88%ED%84%B0%EB%A7%81)
1. [알림 시스템](#%EC%95%8C%EB%A6%BC-%EC%8B%9C%EC%8A%A4%ED%85%9C)
1. [안전한 정리 워크플로우](#%EC%95%88%EC%A0%84%ED%95%9C-%EC%A0%95%EB%A6%AC-%EC%9B%8C%ED%81%AC%ED%94%8C%EB%A1%9C%EC%9A%B0)
1. [문제 해결](#%EB%AC%B8%EC%A0%9C-%ED%95%B4%EA%B2%B0)

## 🔍 모니터링 개요

### 모니터링 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   데이터 수집   │    │   데이터 처리   │    │   시각화        │
│                 │    │                 │    │                 │
│ - tmux 세션     │───▶│ - 메트릭 집계   │───▶│ - Tauri 대시보드│
│ - 시스템 리소스 │    │ - 건강도 계산   │    │ - 웹 인터페이스 │
│ - Claude 상태   │    │ - 알림 생성     │    │ - CLI 출력      │
│ - 애플리케이션  │    │ - 로그 분석     │    │ - API 엔드포인트│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 주요 컴포넌트

1. **MonitoringIntegration** (`libs/dashboard/monitoring_integration.py`)

   - 핵심 모니터링 대시보드 기능
   - 알림 임계값 관리
   - 성능 메트릭 집계
   - 실시간 대시보드 업데이트

1. **HealthCalculator** (`libs/dashboard/health_calculator.py`)

   - 8개 카테고리 건강도 분석
   - 실시간 상태 계산
   - 트렌드 분석

1. **AsyncLogger** (`libs/logging/async_logger.py`)

   - 고성능 비동기 로깅
   - 압축 및 로테이션
   - 구조화된 로그 처리

## 📊 대시보드 설정

### Tauri 대시보드 실행

```bash
# 개발 모드
./yesman.py dashboard --dev

# 프로덕션 모드
./yesman.py dashboard

# 백그라운드 실행
./yesman.py dashboard --daemon
```

### 웹 인터페이스 접속

- **대시보드 URL**: http://localhost:5173 (개발) / http://localhost:3000 (프로덕션)
- **API 엔드포인트**: http://localhost:10501/api
- **실시간 업데이트**: WebSocket 연결

### 대시보드 기능

#### 1. 세션 모니터링

- 실시간 tmux 세션 상태
- 세션별 리소스 사용량
- 활동 히트맵
- 클릭으로 세션 접속

#### 2. 프로젝트 건강도

- 8개 카테고리 점수
- 실시간 업데이트
- 히스토리 차트
- 권장사항 표시

#### 3. 성능 메트릭

- CPU/메모리 사용량
- 응답 시간
- 캐시 히트율
- 네트워크 연결 수

#### 4. Claude 자동화 상태

- 활성 컨트롤러 목록
- 응답 통계
- 신뢰도 점수
- 오류 로그

### 설정 파일

#### 모니터링 설정 (`~/.scripton/yesman/monitoring.yaml`)

```yaml
monitoring:
  # 업데이트 간격 (초)
  update_interval: 1.0
  
  # 성능 최적화 레벨
  optimization_level: "medium"  # low, medium, high, ultra
  
  # 알림 임계값
  thresholds:
    cpu_usage_warning: 70.0
    cpu_usage_critical: 90.0
    memory_usage_warning: 80.0
    memory_usage_critical: 95.0
    response_time_warning: 1.0
    response_time_critical: 3.0
  
  # 건강도 가중치
  health_weights:
    build: 0.15
    tests: 0.15
    dependencies: 0.12
    security: 0.13
    performance: 0.12
    code_quality: 0.11
    git: 0.12
    documentation: 0.10

# 대시보드 설정
dashboard:
  # 테마 설정
  theme: "auto"  # light, dark, auto
  
  # 자동 새로고침
  auto_refresh: true
  
  # 알림 설정
  notifications:
    enabled: true
    sound: false
    desktop: true
```

## 📝 로깅 시스템

### 로그 구조

```
~/tmp/logs/yesman/
├── main.log                    # 메인 애플리케이션 로그
├── dashboard.log               # 대시보드 로그
├── claude_manager.log          # Claude 관리자 로그
├── session_manager.log         # 세션 관리자 로그
├── api.log                     # API 서버 로그
├── performance.log             # 성능 메트릭 로그
└── archived/                   # 압축된 과거 로그
    ├── main_2025-08-18.log.gz
    └── dashboard_2025-08-18.log.gz
```

### 로그 레벨 설정

```yaml
# yesman.yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  
  # 컴포넌트별 로그 레벨
  components:
    dashboard: "DEBUG"
    claude_manager: "INFO"
    session_manager: "INFO"
    api: "WARNING"
  
  # 로그 로테이션
  rotation:
    max_size: "10MB"
    backup_count: 7
    when: "midnight"
  
  # 압축 설정
  compression:
    enabled: true
    format: "gzip"
```

### 로그 관리 명령어

```bash
# 실시간 로그 모니터링
./yesman.py logs tail -f

# 특정 컴포넌트 로그 확인
./yesman.py logs tail --component=claude_manager

# 로그 분석
./yesman.py logs analyze --days=7

# 로그 정리
./yesman.py logs cleanup --older-than=30

# 로그 압축
./yesman.py logs compress
```

### 구조화된 로깅

```python
import logging
from libs.logging import get_logger

logger = get_logger(__name__)

# 구조화된 로그 메시지
logger.info("Session created", extra={
    "session_name": "my-project",
    "template": "django",
    "windows_count": 3,
    "user_id": "user123"
})

# 성능 로깅
with logger.performance("database_query"):
    # 데이터베이스 쿼리 실행
    pass

# 에러 로깅
try:
    # 위험한 작업
    pass
except Exception as e:
    logger.error("Operation failed", extra={
        "operation": "session_creation",
        "error_type": type(e).__name__,
        "error_message": str(e)
    })
```

## ⚡ 성능 모니터링

### 실시간 성능 메트릭

#### 시스템 메트릭

- CPU 사용률 (프로세스별)
- 메모리 사용량 (RSS/VSZ)
- 디스크 I/O
- 네트워크 트래픽

#### 애플리케이션 메트릭

- 응답 시간
- 처리량 (requests/second)
- 에러율
- 캐시 히트율

#### tmux 메트릭

- 활성 세션 수
- 윈도우/패널 수
- 세션별 CPU/메모리 사용량
- 세션 업타임

### 성능 최적화 설정

```python
from libs.dashboard import get_performance_optimizer

optimizer = get_performance_optimizer()

# 최적화 레벨 설정
optimizer.set_optimization_level("high")

# 성능 프로파일링
with optimizer.profiler.measure("operation_name"):
    # 측정할 코드
    pass

# 성능 리포트 생성
report = optimizer.get_performance_report()
print(f"Average response time: {report.avg_response_time:.3f}s")
```

### 성능 임계값 모니터링

```yaml
# monitoring.yaml - 성능 임계값
performance_thresholds:
  # 응답 시간 (초)
  response_time:
    warning: 1.0
    critical: 3.0
  
  # CPU 사용률 (%)
  cpu_usage:
    warning: 70.0
    critical: 90.0
  
  # 메모리 사용률 (%)
  memory_usage:
    warning: 80.0
    critical: 95.0
  
  # 캐시 히트율 (%)
  cache_hit_rate:
    warning: 70.0  # 70% 미만 시 경고
    critical: 50.0  # 50% 미만 시 위험
```

## 🚨 알림 시스템

### 알림 채널 설정

```yaml
# monitoring.yaml - 알림 설정
notifications:
  channels:
    - type: "desktop"
      enabled: true
      urgency: "normal"  # low, normal, critical
    
    - type: "email"
      enabled: false
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      username: "alerts@example.com"
      recipients: ["admin@example.com"]
    
    - type: "slack"
      enabled: false
      webhook_url: "https://hooks.slack.com/..."
      channel: "#alerts"
    
    - type: "log"
      enabled: true
      log_level: "WARNING"
```

### 알림 규칙

```yaml
alert_rules:
  # CPU 사용률 알림
  - name: "high_cpu_usage"
    condition: "cpu_usage > 80"
    duration: "5m"  # 5분 지속 시 알림
    severity: "warning"
    message: "High CPU usage detected: {cpu_usage}%"
  
  # 세션 생성 실패
  - name: "session_creation_failed"
    condition: "session_creation_error_count > 0"
    duration: "0s"  # 즉시 알림
    severity: "critical"
    message: "Session creation failed: {error_message}"
  
  # Claude 컨트롤러 중지
  - name: "claude_controller_stopped"
    condition: "claude_controller_status == 'stopped'"
    duration: "30s"
    severity: "warning"
    message: "Claude controller stopped for session: {session_name}"
```

### 알림 API

```python
from libs.dashboard.notifications import NotificationManager

notifications = NotificationManager()

# 알림 전송
notifications.send_alert(
    severity="warning",
    title="High CPU Usage",
    message="CPU usage is 85%, above threshold of 80%",
    context={
        "cpu_usage": 85.0,
        "threshold": 80.0,
        "session": "my-project"
    }
)

# 알림 기록 조회
alerts = notifications.get_recent_alerts(hours=24)
for alert in alerts:
    print(f"{alert.timestamp}: {alert.title}")
```

## 🛡️ 안전한 정리 워크플로우

### 배경

2025년 8월 13일 `git clean -dfx` 사고로 인해 중요한 Tauri 대시보드 파일들이 삭제되었습니다. 이를 방지하기 위한 안전한 정리 프로세스입니다.

### 예방 조치

#### 1. 안전한 Git 정리 스크립트

```bash
#!/bin/bash
# scripts/safe_cleanup.sh

echo "🧹 Starting safe cleanup process..."

# 1. 중요 파일 백업 확인
echo "📋 Checking critical files..."
CRITICAL_PATHS=(
    "tauri-dashboard/src/lib"
    "tauri-dashboard/src/routes"
    "tauri-dashboard/static"
    "tauri-dashboard/package.json"
    "tauri-dashboard/tsconfig.json"
    "libs/core"
    "libs/dashboard"
    "commands"
)

for path in "${CRITICAL_PATHS[@]}"; do
    if [ ! -e "$path" ]; then
        echo "❌ Critical path missing: $path"
        echo "⚠️  Cleanup aborted for safety"
        exit 1
    fi
done

echo "✅ All critical files present"

# 2. 안전한 정리 (단계별)
echo "🗂️  Cleaning build artifacts..."
rm -rf node_modules/.cache
rm -rf .next
rm -rf dist
rm -rf build

echo "🧽 Cleaning temporary files..."
find . -name "*.tmp" -delete
find . -name "*.log" -type f -mtime +7 -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

echo "✅ Safe cleanup completed"
```

#### 2. Git 후크 설정

```bash
# .git/hooks/pre-clean (실행 권한 필요)
#!/bin/bash

echo "⚠️  WARNING: You're about to run git clean"
echo "This could delete important files!"
echo ""
echo "Use './scripts/safe_cleanup.sh' instead for safe cleanup"
echo ""
read -p "Continue with git clean? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 1
fi
```

#### 3. 개선된 .gitignore

```gitignore
# =============================================================================
# TAURI DASHBOARD PROTECTION
# =============================================================================

# NEVER ignore these critical directories
!tauri-dashboard/src/lib/
!tauri-dashboard/src/lib/**
!tauri-dashboard/src/routes/
!tauri-dashboard/static/
!tauri-dashboard/tests/

# NEVER ignore these critical files
!tauri-dashboard/package.json
!tauri-dashboard/tsconfig.json
!tauri-dashboard/vite.config.ts

# =============================================================================
# SAFE PATTERNS
# =============================================================================

# Python build artifacts (safe patterns)
**/__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib64/  # Note: not lib/ which would catch tauri-dashboard/src/lib/
parts/
sdist/
var/
wheels/

# Node.js (safe patterns)
node_modules/
*.tgz
*.log
npm-debug.log*
.npm
.node_repl_history
```

### 복구 프로세스

#### 1. 파일 손실 감지

```bash
#!/bin/bash
# scripts/check_integrity.sh

echo "🔍 Checking file system integrity..."

REQUIRED_FILES=(
    "tauri-dashboard/src/lib/components/layout/Sidebar.svelte"
    "tauri-dashboard/src/lib/components/dashboard/SessionList.svelte"
    "tauri-dashboard/src/routes/+layout.svelte"
    "tauri-dashboard/static/favicon.png"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing: $file"
        echo "🚨 File system integrity compromised!"
        exit 1
    fi
done

echo "✅ File system integrity OK"
```

#### 2. 자동 복구

```bash
# Git에서 복구
git checkout HEAD -- tauri-dashboard/src/lib/
git checkout HEAD -- tauri-dashboard/src/routes/
git checkout HEAD -- tauri-dashboard/static/

# 의존성 재설치
cd tauri-dashboard && pnpm install

# 빌드 재실행
pnpm run build
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 대시보드 연결 불가

**증상**: 대시보드가 로드되지 않거나 API 연결 실패

**해결책**:

```bash
# API 서버 상태 확인
curl http://localhost:10501/api/health

# 프로세스 확인
ps aux | grep uvicorn

# 수동 재시작
./yesman.py dashboard --restart
```

#### 2. 성능 저하

**증상**: 대시보드 응답 속도 저하

**해결책**:

```bash
# 성능 메트릭 확인
./yesman.py status --performance

# 캐시 정리
./yesman.py cache clear

# 최적화 레벨 조정
./yesman.py config set performance.optimization_level high
```

#### 3. 로그 파일 크기 문제

**증상**: 로그 파일이 너무 커짐

**해결책**:

```bash
# 로그 압축
./yesman.py logs compress

# 오래된 로그 정리
./yesman.py logs cleanup --older-than=7

# 로그 레벨 조정
./yesman.py config set logging.level WARNING
```

### 디버깅 도구

#### 1. 진단 스크립트

```bash
# 전체 시스템 진단
./scripts/diagnose.sh

# 성능 프로파일링
./scripts/profile_performance.sh

# 연결 테스트
./scripts/test_connectivity.sh
```

#### 2. 상세 로깅 활성화

```bash
# 디버그 모드 활성화
export YESMAN_DEBUG=1
export YESMAN_LOG_LEVEL=DEBUG

# 특정 컴포넌트 디버깅
./yesman.py dashboard --debug --component=session_manager
```

#### 3. 건강도 체크

```bash
# 전체 시스템 건강도
./yesman.py health check

# 개별 컴포넌트 체크
./yesman.py health check --component=dashboard
./yesman.py health check --component=api
./yesman.py health check --component=claude_manager
```

______________________________________________________________________

**마지막 업데이트**: 2025-08-19\
**문서 버전**: v2.0\
**지원 플랫폼**: Linux, macOS, Windows (WSL2)
