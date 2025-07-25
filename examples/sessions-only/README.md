# Sessions-Only Configuration (Recommended)

projects.yaml 없이 sessions/*.yaml 파일만 사용하는 현대적인 구성 방식입니다.

## 왜 sessions/*.yaml만 사용하나요?

### 장점
1. **단순함**: 하나의 세션 = 하나의 파일
2. **유연성**: 파일 추가/삭제로 세션 관리
3. **독립성**: 각 세션이 완전히 독립적
4. **확장성**: 디렉토리 구조로 조직화 가능

### 단점
- 공통 설정 중복 가능 (템플릿으로 해결)

## 디렉토리 구조

```
~/.scripton/yesman/
├── sessions/
│   ├── README.md                 # 세션 설명 문서
│   ├── _template.yaml            # 기본 템플릿 (언더스코어로 시작하면 무시됨)
│   │
│   ├── development/              # 개발 환경 세션들
│   │   ├── frontend.yaml
│   │   ├── backend.yaml
│   │   └── fullstack.yaml
│   │
│   ├── production/               # 프로덕션 관련 세션들
│   │   ├── monitoring.yaml
│   │   ├── logs.yaml
│   │   └── debugging.yaml
│   │
│   ├── data/                     # 데이터 관련 세션들
│   │   ├── jupyter.yaml
│   │   ├── spark.yaml
│   │   └── etl-pipeline.yaml
│   │
│   └── personal/                 # 개인 세션들
│       ├── john-dev.yaml
│       └── jane-dev.yaml
│
└── templates/                    # 재사용 가능한 템플릿
    ├── base.yaml
    ├── django.yaml
    └── react.yaml
```

## 구현 예시

### 1. 기본 세션 (sessions/development/backend.yaml)
```yaml
# Backend API development session
session_name: "backend-api"
start_directory: "~/projects/api"
environment:
  DATABASE_URL: "postgresql://localhost/dev"
windows:
  - window_name: "main"
    panes:
      - claude --dangerously-skip-permissions
      - uv run uvicorn main:app --reload
```

### 2. 템플릿 상속 (sessions/development/frontend.yaml)
```yaml
# Frontend development with template
template_name: "react"  # templates/react.yaml 참조
override:
  session_name: "frontend-app"
  start_directory: "~/projects/frontend"
  environment:
    API_URL: "http://localhost:8000"
```

### 3. 조건부 세션 (sessions/_template.yaml)
```yaml
# 언더스코어로 시작하는 파일은 무시됨
# 다른 세션의 기본값으로 복사해서 사용
session_name: "{{ PROJECT_NAME }}"
start_directory: "~/projects/{{ PROJECT_NAME }}"
windows:
  - window_name: "main"
    panes:
      - claude
```

## 마이그레이션 가이드

### projects.yaml에서 sessions/*.yaml로 전환

1. **자동 변환 스크립트**
```bash
#!/bin/bash
# convert-projects-to-sessions.sh

# projects.yaml 읽기
yq eval '.sessions | to_entries | .[]' projects.yaml | while read -r entry; do
  session_name=$(echo "$entry" | yq eval '.key' -)
  session_config=$(echo "$entry" | yq eval '.value' -)
  
  # 개별 파일로 저장
  echo "$session_config" > "sessions/${session_name}.yaml"
  echo "Created: sessions/${session_name}.yaml"
done
```

2. **수동 변환**
```yaml
# Before (projects.yaml)
sessions:
  my-app:
    template_name: "django"
    override:
      start_directory: "~/my-app"

# After (sessions/my-app.yaml)
template_name: "django"
override:
  start_directory: "~/my-app"
```

## 고급 기능

### 1. 환경별 세션
```bash
sessions/
├── dev/
│   └── app.yaml
├── staging/
│   └── app.yaml
└── prod/
    └── app.yaml

# 사용
YESMAN_ENV=dev yesman up     # dev/app.yaml 사용
YESMAN_ENV=prod yesman up    # prod/app.yaml 사용
```

### 2. 동적 세션 생성
```bash
# 템플릿에서 새 세션 생성
cp sessions/_template.yaml sessions/feature-xyz.yaml
sed -i 's/{{ PROJECT_NAME }}/feature-xyz/g' sessions/feature-xyz.yaml
```

### 3. 세션 그룹 관리
```bash
# 특정 디렉토리의 세션만 시작
for session in sessions/development/*.yaml; do
  yesman up $(basename $session .yaml)
done
```

## 베스트 프랙티스

1. **명명 규칙**
   - 환경 구분: `dev-`, `prod-`, `test-`
   - 용도 구분: `-api`, `-frontend`, `-db`
   - 예: `dev-backend-api.yaml`

2. **디렉토리 구조**
   - 용도별 그룹화
   - 환경별 분리
   - 개인/공유 구분

3. **템플릿 활용**
   - 공통 설정은 템플릿으로
   - 언더스코어 파일로 예시 제공

4. **문서화**
   - 각 디렉토리에 README.md
   - 세션 파일 내 주석 활용