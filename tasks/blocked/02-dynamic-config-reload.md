# TODO: 동적 설정 reload 기능 구현

---
status: blocked
reason: watchdog 의존성 추가 및 아키텍처 변경 필요 - 별도 스프린트에서 처리
blocked_date: 2025-08-23
---

## 우선순위
중간

## 설명
설정 파일이 변경될 때 애플리케이션을 재시작하지 않고도 자동으로 설정을 다시 로드하는 기능을 구현합니다.

## 현재 상태
- ✅ Pydantic 기반 설정 관리 구현 완료
- ✅ ConfigLoader 구현 완료
- ❌ 동적 reload 기능 없음
- ❌ 파일 변경 감지 없음

## 작업 내용

### 1. 파일 감시 시스템 구현
- `watchdog` 라이브러리 추가 (`pyproject.toml`)
- 설정 파일 변경 감지 클래스 구현
- 다중 설정 파일 감시 지원

### 2. ConfigLoader 확장
- **파일**: `libs/core/config_loader.py`
- `enable_auto_reload()` 메서드 추가
- `disable_auto_reload()` 메서드 추가
- 변경 감지 시 자동 reload 로직

### 3. YesmanConfig 통합
- **파일**: `libs/core/yesman_config.py`
- 설정 변경 시 이벤트 콜백 지원
- 의존성이 있는 서비스들의 자동 갱신

### 4. CLI 명령어 추가
- **파일**: `commands/config.py` (신규 또는 기존 확장)
- `yesman config watch` 명령어 추가
- 실시간 설정 변경 모니터링

### 5. 안전 장치 구현
- 잘못된 설정 파일로 변경 시 롤백
- 변경 사항 검증 후 적용
- 에러 발생 시 이전 설정 유지

## 기술 구현 세부사항

### 파일 감시자
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.yaml', '.yml')):
            self.reload_config(event.src_path)
```

### 설정 reload 메서드
```python
def reload_config(self) -> bool:
    """설정 파일을 다시 로드하고 검증"""
    try:
        new_config = self._load_fresh_config()
        self._validate_config(new_config)
        self._update_config(new_config)
        return True
    except Exception as e:
        logger.error(f"Config reload failed: {e}")
        return False
```

## 예상 소요 시간
4-6시간

## 완료 기준
- [ ] watchdog 의존성 추가
- [ ] ConfigFileHandler 클래스 구현
- [ ] ConfigLoader.enable_auto_reload() 구현
- [ ] YesmanConfig 동적 업데이트 지원
- [ ] `yesman config watch` 명령어 추가
- [ ] 설정 검증 및 롤백 기능
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성

## 관련 파일
- `libs/core/config_loader.py`
- `libs/core/yesman_config.py`
- `commands/config.py` (신규 또는 확장)
- `pyproject.toml`
- `tests/unit/core/test_config_reload.py` (신규)

## 의존성
- ADR-003 설정 관리 시스템 (완료)
- watchdog 라이브러리 설치

## 테스트 시나리오
1. YAML 파일 수정 → 자동 reload 확인
2. 잘못된 설정 → 롤백 확인
3. 다중 파일 변경 → 순차 reload 확인
4. 실행 중인 명령어에 영향 없음 확인