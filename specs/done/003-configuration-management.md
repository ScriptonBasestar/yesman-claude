# ADR-003: 중앙화된 설정 관리

## 상태

승인됨

## 날짜

2025-07-17

## 컨텍스트

기존 Yesman Claude의 설정 관리에서 다음과 같은 문제점들이 발견되었습니다:

1. **분산된 설정 로딩**: 각 모듈에서 개별적으로 설정 파일 로딩
1. **검증 부족**: 설정 값에 대한 타입 검증 및 유효성 검사 부재
1. **환경별 설정**: 개발/프로덕션 환경별 설정 관리 어려움
1. **에러 처리**: 설정 오류 시 불명확한 에러 메시지

### 기존 문제 사례

```python
# 분산된 설정 로딩
class YesmanConfig:
    def _load_config(self):
        # 하드코딩된 로딩 로직
        if self.global_path.exists():
            with open(self.global_path) as f:
                global_cfg = yaml.safe_load(f) or {}
```

## 결정

**Pydantic 기반의 중앙화된 설정 관리 시스템**을 구축합니다.

### 핵심 설계 원칙

1. **스키마 기반 검증**: Pydantic을 사용한 타입 안전 설정
1. **계층적 설정**: 기본값 → 환경별 → 로컬 → 환경변수 순서
1. **다중 소스 지원**: YAML 파일, 환경변수, 프로그래매틱 설정
1. **환경별 설정**: development, production, test 환경 지원

### 아키텍처 구조

```
config/
├── default.yaml          # 기본 설정
├── development.yaml      # 개발 환경
├── production.yaml       # 프로덕션 환경
└── test.yaml            # 테스트 환경

libs/core/
├── config_schema.py     # Pydantic 스키마
├── config_loader.py     # 설정 로더
└── yesman_config.py     # 기존과의 호환성
```

## 구현 세부사항

### 1. 설정 스키마 정의

```python
class YesmanConfigSchema(BaseModel):
    # 코어 설정
    mode: str = Field(default="merge", pattern="^(merge|isolated|local)$")
    root_dir: str = "~/.scripton/yesman"
    
    # 하위 설정
    tmux: TmuxConfig = Field(default_factory=TmuxConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # 검증 및 후처리
    @field_validator("root_dir")
    @classmethod
    def expand_path(cls, v: str) -> str:
        return str(Path(v).expanduser())
```

### 2. 다중 소스 로더

```python
class ConfigLoader:
    def __init__(self):
        self._sources: list[ConfigSource] = []
    
    def add_source(self, source: ConfigSource) -> None:
        """설정 소스 추가"""
        
    def load(self) -> YesmanConfigSchema:
        """모든 소스에서 설정을 로드하고 병합"""
        
    def _deep_merge(self, dict1: dict, dict2: dict) -> dict:
        """깊은 병합 수행"""
```

### 3. 설정 소스들

- **YamlFileSource**: YAML 파일에서 설정 로드
- **EnvironmentSource**: 환경변수에서 설정 로드
- **DictSource**: 프로그래매틱 설정 지원

### 4. 우선순위 정책

1. **환경변수** (최고 우선순위)
1. **환경별 설정 파일** (YESMAN_ENV=production일 때 production.yaml)
1. **로컬 프로젝트 설정**
1. **글로벌 사용자 설정**
1. **기본 설정 파일**
1. **하드코딩된 기본값** (최저 우선순위)

## 대안 검토

### 1. 기존 방식 유지

- **장점**: 변경 불필요, 단순함
- **단점**: 검증 부족, 에러 처리 미흡

### 2. 환경변수만 사용

- **장점**: 클라우드 친화적, 12-factor app 준수
- **단점**: 복잡한 설정 관리 어려움

### 3. 외부 설정 라이브러리 (dynaconf, python-decouple)

- **장점**: 검증된 솔루션
- **단점**: 외부 의존성, 프로젝트 특성과 맞지 않음

## 구현 결과

### 긍정적 영향

1. **타입 안전성**: Pydantic으로 런타임 검증
1. **명확한 에러**: 설정 오류 시 구체적인 메시지
1. **환경별 관리**: 쉬운 환경별 설정 분리
1. **문서화**: 스키마 자체가 설정 문서 역할

### 설정 검증 예시

```python
# 잘못된 설정
tmux:
  status_position: "middle"  # 허용되지 않는 값

# 에러 메시지
Configuration validation failed:
  - tmux.status_position: string does not match regex "^(top|bottom)$"
```

### 환경별 설정 예시

```yaml
# config/development.yaml
logging:
  level: DEBUG
  
confidence_threshold: 0.5

# config/production.yaml  
logging:
  level: WARNING
  max_size: 52428800  # 50MB
  
confidence_threshold: 0.9
```

### 부정적 영향

1. **초기 복잡성**: 스키마 정의 및 로더 구현 필요
1. **마이그레이션**: 기존 설정 방식과의 호환성 유지 필요
1. **학습 곡선**: Pydantic 문법 이해 필요

## 구현 상태

- ✅ 설정 스키마 정의 완료
- ✅ ConfigLoader 구현 완료
- ✅ 환경별 설정 파일 생성 완료
- ✅ YesmanConfig 리팩토링 완료
- ✅ 하위 호환성 유지 완료

## 사용 예시

### 기본 사용법

```python
from libs.yesman_config import YesmanConfig

# 자동으로 모든 소스에서 설정 로드
config = YesmanConfig()

# 타입 안전한 접근
log_level = config.schema.logging.level
tmux_shell = config.schema.tmux.default_shell

# 기존 방식도 지원 (하위 호환성)
log_level = config.get("logging.level")
```

### 환경별 설정

```bash
# 개발 환경
export YESMAN_ENV=development
yesman enter myproject  # development.yaml 설정 사용

# 프로덕션 환경
export YESMAN_ENV=production
yesman enter myproject  # production.yaml 설정 사용
```

### 환경변수 오버라이드

```bash
# 로그 레벨을 환경변수로 오버라이드
export YESMAN_LOGGING_LEVEL=ERROR
yesman logs  # ERROR 레벨로 로깅
```

## 향후 확장 계획

1. **동적 설정 reload**: 설정 파일 변경 시 자동 재로드
1. **설정 암호화**: 민감한 설정값 암호화 지원
1. **설정 검증 CLI**: `yesman config validate` 명령어
1. **설정 문서화**: 스키마에서 자동 문서 생성

## 관련 ADR

- [ADR-002: 의존성 주입](./002-dependency-injection.md)
- [ADR-004: 에러 처리 표준화](../done/phase-3-004-standardize-error-handling__DONE_20250717.md)
