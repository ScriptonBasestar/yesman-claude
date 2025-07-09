# Task 3.2: 위젯 데이터 모델 구현

**예상 시간**: 2시간  
**선행 조건**: Task 3.1 완료  
**우선순위**: 높음

## 목표
모든 렌더러에서 공통으로 사용할 위젯 데이터 모델을 구현한다.

## 작업 내용

### 1. 데이터 모델 클래스
**파일**: `libs/dashboard/renderers/widget_models.py`

구현할 모델:
- `SessionData`: 세션 정보 모델
- `HealthData`: 건강도 정보 모델
- `ActivityData`: 활동 정보 모델
- `ProgressData`: 진행률 정보 모델

### 2. SessionData 모델
```python
@dataclass
class SessionData:
    name: str
    id: str
    status: SessionStatus
    created_at: datetime
    last_activity: Optional[datetime]
    windows: List[Dict[str, Any]]
    panes: int
    claude_active: bool
    metadata: Dict[str, Any]
```

### 3. 데이터 변환 메서드
각 모델에 구현:
- `to_dict()`: 딕셔너리 변환
- `from_dict()`: 딕셔너리에서 생성
- 검증 로직

### 4. WidgetDataAdapter 클래스
원시 데이터를 모델로 변환:
- `adapt_session_data()`
- `adapt_health_data()`
- `adapt_activity_data()`
- `adapt_progress_data()`

### 5. Enum 타입 정의
```python
class SessionStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    STOPPED = "stopped"
    ERROR = "error"
```

## 완료 기준
- [ ] 4개 데이터 모델 구현
- [ ] 변환 메서드 구현
- [ ] WidgetDataAdapter 구현
- [ ] 타입 안정성 확보
- [ ] 단위 테스트 작성

## 테스트
```python
# 모델 생성 테스트
session = SessionData(
    name="test",
    id="123",
    status=SessionStatus.ACTIVE,
    created_at=datetime.now()
)

# 변환 테스트
data_dict = session.to_dict()
session2 = SessionData.from_dict(data_dict)
```

## 주의사항
- dataclass 활용
- 타입 힌트 철저히
- 불변성 고려