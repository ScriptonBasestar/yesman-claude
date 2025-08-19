# 📚 Yesman-Agent 문서

Yesman-Agent의 공식 문서 디렉토리입니다. 모든 문서는 체계적으로 구조화되어 있으며 숫자 prefix를 통해 우선순위와 읽기 순서를 나타냅니다.

## 📋 문서 구조

### 00-overview - 프로젝트 개요
- **01-project-overview.md** - 프로젝트 소개, 목표, 핵심 기능

### 10-architecture - 시스템 아키텍처  
- **12-tech-stack.md** - 기술 스택 및 의존성 상세 정보

### 20-api - API 문서
- **21-endpoints.md** - REST API 및 WebSocket 완전 가이드

### 30-user-guide - 사용자 가이드
- **31-getting-started.md** - 설치 및 시작 가이드
- **32-configuration.md** - 설정 시스템 가이드  
- **33-templates.md** - 템플릿 시스템 사용법
- **34-feature-overview.md** - 주요 기능 개요

### 40-developer-guide - 개발자 가이드
- **41-development-setup.md** - 개발 환경 설정 및 기여 가이드
- **42-testing-guide.md** - 테스트 전략 및 실행 방법
- **CLAUDE.md** - Claude Code 전용 개발 가이드

### 50-operations - 운영 가이드
- **51-monitoring-setup.md** - 모니터링, 로깅, 성능 관리

### 60-project-management - 프로젝트 관리
- **61-roadmap.md** - 프로젝트 로드맵 및 개발 계획

### 70-examples - 예제 및 템플릿
- **71-configuration-examples.md** - 다양한 설정 예제 모음

## 🎯 빠른 네비게이션

### 새로운 사용자
1. [프로젝트 개요](00-overview/01-project-overview.md) - 프로젝트 이해
2. [시작하기](30-user-guide/31-getting-started.md) - 설치 및 첫 실행
3. [설정 가이드](30-user-guide/32-configuration.md) - 기본 설정
4. [설정 예제](70-examples/71-configuration-examples.md) - 실제 사용 예제

### 개발자
1. [개발 환경 설정](40-developer-guide/41-development-setup.md) - 개발 환경 구축
2. [기술 스택](10-architecture/12-tech-stack.md) - 아키텍처 이해
3. [API 문서](20-api/21-endpoints.md) - API 개발
4. [테스트 가이드](40-developer-guide/42-testing-guide.md) - 테스트 실행

### 운영자
1. [모니터링 설정](50-operations/51-monitoring-setup.md) - 운영 환경 설정
2. [프로젝트 로드맵](60-project-management/61-roadmap.md) - 개발 계획 확인

### Claude Code 사용자
1. [Claude 전용 가이드](40-developer-guide/CLAUDE.md) - Claude Code 최적화 정보

## 📖 문서 사용 가이드

### 네이밍 규칙

문서는 다음 패턴을 따릅니다:
- **숫자 prefix**: 중요도/우선순위 (00-09 개요, 10-19 아키텍처, 20-29 API, ...)
- **kebab-case**: 파일명은 하이픈으로 구분
- **명확한 제목**: 내용을 정확히 표현

### 상호 참조

문서 간 링크는 상대 경로를 사용합니다:
```markdown
[API 문서](../20-api/21-endpoints.md)
[설정 가이드](../30-user-guide/32-configuration.md)
```

### 업데이트 정책

모든 문서는 다음 정보를 포함합니다:
- **마지막 업데이트**: 문서 수정 날짜
- **버전**: 해당하는 경우 버전 정보
- **호환성**: 지원 플랫폼 또는 의존성

## 🔧 문서 기여

### 수정 가이드라인

1. **정확성**: 코드베이스와 일치하는 정보만 포함
2. **명확성**: 기술적 내용을 이해하기 쉽게 설명
3. **완성도**: 예제와 실제 사용법 포함
4. **일관성**: 기존 문서의 스타일과 구조 유지

### 새 문서 추가

1. 적절한 카테고리 디렉토리 선택
2. 숫자 prefix 할당 (기존 문서와 중복 방지)
3. 명확한 파일명 사용
4. 이 README.md에 새 문서 링크 추가

### 문서 구조 템플릿

새 문서는 다음 구조를 권장합니다:

```markdown
# 문서 제목

문서에 대한 간단한 설명.

## 📚 목차

1. [섹션 1](#섹션-1)
2. [섹션 2](#섹션-2)

## 🎯 주요 내용

### 섹션 1
내용...

### 섹션 2  
내용...

## 📝 예제

실제 사용 예제...

## 🔧 문제 해결

일반적인 문제와 해결책...

---

**마지막 업데이트**: YYYY-MM-DD  
**버전**: vX.X  
**호환성**: 지원 플랫폼/의존성
```

## 🚀 프로젝트 상태

- **현재 버전**: v2.0
- **문서 커버리지**: 100% (모든 주요 기능 문서화 완료)
- **마지막 대규모 정리**: 2025-08-19
- **다음 업데이트 계획**: 2025-09-01

## 📞 도움이 필요한 경우

1. **일반적인 사용법**: [사용자 가이드](30-user-guide/) 참조
2. **개발 관련**: [개발자 가이드](40-developer-guide/) 참조
3. **API 사용**: [API 문서](20-api/) 참조
4. **설정 문제**: [예제 문서](70-examples/) 참조

---

**문서 관리**: Development Team  
**최종 검토**: 2025-08-19  
**구조 버전**: v2.0