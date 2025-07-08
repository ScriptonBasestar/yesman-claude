# Yesman-Claude 문서 색인

Yesman-Claude 프로젝트의 모든 문서를 체계적으로 정리한 종합 가이드입니다.

## 📖 문서 구조 개요

### 👤 사용자 가이드 (`user-guide/`)
새로운 사용자와 일반 사용자를 위한 기본 정보입니다.

- [**시작하기**](user-guide/getting-started.md) - 설치 및 기본 사용법
- [**기능 개요**](user-guide/feature-overview.md) - 전체 기능 소개 및 사용 예시

### 🔧 개발자 가이드 (`developer-guide/`)
프로젝트 개발 및 기여를 위한 기술 문서입니다.

#### 핵심 문서
- [**프로젝트 가이드**](developer-guide/project-guide.md) - 프로젝트 구조 및 개발 환경 설정
- [**기술 스택**](developer-guide/tech-stack.md) - 사용된 모든 기술과 라이브러리 상세 정보
- [**구현 개요**](developer-guide/implementation-overview.md) - 주요 구현 사항 요약
- [**개선 아이디어**](developer-guide/improvement-ideas.md) - 향후 개선 및 신기능 아이디어
- [**개선 이력**](developer-guide/improvement-history.md) - 과거 개선 작업 기록

#### 테스팅 (`testing/`)
- [**통합 테스트**](developer-guide/testing/integration-testing.md) - 통합 테스트 실행 가이드
- [**테스트 스위트**](developer-guide/testing/test-suite-guide.md) - 전체 테스트 환경 설명
- [**테스트 개선사항**](developer-guide/testing/test-improvements.md) - 테스트 관련 개선 내역

#### 문제 해결 (`troubleshooting/`)
- [**문제 해결 가이드**](developer-guide/troubleshooting/troubleshooting-guide.md) - 일반적인 문제 및 해결책

### 📋 프로젝트 관리 (`project-management/`)
프로젝트 진행 상황 및 계획 관리를 위한 문서입니다.

#### 진행 상황 추적 (`tracking/`)
- [**현재 작업**](project-management/tracking/active-todos.md) - 현재 진행 중인 작업 목록
- [**백로그**](project-management/tracking/backlog.md) - 향후 작업 계획
- [**알려진 이슈**](project-management/tracking/known-issues.md) - 현재 발견된 문제들
- [**문서 수정 사항**](project-management/tracking/documentation-fixes.md) - 문서 관련 수정 작업

#### 계획 수립 (`planning/`)
- [**로드맵**](project-management/planning/roadmap.md) - 장기 개발 계획
- [**WebSocket 터미널**](project-management/planning/01-websocket-terminal.md) - WebSocket 기반 터미널 구현 계획
- [**보안 강화**](project-management/planning/02-security-hardening.md) - 보안 개선 계획
- [**에러 복구**](project-management/planning/03-error-recovery.md) - 오류 처리 개선 계획
- [**플러그인 아키텍처**](project-management/planning/04-plugin-architecture.md) - 플러그인 시스템 설계

#### 완료된 작업 (`completed/`)
- [**FastAPI 서버 설정**](project-management/completed/01-setup-fastapi-server.md)
- [**세션 로직 마이그레이션**](project-management/completed/02-migrate-session-logic.md)
- [**컨트롤러 로직 마이그레이션**](project-management/completed/03-migrate-controller-logic.md)
- [**기타 로직 마이그레이션**](project-management/completed/04-migrate-other-logic.md)
- [**세션 메서드 누락 수정**](project-management/completed/todo-2-missing-session-methods.md)
- [**설정 읽기 전용 수정**](project-management/completed/todo-4-config-readonly.md)

### 🏗️ 아키텍처 (`architecture/`)
시스템 구조 및 기술적 설계에 대한 문서입니다.

- [**아키텍처 개요**](architecture/README.md) - 전체 시스템 구조 설명
- [**API 기술 스택**](architecture/api-technology-stack.md) - API 서버 기술 상세

### 📡 API 문서 (`api/`)
REST API 관련 문서입니다.

- [**API 개요**](api/README.md) - FastAPI 서버 사용법 및 엔드포인트
- [**API 기술 스택**](api/tech-stack.md) - API 관련 기술 정보

### 📚 예제 (`examples/`)
설정 및 사용 예제 모음입니다.

- [**예제 가이드**](examples/example-guide.md) - 설정 파일 예제 및 사용법

## 🔍 빠른 검색

### 새로 시작하는 분들께
1. [시작하기 가이드](user-guide/getting-started.md) 
2. [기능 개요](user-guide/feature-overview.md)
3. [예제 가이드](examples/example-guide.md)

### 개발에 참여하고 싶은 분들께
1. [프로젝트 가이드](developer-guide/project-guide.md)
2. [기술 스택](developer-guide/tech-stack.md) 
3. [현재 작업](project-management/tracking/active-todos.md)

### 문제를 해결하고 싶은 분들께
1. [문제 해결 가이드](developer-guide/troubleshooting/troubleshooting-guide.md)
2. [알려진 이슈](project-management/tracking/known-issues.md)
3. [테스트 가이드](developer-guide/testing/test-suite-guide.md)

### 프로젝트 진행 상황을 확인하고 싶은 분들께
1. [로드맵](project-management/planning/roadmap.md)
2. [현재 작업](project-management/tracking/active-todos.md)
3. [완료된 작업](project-management/completed/)

## 📝 문서 작성 규칙

- **언어**: 내부 개발 문서는 한국어, 공개 문서는 영어
- **파일명**: kebab-case 사용 (예: `my-document.md`)
- **구조**: 사용자 그룹별 논리적 분류

## 🔄 최근 업데이트

- **2025-01-08**: 문서 구조 전면 개편
  - 47개 분산된 문서를 체계적으로 재구성
  - 사용자별 문서 그룹 분류
  - 중복 문서 통합 및 정리
  - kebab-case 명명 규칙 적용

---

**마지막 업데이트**: 2025-01-08  
**문서 개수**: 50+ 개  
**관리자**: Yesman-Claude 개발팀