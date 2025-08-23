# TODO: 설정 문서 자동 생성 기능 구현

---
status: suspended
reason: 복잡한 문서 생성 로직 및 템플릿 시스템 필요 - 전용 문서화 스프린트에서 처리
suspended_date: 2025-08-23
---

## 우선순위
낮음

## 설명
Pydantic 스키마에서 자동으로 설정 문서를 생성하는 기능을 구현합니다. 개발자와 사용자가 쉽게 이해할 수 있는 설정 문서를 자동으로 만들어줍니다.

## 현재 상태
- ✅ Pydantic 스키마 정의 완료
- ✅ 설정 구조 체계화 완료
- ❌ 자동 문서 생성 기능 없음
- ❌ 설정 가이드 문서 없음

## 작업 내용

### 1. 문서 생성기 구현
- **파일**: `libs/core/config_docs_generator.py` (신규)
- Pydantic 스키마 분석
- 마크다운 문서 생성
- 예제 설정 자동 생성

### 2. CLI 명령어 추가
```bash
yesman config docs                        # 설정 문서 출력
yesman config docs --output config.md    # 파일로 저장
yesman config docs --format json         # JSON 스키마 출력
yesman config docs --examples            # 예제 포함
```

### 3. 생성할 문서 섹션
- **설정 개요**: 전체 설정 구조 설명
- **필수 설정**: 반드시 설정해야 하는 항목들
- **선택적 설정**: 기본값이 있는 선택적 항목들
- **설정 예제**: 실제 사용 가능한 YAML 예제
- **환경변수 매핑**: 환경변수로 오버라이드 가능한 항목들
- **검증 규칙**: 각 설정값의 제약 조건

### 4. 다양한 출력 형식 지원
- **Markdown**: 읽기 쉬운 문서 형태
- **JSON Schema**: IDE 자동완성 지원
- **HTML**: 웹 브라우저에서 보기
- **YAML Template**: 복사해서 사용할 수 있는 템플릿

## 기술 구현 세부사항

### ConfigDocsGenerator 클래스
```python
class ConfigDocsGenerator:
    def __init__(self, schema_class: type[BaseModel]):
        self.schema = schema_class
        self.json_schema = schema_class.model_json_schema()
    
    def generate_markdown(self) -> str:
        """마크다운 문서 생성"""
        
    def generate_json_schema(self) -> dict:
        """JSON 스키마 생성"""
        
    def generate_yaml_template(self) -> str:
        """YAML 템플릿 생성"""
        
    def generate_examples(self) -> dict[str, str]:
        """환경별 예제 생성"""
```

### 스키마 분석 로직
```python
def _analyze_field(self, field_name: str, field_info: FieldInfo) -> FieldDoc:
    """필드 정보를 분석하여 문서용 데이터 생성"""
    return FieldDoc(
        name=field_name,
        type=self._get_type_string(field_info.annotation),
        required=field_info.is_required(),
        default=field_info.default,
        description=field_info.description,
        constraints=self._extract_constraints(field_info),
        env_var=self._get_env_var_name(field_name)
    )
```

### 마크다운 템플릿
```python
MARKDOWN_TEMPLATE = """
# Yesman 설정 가이드

## 개요
{overview}

## 설정 구조
{structure}

## 필수 설정
{required_fields}

## 선택적 설정  
{optional_fields}

## 설정 예제
{examples}

## 환경변수 오버라이드
{env_vars}
"""
```

## 예상 소요 시간
5-6시간

## 완료 기준
- [ ] `libs/core/config_docs_generator.py` 구현
- [ ] `commands/config.py`에 docs 서브명령어 추가
- [ ] Markdown 형식 문서 생성
- [ ] JSON Schema 출력 지원
- [ ] YAML 템플릿 생성
- [ ] 환경별 예제 자동 생성
- [ ] 환경변수 매핑 문서화
- [ ] CLI 옵션 구현 (--output, --format, --examples)
- [ ] 단위 테스트 작성
- [ ] 생성된 문서 검증 테스트

## 관련 파일
- `libs/core/config_docs_generator.py` (신규)
- `commands/config.py` (확장)
- `libs/core/config_schema.py` (분석 대상)
- `tests/unit/core/test_config_docs_generator.py` (신규)
- `docs/configuration/README.md` (자동 생성될 문서)

## 의존성
- ADR-003 설정 관리 시스템 (완료)
- Pydantic 모델 정의 (완료)
- Jinja2 템플릿 엔진 (추가 필요할 수 있음)

## 생성될 문서 예시

### 마크다운 출력
```markdown
# Yesman 설정 가이드

## tmux 설정

### tmux.default_shell
- **타입**: `string`
- **기본값**: `"/bin/bash"`
- **설명**: tmux 세션에서 사용할 기본 셸
- **환경변수**: `YESMAN_TMUX_DEFAULT_SHELL`
- **예제**: `"/bin/zsh"`, `"/usr/bin/fish"`

### tmux.status_position
- **타입**: `string`
- **기본값**: `"bottom"`
- **필수**: 아니오
- **제약조건**: `"top"` 또는 `"bottom"`만 허용
- **설명**: tmux 상태바 위치
```

### JSON Schema 출력
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "tmux": {
      "type": "object",
      "properties": {
        "default_shell": {
          "type": "string",
          "default": "/bin/bash",
          "description": "tmux 세션에서 사용할 기본 셸"
        }
      }
    }
  }
}
```

## 테스트 시나리오
1. **전체 스키마 문서화**: 모든 설정 항목이 문서에 포함
2. **필드 분석 정확성**: 타입, 기본값, 제약조건 올바르게 추출
3. **예제 생성**: 유효한 YAML 예제 생성
4. **환경변수 매핑**: 올바른 환경변수 이름 생성
5. **출력 형식**: 각 형식별 올바른 출력 생성
6. **파일 저장**: --output 옵션으로 파일 저장 기능