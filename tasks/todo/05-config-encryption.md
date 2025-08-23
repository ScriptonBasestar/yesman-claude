# TODO: 설정 암호화 기능 구현

## 우선순위
낮음

## 설명
민감한 설정값(API 키, 패스워드 등)을 암호화하여 안전하게 저장하고 관리하는 기능을 구현합니다. 외부 시크릿 저장소 연동도 고려합니다.

## 현재 상태
- ✅ Pydantic 기반 설정 관리 구현 완료
- ✅ 설정 계층화 구조 완료
- ❌ 설정값 암호화 기능 없음
- ❌ 시크릿 관리 시스템 없음

## 작업 내용

### 1. 암호화 시스템 구현
- **파일**: `libs/core/config_encryption.py` (신규)
- Fernet 대칭 암호화 사용
- 마스터 키 관리
- 선택적 암호화 지원

### 2. 시크릿 필드 타입 정의
- **파일**: `libs/core/config_schema.py` (확장)
- `SecretStr` 커스텀 타입 정의
- 자동 암호화/복호화 지원
- JSON 직렬화 시 마스킹

### 3. CLI 명령어 추가
```bash
yesman config encrypt <key> <value>      # 설정값 암호화
yesman config decrypt <key>              # 설정값 복호화 (보안 확인 후)
yesman config secrets list              # 암호화된 설정 목록
yesman config secrets rotate-key        # 마스터 키 교체
```

### 4. 외부 시크릿 저장소 연동
- 환경변수 기반 시크릿 참조
- HashiCorp Vault 연동 (선택적)
- AWS Secrets Manager 연동 (선택적)
- 클라우드별 시크릿 서비스 지원

### 5. 보안 강화 기능
- 마스터 키 안전한 저장
- 설정 파일 권한 자동 설정
- 로그에서 민감 정보 마스킹
- 메모리에서 민감 데이터 클리어

## 기술 구현 세부사항

### ConfigEncryption 클래스
```python
from cryptography.fernet import Fernet

class ConfigEncryption:
    def __init__(self, master_key: bytes | None = None):
        self.fernet = Fernet(master_key or self._load_or_generate_key())
    
    def encrypt_value(self, value: str) -> str:
        """값을 암호화하고 base64 인코딩"""
        encrypted = self.fernet.encrypt(value.encode())
        return f"encrypted:{encrypted.decode()}"
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """암호화된 값을 복호화"""
        if not encrypted_value.startswith("encrypted:"):
            return encrypted_value
        
        encrypted_data = encrypted_value[10:].encode()
        return self.fernet.decrypt(encrypted_data).decode()
```

### SecretStr 타입
```python
from typing import Any
from pydantic import Field, field_validator

class SecretStr(str):
    """민감한 문자열을 위한 커스텀 타입"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v: Any) -> str:
        if isinstance(v, str) and v.startswith("encrypted:"):
            return CONFIG_ENCRYPTION.decrypt_value(v)
        return str(v)
    
    def __repr__(self) -> str:
        return "SecretStr('***')"
```

### 설정 스키마 확장
```python
class AIConfig(BaseModel):
    api_key: SecretStr = Field(description="Claude API 키 (암호화 저장)")
    openai_api_key: SecretStr | None = Field(None, description="OpenAI API 키")
    
    @field_validator('api_key', 'openai_api_key')
    @classmethod
    def validate_secret(cls, v):
        # 개발 환경에서는 평문 허용, 프로덕션에서는 암호화 강제
        if YESMAN_ENV == "production" and not v.startswith("encrypted:"):
            raise ValueError("Production에서는 암호화된 값만 허용됩니다")
        return v
```

### 외부 시크릿 참조
```python
class SecretReference:
    """외부 시크릿 저장소 참조"""
    
    def resolve(self, reference: str) -> str:
        if reference.startswith("env:"):
            return os.environ.get(reference[4:], "")
        elif reference.startswith("vault:"):
            return self._fetch_from_vault(reference[6:])
        elif reference.startswith("aws:"):
            return self._fetch_from_aws_secrets(reference[4:])
        else:
            return reference
```

## 보안 고려사항

### 1. 마스터 키 관리
- 키 파일을 홈 디렉토리 밖에 저장 (~/.local/share/yesman/)
- 키 파일 권한을 600으로 제한
- 키 교체 시 기존 설정값 재암호화

### 2. 메모리 보안
```python
def secure_clear(data: str) -> None:
    """메모리에서 민감한 데이터 제거"""
    if hasattr(data, 'encode'):
        # 메모리 덮어쓰기 (플랫폼별 구현)
        pass
```

### 3. 로깅 보안
```python
class SecureFormatter(logging.Formatter):
    """민감한 정보를 마스킹하는 로그 포맷터"""
    
    def format(self, record):
        message = super().format(record)
        # API 키 패턴 마스킹
        message = re.sub(r'api_key["\s]*[:=]["\s]*[^"\s]+', 'api_key: ***', message)
        return message
```

## 예상 소요 시간
8-10시간 (보안 고려사항 포함)

## 완료 기준
- [ ] `libs/core/config_encryption.py` 구현
- [ ] `SecretStr` 커스텀 타입 구현
- [ ] CLI 명령어 구현 (encrypt, decrypt, secrets)
- [ ] 마스터 키 안전한 생성 및 저장
- [ ] 설정 스키마에 SecretStr 적용
- [ ] 외부 시크릿 참조 시스템 (기본적인 env: 지원)
- [ ] 로그 마스킹 기능
- [ ] 보안 테스트 작성
- [ ] 암호화 관련 문서 작성

## 관련 파일
- `libs/core/config_encryption.py` (신규)
- `libs/core/config_schema.py` (확장)
- `commands/config.py` (secrets 서브명령어 추가)
- `libs/core/logging.py` (보안 로깅)
- `tests/unit/core/test_config_encryption.py` (신규)
- `tests/security/test_secrets_handling.py` (신규)

## 의존성
- cryptography 라이브러리 (`pyproject.toml`에 추가)
- ADR-003 설정 관리 시스템 (완료)

## 사용법 예시

### 설정 암호화
```bash
# API 키 암호화
yesman config encrypt ai.api_key "sk-abc123..."
# 출력: encrypted:gAAAAABh...

# 설정 파일에 암호화된 값 저장
# config/production.yaml
ai:
  api_key: "encrypted:gAAAAABh..."
```

### 환경변수 참조
```yaml
# config/production.yaml
ai:
  api_key: "env:CLAUDE_API_KEY"        # 환경변수에서 읽기
  backup_key: "encrypted:gAAAA..."     # 암호화된 백업 키
```

### 보안 검증
```bash
# 암호화된 설정 목록
yesman config secrets list
# 출력:
# ai.api_key: encrypted (created: 2024-01-15)
# database.password: env:DB_PASSWORD

# 마스터 키 교체
yesman config secrets rotate-key
# 모든 암호화된 값을 새 키로 재암호화
```

## 테스트 시나리오
1. **기본 암호화**: 값 암호화/복호화 정확성
2. **설정 로딩**: 암호화된 설정값 자동 복호화
3. **마스터 키 관리**: 키 생성, 저장, 로딩
4. **환경변수 참조**: env: 접두사로 환경변수 읽기
5. **보안 검증**: 평문 API 키 프로덕션 차단
6. **로그 마스킹**: 로그에서 민감 정보 숨김
7. **키 교체**: 기존 데이터 무손실 키 교체