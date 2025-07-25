# Sessions Directory Configuration

Yesman-Claude는 `~/.scripton/yesman/sessions/` 디렉토리의 개별 YAML 파일들을 지원합니다.

## 디렉토리 구조

```
~/.scripton/yesman/
├── projects.yaml              # 메인 프로젝트 설정 (선택사항)
├── sessions/                  # 개별 세션 설정 디렉토리
│   ├── frontend.yaml         # 프론트엔드 세션
│   ├── backend.yaml          # 백엔드 세션
│   ├── database.yaml         # 데이터베이스 세션
│   └── monitoring.yaml       # 모니터링 세션
└── templates/                # 재사용 가능한 템플릿
    ├── django.yaml
    └── react.yaml
```

## 장점

1. **모듈화**: 각 세션을 독립적인 파일로 관리
2. **버전 관리**: 개별 파일을 선택적으로 git에 추가 가능
3. **팀 협업**: 팀원별로 다른 세션 파일 사용 가능
4. **동적 관리**: 파일 추가/삭제로 세션 관리

## 사용법

1. 세션 파일 생성:
```bash
mkdir -p ~/.scripton/yesman/sessions/
```

2. 개별 세션 파일 작성
3. `yesman up` 실행 시 자동으로 모든 세션 파일 로드

## 우선순위

1. `sessions/*.yaml` 파일들
2. `projects.yaml`의 sessions 섹션

동일한 이름의 세션이 있으면 sessions 디렉토리의 파일이 우선됩니다.