# DEFINITION.md

## 프로젝트 정의

**Yesman-Claude**는 Claude Code와의 상호작용을 자동화하고 개발 환경을 통합 관리하는 AI 기반 개발 자동화 플랫폼입니다.

## 핵심 목표

### 주요 가치

1. **완전 자동화된 AI 코딩 워크플로**: Claude Code의 모든 대화형 프롬프트를 자동 처리
1. **무중단 개발 환경**: tmux 세션 기반의 지속적인 개발 환경 제공
1. **지능형 학습 시스템**: 사용자 패턴을 학습하여 점진적으로 개선되는 응답 시스템
1. **컨텍스트 인식 자동화**: 개발 상황을 감지하고 적절한 워크플로 자동 실행

### 해결하는 문제

- Claude Code 사용 시 반복적인 수동 응답 제거
- 복잡한 개발 환경 설정의 자동화
- 프로젝트별 템플릿 기반 일관된 환경 구성
- 실시간 개발 상태 모니터링 및 제어

## 필수 기능

### 1. Claude Code 자동화 엔진

```
핵심: libs/core/claude_manager.py
```

- **고급 프롬프트 인식**: 정규식 기반 trust 프롬프트, 선택 메뉴, Y/N 질문 감지
- **자동 응답 시스템**: 사용자 개입 없이 프롬프트에 자동 응답
- **패턴 기반 학습**: 사용자 행동 패턴을 학습하여 응답 정확도 향상
- **신뢰도 점수**: 머신러닝 기반 응답 신뢰도 계산

### 2. 세션 관리 시스템

```
핵심: libs/core/session_manager.py
```

- **YAML 템플릿 기반**: 선언적 세션 정의 및 변수 치환
- **스마트 템플릿**: 조건부 명령 실행 (의존성 설치 등)
- **계층적 설정**: 글로벌 → 템플릿 → 프로젝트 → 로컬 오버라이드
- **실시간 세션 모니터링**: tmux 세션, 윈도우, 패널 상태 추적

### 3. 멀티 인터페이스 대시보드

```
핵심: libs/dashboard/, api/, tauri-dashboard/
```

- **3중 인터페이스**: TUI(터미널), Web(브라우저), Native(데스크톱)
- **실시간 모니터링**: 세션 활동, 성능 지표, 헬스 상태
- **인터랙티브 제어**: 대시보드에서 직접 세션 제어 및 관리
- **성능 최적화**: 스마트 캐싱으로 70% 성능 향상

### 4. AI 학습 시스템

```
핵심: libs/ai/
```

- **적응형 응답**: 사용자 패턴 학습 및 응답 개선
- **신뢰도 임계값**: 프롬프트 유형별 조정 가능한 신뢰도 레벨
- **응답 분석**: 상세 통계 및 트렌드 분석
- **패턴 분류**: 다양한 프롬프트 유형 자동 분류

### 5. 컨텍스트 인식 자동화

```
핵심: libs/automation/
```

- **개발 이벤트 감지**: git 커밋, 테스트 실패, 빌드 이벤트 모니터링
- **워크플로 체인**: 테스트 → 빌드 → 배포 자동화 시퀀스
- **실시간 트리거**: 8가지 컨텍스트 유형으로 포괄적 프로젝트 모니터링

## 기술 스택

### 백엔드 (Python 3.11+)

- **CLI**: Click, Rich
- **세션**: tmuxp, libtmux
- **자동화**: pexpect, psutil
- **API**: FastAPI, uvicorn
- **AI**: 커스텀 학습 알고리즘

### 프론트엔드 (TypeScript)

- **프레임워크**: SvelteKit 2.x
- **UI**: Tailwind CSS + DaisyUI
- **빌드**: Vite, PostCSS
- **시각화**: Chart.js

### 네이티브 (Rust)

- **프레임워크**: Tauri 1.5
- **런타임**: Tokio
- **통합**: 시스템 알림, 트레이

## 아키텍처 핵심

### 명령 구조

```bash
# 기본 세션 관리
./yesman.py up          # 모든 세션 생성
./yesman.py down        # 모든 세션 종료
./yesman.py show        # 실행 중인 세션 표시

# 대시보드 인터페이스
./yesman.py dash run -i web     # 웹 대시보드
./yesman.py dash run -i tauri   # 네이티브 앱
./yesman.py dash run -i tui     # 터미널 UI

# AI 학습 시스템
./yesman.py ai status           # AI 상태 확인
./yesman.py ai config -t 0.8    # 신뢰도 설정

# 컨텍스트 자동화
./yesman.py automate monitor    # 컨텍스트 모니터링
```

### 설정 계층

```
$HOME/.scripton/yesman/yesman.yaml     # 글로벌 설정
$HOME/.scripton/yesman/projects.yaml   # 프로젝트 정의
$HOME/.scripton/yesman/templates/      # 재사용 템플릿
./.scripton/yesman/                    # 로컬 오버라이드
```

### 템플릿 예시

```yaml
session_name: "{{ session_name }}"
start_directory: "{{ start_directory }}"
before_script: uv sync
windows:
  - window_name: 개발서버
    layout: even-horizontal
    panes:
      - claude --dangerously-skip-permissions
      - uv run ./manage.py runserver
      - htop
```

## 핵심 컴포넌트

### 1. 자동화 엔진

- **DashboardController**: 메인 오케스트레이션 컨트롤러
- **ContentCollector**: tmux 패널 콘텐츠 수집
- **PromptDetector**: 정교한 프롬프트 인식 시스템
- **AdaptiveResponse**: ML 기반 자동 응답 생성

### 2. 대시보드 시스템

- **TUIRenderer**: Rich 기반 터미널 인터페이스
- **FastAPI**: REST API 서버
- **SvelteKit**: 반응형 웹 인터페이스
- **Tauri**: 네이티브 데스크톱 앱

### 3. 모니터링 시스템

- **HealthCalculator**: 8카테고리 프로젝트 헬스 평가
- **PerformanceOptimizer**: 지능형 캐싱 및 최적화
- **AsyncLogger**: 고성능 비동기 로깅

## 구현 상태

### ✅ 완료된 기능

- 완전한 CLI 명령 세트 (11개 명령 그룹)
- 멀티 인터페이스 대시보드
- AI 기반 적응형 응답 시스템
- 컨텍스트 인식 자동화 엔진
- 스마트 세션 템플릿 시스템
- 포괄적인 REST API
- 네이티브 데스크톱 애플리케이션

### 🚀 고급 기능

- 머신러닝 기반 패턴 인식
- 실시간 성능 최적화
- 포괄적인 로깅 및 분석
- 멀티 에이전트 협업 프레임워크
- Chrome DevTools 통합

## 성공 기준

1. **자동화율**: Claude Code 프롬프트 95% 이상 자동 처리
1. **성능**: tmux 서버 부하 70% 감소
1. **안정성**: 24시간 무중단 세션 관리
1. **학습 효율**: 사용자 패턴 학습으로 90% 이상 정확도
1. **확장성**: 다중 프로젝트 동시 관리 지원

## 향후 확장 방향

- 다른 AI 어시스턴트 지원 확장
- 클러스터 환경에서의 분산 세션 관리
- 고급 워크플로 자동화 엔진
- 팀 협업 기능 및 공유 템플릿
- 프로젝트 헬스 예측 분석
