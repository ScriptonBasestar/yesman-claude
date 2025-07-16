---
phase: 3
order: 3
source_plan: /tasks/plan/05-code-structure-refactoring.md
priority: medium
tags: [refactoring, configuration, architecture]
---

# 📌 작업: 설정 관리 중앙화

## Phase: 3 - Standardize Architecture

## 순서: 3

### 작업 내용

분산된 설정 로딩 로직을 중앙화하고, 설정 검증 및 스키마를 구현합니다.

### 구현 사항

#### 1. 설정 스키마 정의

**libs/core/config_schema.py**

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

class TmuxConfig(BaseModel):
    default_shell: str = "/bin/bash"
    base_index: int = 0
    pane_base_index: int = 0
    
class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    
class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = 5
    
class YesmanConfigSchema(BaseModel):
    tmux: TmuxConfig
    logging: LoggingConfig
    database: Optional[DatabaseConfig] = None
    templates_dir: str = "templates"
    projects_file: str = "projects.yaml"
    
    @validator('templates_dir')
    def validate_templates_dir(cls, v):
        # 디렉터리 존재 확인
        pass
```

#### 2. 설정 로더 개선

**libs/core/config_loader.py**

```python
class ConfigLoader:
    """Centralized configuration loader"""
    
    def __init__(self):
        self._config_sources = []
        self._env_prefix = "YESMAN_"
    
    def add_source(self, source: ConfigSource) -> None:
        """Add configuration source"""
        pass
    
    def load(self) -> YesmanConfigSchema:
        """Load and merge configurations"""
        pass
    
    def validate(self, config: dict) -> YesmanConfigSchema:
        """Validate configuration against schema"""
        pass
```

#### 3. 환경별 설정 지원

```yaml
# config/default.yaml
tmux:
  default_shell: /bin/bash
  
# config/development.yaml
logging:
  level: DEBUG
  
# config/production.yaml
logging:
  level: WARNING
```

### 실행 단계

```yaml
- name: 설정 스키마 정의
  file: libs/core/config_schema.py
  action: Pydantic 모델로 스키마 정의

- name: 설정 로더 구현
  file: libs/core/config_loader.py
  features:
    - 다중 소스 지원 (파일, 환경변수, CLI)
    - 설정 병합 로직
    - 검증 및 기본값 처리

- name: YesmanConfig 리팩토링
  file: libs/yesman_config.py
  action: ConfigLoader 사용하도록 변경

- name: 환경별 설정 파일 생성
  files:
    - config/default.yaml
    - config/development.yaml
    - config/production.yaml
    - config/test.yaml
```

### 검증 조건

- [ ] 모든 설정이 스키마로 정의됨
- [ ] 환경변수 오버라이드 작동
- [ ] 설정 검증 시 명확한 오류 메시지
- [ ] 기존 설정과 호환성 유지

### 설정 우선순위

1. CLI 인자
1. 환경변수
1. 환경별 설정 파일
1. 기본 설정 파일
1. 하드코딩된 기본값

### 예상 이점

- 타입 안전한 설정 관리
- 설정 검증 자동화
- 환경별 설정 관리 용이
- 설정 문서화 자동화
