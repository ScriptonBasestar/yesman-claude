# TECH_STACK.md - 기술 스택 문서

Yesman Claude 프로젝트에서 사용하는 전체 기술 스택을 정리한 문서입니다.

## 🐍 Core Python Stack

### 언어
- **Python 3.10+**: 메인 개발 언어

### 핵심 라이브러리
- **click >= 8.0**: CLI 명령어 인터페이스
- **pyyaml >= 5.4**: YAML 설정 파일 파싱
- **pexpect >= 4.8**: 프로세스 제어 및 자동화 (Claude 출력 모니터링)
- **tmuxp >= 1.55.0**: Tmux 세션 관리 및 자동화
- **libtmux >= 0.46.2**: Python tmux 바인딩
- **rich >= 13.0.0**: 터미널 UI 및 텍스트 포매팅
- **psutil >= 5.9.0**: 시스템 프로세스 모니터링

## 🦀 Desktop Application Stack

### Tauri Desktop App (`tauri-dashboard/`)

#### Backend (Rust)
- **Tauri**: 네이티브 데스크탑 앱 프레임워크
- **serde**: JSON 직렬화/역직렬화
- **tokio**: 비동기 런타임
- **tauri-plugin-***: 시스템 통합 플러그인들

#### Frontend (JavaScript/TypeScript)
- **SvelteKit**: 반응형 웹 프레임워크
- **TypeScript**: 타입 안전성 보장
- **Vite**: 빌드 도구 및 개발 서버
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **DaisyUI**: Tailwind 기반 컴포넌트 라이브러리

#### 개발 도구
- **ESLint**: JavaScript/TypeScript 린터
- **Prettier**: 코드 포매터
- **@tauri-apps/cli**: Tauri 명령어 도구

## 🌐 Web API Stack

### FastAPI Server (`api/`)
- **FastAPI**: 현대적 웹 API 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 설정 관리

## 🏗️ Architecture Components

### 세션 관리
- **tmux**: 터미널 멀티플렉서 (시스템 의존성)
- **tmuxp**: 선언적 tmux 세션 구성
- **libtmux**: Python tmux 인터페이스

### Claude 통합
- **Claude Code**: claude.ai/code CLI (시스템 의존성)
- **pexpect**: Claude 프로세스 자동화
- **정규식 패턴**: 프롬프트 감지 시스템

### 캐싱 및 성능
- **메모리 캐싱**: 세션 상태 캐싱
- **파일 시스템 캐싱**: 구성 및 상태 지속성
- **비동기 로깅**: 성능 최적화된 로그 처리

## 📁 프로젝트 구조

```
yesman-claude/
├── 🐍 Python Core
│   ├── yesman.py                    # CLI 진입점
│   ├── commands/                    # CLI 명령어 구현
│   ├── libs/core/                   # 핵심 로직
│   ├── libs/                        # 유틸리티 및 관리자
│   └── patterns/                    # 자동응답 패턴
├── 🦀 Tauri Desktop App
│   └── tauri-dashboard/
│       ├── src/                     # Svelte 프론트엔드
│       └── src-tauri/               # Rust 백엔드
├── 🌐 FastAPI Server
│   └── api/
│       ├── main.py                  # FastAPI 앱
│       └── routers/                 # API 라우터
└── 📊 Configuration & Data
    ├── examples/                    # 설정 예시
    └── tests/                       # 테스트 파일
```

## 🔧 Development Tools

### 현재 사용 중
- **UV**: Python 패키지 및 의존성 관리
- **Git**: 버전 관리
- **GitHub**: 코드 저장소

### 계획된 도구
- **pytest**: 단위 테스트 프레임워크
- **ruff**: Python 린터 및 포매터
- **mypy**: 정적 타입 검사

## 🚀 Deployment & Distribution

### Development
- **UV**: 개발 의존성 관리
- **Tauri Dev**: 핫 리로드 개발 서버
- **FastAPI**: 개발 서버 (uvicorn)

### Production
- **Tauri Build**: 네이티브 실행 파일 생성
- **Cross-platform**: Windows, macOS, Linux 지원
- **Self-contained**: 의존성 번들링

## 🔄 Data Flow

```
CLI Commands → Python Core → tmux Sessions
     ↓              ↑              ↓
FastAPI Server ← Core APIs → Tauri Desktop
     ↓              ↑              ↓
REST Endpoints   Cache Layer   Native UI
```

## 🎯 Key Design Decisions

### 아키텍처 선택
- **Tauri vs Electron**: 더 작은 번들 크기, 더 나은 성능
- **SvelteKit vs React**: 컴파일 타임 최적화, 작은 런타임
- **FastAPI vs Flask**: 현대적 API, 자동 문서화, 타입 안전성

### 성능 최적화
- **Rust 백엔드**: 메모리 안전성과 성능
- **캐싱 전략**: 메모리 + 파일 시스템 하이브리드
- **비동기 처리**: Non-blocking I/O 최적화

---

**마지막 업데이트**: 2025-07-07  
**기술 스택 버전**: v2.0 (Tauri Migration Complete)  
**다음 리뷰**: 분기별 기술 스택 검토