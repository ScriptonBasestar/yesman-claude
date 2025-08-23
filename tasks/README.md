# Tasks 디렉토리

이 디렉토리는 Yesman 프로젝트의 작업 계획과 진행 상황을 관리합니다.

## 구조

```
tasks/
├── README.md                          # 이 파일
└── plan/                              # 계획 문서들
    └── architecture-completion-plan.md # 아키텍처 ADR 완료 현황
```

## 디렉토리 설명

### plan/
프로젝트의 장기적인 계획과 로드맵을 담고 있습니다.

- **architecture-completion-plan.md**: 모든 아키텍처 결정사항(ADR) 완료 현황과 향후 개선 계획

## 사용 방법

1. **새 계획 작성**: `plan/` 디렉토리에 새 마크다운 파일 추가
2. **계획 업데이트**: 기존 파일을 수정하여 진행 상황 반영
3. **완료된 계획**: 완료 날짜와 함께 상태 업데이트

## 계획 문서 작성 가이드

각 계획 문서는 다음 구조를 따라야 합니다:

```markdown
# 계획 제목

## 개요
계획의 목적과 범위

## 현재 상태
현재까지의 진행 상황

## 목표
달성하고자 하는 목표들

## 작업 계획
구체적인 작업 단계들

## 성공 기준
완료를 판단하는 기준

## 관련 문서
연관된 문서들의 링크

## 상태 정보
- 마지막 업데이트 날짜
- 작성자
- 현재 상태
```

## 관련 디렉토리

- [specs/architecture/](../specs/architecture/): 아키텍처 결정사항 (ADR)
- [specs/done/](../specs/done/): 완료된 ADR들
- [docs/development/](../docs/development/): 개발 가이드 문서들

## 상태 코드

- **Active**: 현재 진행 중
- **Completed**: 완료됨  
- **Paused**: 일시 중단
- **Cancelled**: 취소됨