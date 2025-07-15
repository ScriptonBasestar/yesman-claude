# 4단계: 기타 기능 로직 이전 (설정, 로그 등)

## 목표

세션과 컨트롤러 관리를 제외한 나머지 부가 기능들(애플리케이션 설정 관리, 세션 로그 조회 등)을 FastAPI 서버로 이전하여 백엔드 기능 통합을 완료합니다.

## 상세 실행 계획

### 1. 기능별 라우터 생성

- `api/routers/config.py`: 애플리케이션 설정 관련 엔드포인트.
- `api/routers/logs.py`: 로그 조회 관련 엔드포인트.

### 2. 설정(Config) 관리 엔드포인트 구현

`api/routers/config.py` 파일에 `yesman_config`와 연동되는 엔드포인트를 구현합니다.

```python
# api/routers/config.py
from fastapi import APIRouter
from libs.yesman_config import YesmanConfig
from pydantic import BaseModel

# 설정 데이터 모델 정의
class AppConfig(BaseModel):
    confidence_threshold: float
    response_delay: float
    # ... 기존 AppConfig 구조체 필드들 ...

router = APIRouter()
config_manager = YesmanConfig()

@router.get("/config", response_model=AppConfig)
def get_app_config():
    """애플리케이션 설정을 불러옵니다."""
    # YesmanConfig에서 설정 값을 읽어와 AppConfig 모델로 반환
    # ... 구현 필요 ...
    return config_manager.get_all_settings_as_dict()

@router.post("/config", status_code=204)
def save_app_config(config: AppConfig):
    """애플리케이션 설정을 저장합니다."""
    # AppConfig 모델을 받아 YesmanConfig를 통해 실제 파일에 저장
    # ... 구현 필요 ...
    config_manager.save_settings_from_dict(config.dict())
    return
```

### 3. 로그 조회 엔드포인트 구현

`api/routers/logs.py` 파일에 특정 세션의 로그를 조회하는 엔드포인트를 구현합니다.

```python
# api/routers/logs.py
from fastapi import APIRouter
from typing import List
# 로그를 읽어오는 실제 로직이 담긴 모듈 import (예: libs.utils)
# ...

router = APIRouter()

@router.get("/sessions/{session_name}/logs", response_model=List[str])
def get_session_logs(session_name: str, limit: int = 100):
    """특정 세션의 최근 로그를 조회합니다."""
    # 세션 이름과 limit을 사용하여 로그 파일에서 내용을 읽어오는 로직 구현
    # ...
    return ["log line 1", "log line 2"]
```

### 4. 메인 앱에 라우터 등록

`api/main.py` 파일에 새로운 라우터들을 추가합니다.

```python
# api/main.py
from fastapi import FastAPI
from .routers import sessions, controllers, config, logs # config, logs 추가

app = FastAPI()

app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(controllers.router, prefix="/api", tags=["controllers"])
app.include_router(config.router, prefix="/api", tags=["configuration"]) # 추가
app.include_router(logs.router, prefix="/api", tags=["logs"])             # 추가

# ...
```

### 5. 실행 및 API 문서 확인

서버를 재실행하고 `http://localhost:8000/docs`에서 설정 및 로그 관련 엔드포인트들이 추가되었는지 확인하고 테스트합니다.

## 예상 결과

- 기존 `python_bridge.rs`에 있던 모든 비즈니스 로직이 FastAPI 서버의 엔드포인트로 이전 완료됨.
- FastAPI 서버는 이제 프론트엔드에 필요한 모든 데이터와 기능을 제공하는 완전한 백엔드 역할을 수행함.
- `libs/`에 있던 모든 핵심 Python 로직이 API를 통해 외부에 노출됨.
