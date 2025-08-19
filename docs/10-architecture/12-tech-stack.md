# Technology Stack

Yesman-Agent 프로젝트의 전체 기술 스택 문서입니다.

## 📚 목차

1. [프로젝트 개요](#%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EA%B0%9C%EC%9A%94)
1. [프로그래밍 언어](#%ED%94%84%EB%A1%9C%EA%B7%B8%EB%9E%98%EB%B0%8D-%EC%96%B8%EC%96%B4)
1. [백엔드 기술 스택](#%EB%B0%B1%EC%97%94%EB%93%9C-%EA%B8%B0%EC%88%A0-%EC%8A%A4%ED%83%9D)
1. [프론트엔드 기술 스택](#%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C-%EA%B8%B0%EC%88%A0-%EC%8A%A4%ED%83%9D)
1. [Rust 의존성](#rust-%EC%9D%98%EC%A1%B4%EC%84%B1)
1. [개발 도구 및 빌드 시스템](#%EA%B0%9C%EB%B0%9C-%EB%8F%84%EA%B5%AC-%EB%B0%8F-%EB%B9%8C%EB%93%9C-%EC%8B%9C%EC%8A%A4%ED%85%9C)
1. [API 기술 스택](#api-%EA%B8%B0%EC%88%A0-%EC%8A%A4%ED%83%9D)
1. [아키텍처 컴포넌트](#%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98-%EC%BB%B4%ED%8F%AC%EB%84%8C%ED%8A%B8)

## 🎯 프로젝트 개요

Yesman-Agent는 Claude Code 자동화 및 모니터링을 위한 멀티 기술 스택 프로젝트입니다.

## 💻 프로그래밍 언어

- **Python** (>=3.11): 메인 백엔드 언어, CLI 도구 및 핵심 자동화 로직
- **JavaScript/TypeScript**: Tauri 대시보드 프론트엔드 개발
- **Rust**: 네이티브 데스크톱 애플리케이션 백엔드 (Tauri 프레임워크)
- **HTML/CSS**: 프론트엔드 마크업 및 스타일링

## 🐍 백엔드 기술 스택

### Python 핵심 의존성

```toml
# pyproject.toml
[dependencies]
click = ">=8.0"              # CLI 프레임워크
pyyaml = ">=5.4"             # YAML 설정 파일 파싱
pexpect = ">=4.8"            # 프로세스 자동화 및 상호작용
tmuxp = ">=1.55.0"           # tmux 세션 관리
libtmux = ">=0.46.2"         # Python tmux 라이브러리 바인딩
rich = ">=13.0.0"            # 터미널 포매팅 및 UI 컴포넌트
psutil = ">=5.9.0"           # 시스템 및 프로세스 유틸리티
```

### API 서버 의존성

- **FastAPI** (>=0.116.0): 최신 Python 웹 프레임워크 (REST API)
- **Uvicorn** (>=0.35.0): FastAPI용 ASGI 서버
- **Pydantic**: 데이터 검증 및 설정 관리 (FastAPI에 포함)
- **Textual** (>=0.41.0): 고급 터미널 UI 프레임워크

### 추가 Python 라이브러리

- **setuptools** (>=64): Python 패키지 빌드
- **wheel**: Python 패키지 배포 형식
- **altair**: 통계 시각화 라이브러리
- **attrs**: 간편한 Python 클래스 생성
- **blinker**: 객체 간 신호 전달
- **cachetools**: 캐싱 유틸리티
- **jinja2**: 템플릿 엔진
- **jsonschema**: JSON 스키마 검증
- **packaging**: Python 패키지 핵심 유틸리티
- **typing-extensions**: 타입 힌트 확장

## 🌐 프론트엔드 기술 스택 (Tauri 대시보드)

### 핵심 프론트엔드 프레임워크

```json
{
  "devDependencies": {
    "@sveltejs/kit": "^2.22.2",     // 풀스택 Svelte 프레임워크
    "svelte": "^4.2.20",            // 반응형 컴포넌트 프레임워크
    "vite": "^5.4.19",              // 빌드 도구 및 개발 서버
    "typescript": "^5.8.3"          // 타입 안전 JavaScript
  }
}
```

### UI 및 스타일링

- **Tailwind CSS** (^3.4.17): 유틸리티 우선 CSS 프레임워크
- **DaisyUI** (^4.12.24): Tailwind CSS 컴포넌트 라이브러리
- **@tailwindcss/typography** (^0.5.16): 타이포그래피 플러그인
- **PostCSS** (^8.5.6): CSS 후처리
- **Autoprefixer** (^10.4.21): CSS 벤더 프리픽스

### Tauri 데스크톱 프레임워크

- **@tauri-apps/api** (^1.6.0): Tauri JavaScript API
- **@tauri-apps/cli** (^1.6.3): Tauri CLI 도구
- **@tauri-apps/plugin-fs** (^2.4.0): 파일 시스템 작업
- **@tauri-apps/plugin-shell** (^2.3.0): 쉘 명령 실행

### 데이터 시각화 및 UI 컴포넌트

- **Chart.js** (^4.5.0): 차트 라이브러리
- **chartjs-adapter-date-fns** (^3.0.0): 차트용 날짜 포맷팅
- **date-fns** (^2.30.0): 날짜 유틸리티 라이브러리
- **lucide-svelte** (^0.292.0): Svelte용 아이콘 라이브러리

## 🦀 Rust 의존성 (Tauri 백엔드)

```toml
# tauri-dashboard/src-tauri/Cargo.toml
[dependencies]
tauri = "1.5"              # 크로스 플랫폼 데스크톱 애플리케이션 프레임워크
serde = "1.0"              # 직렬화 프레임워크
serde_json = "1.0"         # JSON 직렬화
tokio = "1.0"              # 비동기 런타임
chrono = "0.4"             # 날짜 및 시간 처리
uuid = "1.0"               # UUID 생성
thiserror = "1.0"          # 에러 처리
lazy_static = "1.4"        # 정적 변수 초기화

[build-dependencies]
tauri-build = "1.5"        # 빌드 타임 의존성
```

## 🛠️ 개발 도구 및 빌드 시스템

### 패키지 관리

- **uv**: Python 패키지 매니저 (개발 환경 권장)
- **pip**: Python 패키지 설치기
- **pnpm** (10.12.1): Node.js 패키지 매니저
- **setuptools**: Python 패키지 빌드

### 빌드 도구

- **Vite**: 프론트엔드 빌드 도구
- **Tauri**: 데스크톱 앱 번들러
- **esbuild**: JavaScript 번들러 (Vite 통해)
- **Make**: 빌드 자동화

### 개발 의존성

- **@sveltejs/adapter-static**: 정적 사이트 어댑터
- **@sveltejs/vite-plugin-svelte**: Svelte Vite 플러그인
- **@types/node**: Node.js용 TypeScript 정의
- **concurrently**: 다중 명령어 동시 실행
- **svelte-check**: Svelte TypeScript 체크
- **tslib**: TypeScript 헬퍼 라이브러리

### 코드 품질 도구

- **Ruff**: 린터 및 코드 포매터 (Black + isort 대체)
- **mypy**: 타입 체킹
- **pytest**: 단위 테스트 프레임워크
- **bandit**: 보안 취약점 스캐닝
- **pre-commit**: 자동 품질 검사

## 🌐 API 기술 스택

### Core API Framework

#### 언어 및 프레임워크

- **Python 3.12+**: 메인 개발 언어
- **FastAPI**: 현대적 웹 API 프레임워크
  - 자동 OpenAPI 문서 생성
  - 타입 힌트 기반 데이터 검증
  - 높은 성능 (Starlette + Pydantic 기반)

#### 서버 및 배포

- **Uvicorn**: ASGI 서버
  - 비동기 요청 처리
  - 핫 리로드 지원 (개발 모드)

### API Architecture

#### 라우터 구조

```
api/
├── main.py              # FastAPI 앱 진입점
├── models.py            # 데이터 모델 정의
├── requirements.txt     # API 전용 의존성
└── routers/
    ├── sessions.py      # 세션 관리 API
    └── controllers.py   # 컨트롤러 관리 API
```

#### 주요 엔드포인트

**Sessions Router (`/api/sessions`)**

- `GET /sessions` - 모든 tmux 세션 조회
- `POST /sessions/{name}` - 특정 세션 생성
- `DELETE /sessions/{name}` - 특정 세션 삭제
- `GET /sessions/{name}/status` - 세션 상태 조회

**Controllers Router (`/api/controllers`)**

- `GET /controllers` - 모든 Claude 컨트롤러 상태 조회
- `POST /controllers/{name}/start` - 컨트롤러 시작
- `POST /controllers/{name}/stop` - 컨트롤러 중지
- `POST /controllers/{name}/restart` - 컨트롤러 재시작

## 🧪 테스팅 프레임워크

- **unittest**: Python 표준 테스팅 프레임워크
- **pytest**: 고급 Python 테스팅 프레임워크
- **unittest.mock**: 테스트용 모킹 라이브러리

## ⚙️ 시스템 의존성

- **tmux**: 터미널 멀티플렉서
- **Claude Code**: Claude AI CLI 도구 통합
- **Linux/Unix**: 주요 운영 체제 지원

## 📄 설정 및 데이터 형식

- **YAML**: 설정 파일 형식
- **JSON**: 데이터 교환 형식
- **TOML**: 설정 형식 (pyproject.toml)

## 📊 로깅 및 모니터링

- **Python logging**: 표준 로깅 모듈
- **Rich**: 향상된 터미널 출력
- **FastAPI**: 웹 기반 모니터링 대시보드

## 🏗️ 아키텍처 컴포넌트

### 핵심 애플리케이션 구조

- **CLI 애플리케이션**: Click 기반 명령줄 인터페이스
- **웹 대시보드**: FastAPI 기반 모니터링 인터페이스
- **네이티브 데스크톱 앱**: Tauri 기반 크로스 플랫폼 애플리케이션
- **FastAPI 서버**: REST API 백엔드
- **Tmux 통합**: 터미널 세션 관리
- **프로세스 자동화**: Claude Code 상호작용 자동화
- **실시간 모니터링**: 세션 및 프로세스 모니터링
- **설정 관리**: YAML 기반 설정 시스템

### 자동화 시스템

- **콘텐츠 수집**: tmux 패널 콘텐츠 실시간 캡처
- **프롬프트 감지**: 정규식 기반 고급 프롬프트 인식
- **자동 응답**: 패턴 기반 자동 응답 시스템
- **세션 관리**: 자동 세션 생성 및 종료
- **대시보드 제어**: 웹 기반 세션 제어 및 모니터링

### AI/ML 시스템

- **ResponseAnalyzer**: 패턴 분석 및 학습 엔진
- **AdaptiveResponse**: AI 기반 자동 응답 시스템
- **Context-Aware Automation**: 상황 인식 자동화
- **Performance Monitoring**: 성능 지표 수집 및 분석

## 🔮 향후 기술 스택 계획

### 성능 최적화

- **캐싱**: 설정 및 상태 캐싱
- **멀티 엔진 지원**: GPT, Claude-3 등 다양한 LLM 지원
- **에러 복구**: 자동 에러 복구 메커니즘

### 확장성

- **플러그인 시스템**: 확장 가능한 아키텍처
- **분산 처리**: 다중 인스턴스 지원
- **클라우드 통합**: AWS, GCP 등 클라우드 서비스 연동

## 📈 성능 특성

### 메모리 사용량

- **Python CLI**: ~50-100MB
- **FastAPI 서버**: ~80-150MB
- **Tauri 앱**: ~100-200MB
- **전체 시스템**: ~300-500MB

### 응답 시간

- **CLI 명령어**: \<1초
- **API 요청**: \<200ms
- **UI 업데이트**: \<100ms
- **세션 생성**: 2-5초

### 확장성

- **동시 세션**: 최대 50개
- **API 요청**: 1000 req/sec
- **WebSocket 연결**: 100개 동시 연결

이 프로젝트는 Python 자동화, 현대적인 웹 기술, 그리고 네이티브 데스크톱 개발을 결합하여 포괄적인 Claude Code 자동화 및 모니터링 솔루션을 제공합니다.

______________________________________________________________________

**마지막 업데이트**: 2025-08-19\
**버전**: v2.0\
**호환성**: Python 3.12+, Node.js 18+, Rust 1.70+
