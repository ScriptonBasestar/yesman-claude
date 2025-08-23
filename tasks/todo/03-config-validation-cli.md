# TODO: 설정 검증 CLI 명령어 구현

## 우선순위
중간

## 설명
`yesman config validate` 명령어를 추가하여 설정 파일의 유효성을 검사하고 문제점을 보고하는 기능을 구현합니다.

## 현재 상태
- ✅ Pydantic 기반 설정 검증 구현 완료
- ✅ ConfigLoader 구현 완료  
- ❌ CLI 검증 명령어 없음
- ❌ 사용자 친화적 검증 메시지 없음

## 작업 내용

### 1. Config 명령어 클래스 구현
- **파일**: `commands/config.py` (신규)
- BaseCommand 패턴 적용
- Click 기반 CLI 인터페이스
- 여러 검증 옵션 지원

### 2. 설정 검증 서비스 구현
- **파일**: `libs/core/config_validator.py` (신규)
- 상세한 검증 로직
- 에러 메시지 개선
- 검증 결과 분류

### 3. CLI 명령어 구현
```bash
yesman config validate                    # 모든 설정 검증
yesman config validate --file config.yaml  # 특정 파일 검증
yesman config validate --verbose           # 상세 모드
yesman config validate --fix               # 자동 수정 시도
```

### 4. 검증 항목
- **스키마 검증**: Pydantic 모델과 일치하는지 확인
- **파일 존재성**: 참조하는 파일들이 존재하는지 확인
- **권한 검증**: 필요한 디렉토리/파일 권한 확인
- **의존성 확인**: tmux, 기타 외부 도구 설치 여부
- **값 범위**: 설정값들이 허용 범위 내인지 확인

### 5. 사용자 친화적 출력
- Rich 라이브러리 활용한 컬러 출력
- 문제 분류별 그룹핑
- 수정 방법 제안
- 진행 상황 표시

## 기술 구현 세부사항

### ConfigValidator 클래스
```python
class ConfigValidator:
    def validate_all(self) -> ValidationResult:
        """모든 설정 검증"""
        
    def validate_file(self, file_path: Path) -> ValidationResult:
        """특정 파일 검증"""
        
    def validate_schema(self, config_data: dict) -> list[ValidationError]:
        """스키마 검증"""
        
    def validate_dependencies(self) -> list[ValidationError]:
        """외부 의존성 검증"""
```

### 검증 결과 표시
```python
def display_results(self, result: ValidationResult):
    console = Console()
    
    if result.is_valid:
        console.print("✅ 모든 설정이 유효합니다", style="green bold")
    else:
        console.print("❌ 설정에 문제가 있습니다", style="red bold")
        
        for error in result.errors:
            console.print(f"• {error.message}", style="red")
            if error.suggestion:
                console.print(f"  💡 {error.suggestion}", style="yellow")
```

### 자동 수정 기능
```python
def auto_fix(self, errors: list[ValidationError]) -> FixResult:
    """자동 수정 가능한 항목들을 수정"""
    fixed = []
    failed = []
    
    for error in errors:
        if error.auto_fixable:
            try:
                self._apply_fix(error)
                fixed.append(error)
            except Exception:
                failed.append(error)
                
    return FixResult(fixed=fixed, failed=failed)
```

## 예상 소요 시간
3-4시간

## 완료 기준
- [x] `commands/config.py` 구현
- [x] `libs/core/config_validator.py` 구현
- [x] CLI 명령어 등록 (`yesman.py`)
- [x] 모든 검증 항목 구현
- [x] Rich 기반 사용자 친화적 출력
- [x] `--fix` 옵션 구현
- [x] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 사용법 문서 추가

## 관련 파일
- `commands/config.py` (신규)
- `libs/core/config_validator.py` (신규)
- `commands/__init__.py` (명령어 등록)
- `tests/unit/commands/test_config_command.py` (신규)
- `tests/unit/core/test_config_validator.py` (신규)

## 의존성
- ADR-003 설정 관리 시스템 (완료)
- Rich 라이브러리 (이미 사용 중)

## 테스트 시나리오
1. **유효한 설정**: 모든 검증 통과 확인
2. **스키마 오류**: Pydantic 검증 실패 시 적절한 메시지
3. **파일 누락**: 참조 파일이 없을 때 에러 보고
4. **권한 문제**: 디렉토리 권한 부족 시 알림
5. **의존성 누락**: tmux 미설치 시 경고
6. **자동 수정**: 수정 가능한 문제 자동 해결
7. **상세 모드**: --verbose 옵션으로 상세 정보 출력

## 출력 예시
```
🔍 Yesman 설정 검증 중...

✅ 스키마 검증 (3/3 파일 통과)
✅ 파일 존재성 (모든 참조 파일 존재)
❌ 의존성 확인 (1개 문제)
  • tmux가 설치되지 않았습니다
  💡 brew install tmux 또는 apt install tmux 실행

⚠️  권한 검증 (1개 경고)  
  • ~/.scripton 디렉토리 쓰기 권한 없음
  💡 chmod 755 ~/.scripton 실행

요약: 2개 문제 발견 (1개 에러, 1개 경고)
자동 수정 가능한 항목: 1개
```