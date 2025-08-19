# API Endpoints

Yesman-Agent의 FastAPI 기반 REST API 엔드포인트 완전 가이드입니다.

## 📚 목차

1. [API 개요](#api-개요)
2. [인증 및 보안](#인증-및-보안)
3. [세션 관리](#세션-관리)
4. [컨트롤러 관리](#컨트롤러-관리)
5. [건강도 모니터링](#건강도-모니터링)
6. [성능 메트릭](#성능-메트릭)
7. [테마 및 설정](#테마-및-설정)
8. [WebSocket 프로토콜](#websocket-프로토콜)
9. [에러 처리](#에러-처리)

## 🌐 API 개요

### 기본 정보

- **Base URL**: `http://localhost:10501/api`
- **프로토콜**: HTTP/1.1, WebSocket
- **데이터 형식**: JSON
- **인증**: Bearer Token (선택사항)

### 서버 실행

```bash
# 개발 모드
cd api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 10501

# 프로덕션 모드
cd api && python -m uvicorn main:app --host 0.0.0.0 --port 10501

# 또는 메인 명령어 사용
./yesman.py dashboard --api-only
```

### API 문서 접속

- **Swagger UI**: http://localhost:10501/docs
- **ReDoc**: http://localhost:10501/redoc
- **OpenAPI Schema**: http://localhost:10501/openapi.json

## 🔒 인증 및 보안

### 토큰 기반 인증 (선택사항)

```http
Authorization: Bearer <token>
```

### CORS 설정

API 서버는 다음 도메인에서의 접근을 허용합니다:
- `http://localhost:5173` (Tauri 개발 서버)
- `http://localhost:3000` (기타 개발 서버)
- `https://tauri.localhost` (Tauri 프로덕션)

## 📋 세션 관리

### 모든 세션 조회

**GET** `/sessions`

세션 목록과 상태 정보를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/sessions"
```

**응답 예시:**

```json
{
  "sessions": [
    {
      "name": "my-project",
      "status": "active",
      "uptime": 3600,
      "windows": 3,
      "panes": 5,
      "cpu_usage": 15.5,
      "memory_usage": 256.7,
      "last_activity": "2025-08-19T12:30:00Z"
    }
  ],
  "total_sessions": 1,
  "active_sessions": 1
}
```

### 특정 세션 조회

**GET** `/sessions/{session_name}`

특정 세션의 상세 정보를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/sessions/my-project"
```

**응답 예시:**

```json
{
  "name": "my-project",
  "status": "active",
  "uptime": 3600,
  "windows": [
    {
      "index": 0,
      "name": "editor",
      "active": true,
      "panes": [
        {
          "index": 0,
          "active": true,
          "current_command": "nvim",
          "working_directory": "/home/user/project"
        }
      ]
    }
  ],
  "created_at": "2025-08-19T08:30:00Z",
  "config": {
    "template": "django",
    "start_directory": "/home/user/project"
  }
}
```

### 세션 설정 (생성)

**POST** `/sessions/{session_name}/setup`

지정된 이름으로 새로운 tmux 세션을 생성하고 설정합니다.

```bash
curl -X POST "http://localhost:10501/api/sessions/my-project/setup"
```

**응답 예시:**

```json
{
  "success": true,
  "session_name": "my-project",
  "message": "Session setup completed successfully",
  "details": {
    "windows_created": 3,
    "session_exists": true,
    "config_loaded": true
  }
}
```

### 세션 삭제 (Teardown)

**DELETE** `/sessions/{session_name}`

지정된 세션을 종료하고 삭제합니다.

```bash
curl -X DELETE "http://localhost:10501/api/sessions/my-project"
```

**응답 예시:**

```json
{
  "success": true,
  "message": "Session 'my-project' deleted successfully"
}
```

### 모든 세션 설정

**POST** `/sessions/setup-all`

프로젝트 설정 파일에 정의된 모든 세션을 생성합니다.

```bash
curl -X POST "http://localhost:10501/api/sessions/setup-all"
```

### 모든 세션 정리

**POST** `/sessions/teardown-all`

모든 관리 중인 세션을 종료합니다.

```bash
curl -X POST "http://localhost:10501/api/sessions/teardown-all"
```

### 세션 시작

**POST** `/sessions/{session_name}/start`

기존 세션을 시작합니다.

```bash
curl -X POST "http://localhost:10501/api/sessions/my-project/start"
```

### 세션 중지

**POST** `/sessions/{session_name}/stop`

실행 중인 세션을 중지합니다.

```bash
curl -X POST "http://localhost:10501/api/sessions/my-project/stop"
```

### 세션 상태 조회

**GET** `/sessions/{session_name}/status`

특정 세션의 현재 상태를 조회합니다.

```bash
curl -X GET "http://localhost:10501/api/sessions/my-project/status"
```

**응답 예시:**

```json
{
  "session_name": "my-project",
  "status": "active",
  "windows_count": 3,
  "panes_count": 5,
  "uptime_seconds": 3600,
  "last_activity": "2025-08-19T12:30:00Z"
}
```

## 🤖 컨트롤러 관리

### 모든 컨트롤러 상태 조회

**GET** `/controllers`

Claude 컨트롤러들의 상태를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/controllers"
```

**응답 예시:**

```json
{
  "controllers": [
    {
      "session_name": "my-project",
      "status": "running",
      "uptime": 1800,
      "responses_count": 42,
      "last_response": "2025-08-19T12:25:00Z",
      "confidence_score": 0.89,
      "error_count": 0
    }
  ],
  "total_controllers": 1,
  "active_controllers": 1
}
```

### 특정 컨트롤러 상태 조회

**GET** `/controllers/{session_name}`

특정 세션의 Claude 컨트롤러 상태를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/controllers/my-project"
```

### 컨트롤러 시작

**POST** `/controllers/{session_name}/start`

지정된 세션에서 Claude 자동화를 시작합니다.

```bash
curl -X POST "http://localhost:10501/api/controllers/my-project/start"
```

**응답 예시:**

```json
{
  "success": true,
  "message": "Claude controller started for session 'my-project'",
  "controller_id": "ctrl_123456"
}
```

### 컨트롤러 중지

**POST** `/controllers/{session_name}/stop`

지정된 세션의 Claude 자동화를 중지합니다.

```bash
curl -X POST "http://localhost:10501/api/controllers/my-project/stop"
```

### 컨트롤러 재시작

**POST** `/controllers/{session_name}/restart`

Claude 컨트롤러를 재시작합니다.

```bash
curl -X POST "http://localhost:10501/api/controllers/my-project/restart"
```

## 📊 건강도 모니터링

### 프로젝트 건강도 조회

**GET** `/health`

전체 프로젝트의 건강도 점수를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/health"
```

**응답 예시:**

```json
{
  "overall_score": 85,
  "overall_level": "good",
  "categories": {
    "build": 90,
    "tests": 80,
    "dependencies": 88,
    "security": 75,
    "performance": 85,
    "code_quality": 82,
    "git": 92,
    "documentation": 70
  },
  "details": {
    "build": {
      "score": 90,
      "level": "excellent",
      "last_check": "2025-08-19T12:00:00Z",
      "issues": []
    }
  },
  "recommendations": [
    "Consider updating security dependencies",
    "Add more documentation for new features"
  ],
  "last_updated": "2025-08-19T12:30:00Z"
}
```

### 건강도 히스토리

**GET** `/health/history`

건강도 변화 히스토리를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/health/history?days=7"
```

**쿼리 파라미터:**
- `days`: 조회할 일수 (기본값: 7)
- `category`: 특정 카테고리만 조회 (선택사항)

### 건강도 재계산

**POST** `/health/refresh`

건강도를 강제로 재계산합니다.

```bash
curl -X POST "http://localhost:10501/api/health/refresh"
```

## ⚡ 성능 메트릭

### 현재 성능 메트릭 조회

**GET** `/performance/metrics`

실시간 성능 지표를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/performance/metrics"
```

**응답 예시:**

```json
{
  "system": {
    "cpu_usage": 15.5,
    "memory_usage": 256.7,
    "memory_percent": 12.3,
    "disk_usage": 45.2
  },
  "application": {
    "render_time": 0.032,
    "response_time": 0.015,
    "cache_hit_rate": 0.85,
    "active_connections": 5,
    "queue_size": 0
  },
  "tmux": {
    "sessions_count": 3,
    "windows_count": 8,
    "panes_count": 12
  },
  "timestamp": "2025-08-19T12:30:00Z"
}
```

### 성능 히스토리

**GET** `/performance/history`

성능 메트릭 히스토리를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/performance/history?hours=24"
```

### 최적화 레벨 설정

**POST** `/performance/optimization`

성능 최적화 레벨을 설정합니다.

```bash
curl -X POST "http://localhost:10501/api/performance/optimization" \
  -H "Content-Type: application/json" \
  -d '{"level": "high"}'
```

**요청 본문:**

```json
{
  "level": "low|medium|high|ultra"
}
```

## 🎨 테마 및 설정

### 사용 가능한 테마 조회

**GET** `/themes`

사용 가능한 모든 테마를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/themes"
```

**응답 예시:**

```json
{
  "themes": [
    {
      "name": "default_light",
      "display_name": "Default Light",
      "mode": "light",
      "colors": {
        "primary": "#3498db",
        "secondary": "#2ecc71",
        "background": "#ffffff"
      }
    },
    {
      "name": "default_dark",
      "display_name": "Default Dark",
      "mode": "dark",
      "colors": {
        "primary": "#3498db",
        "secondary": "#2ecc71",
        "background": "#2c3e50"
      }
    }
  ],
  "current_theme": "default_dark"
}
```

### 현재 테마 조회

**GET** `/themes/current`

현재 활성화된 테마를 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/themes/current"
```

### 테마 설정

**POST** `/themes/current`

활성 테마를 변경합니다.

```bash
curl -X POST "http://localhost:10501/api/themes/current" \
  -H "Content-Type: application/json" \
  -d '{"theme": "default_dark"}'
```

### 설정 조회

**GET** `/config`

현재 시스템 설정을 반환합니다.

```bash
curl -X GET "http://localhost:10501/api/config"
```

### 설정 업데이트

**PUT** `/config`

시스템 설정을 업데이트합니다.

```bash
curl -X PUT "http://localhost:10501/api/config" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "update_interval": 1.0,
      "theme": "auto"
    },
    "performance": {
      "optimization_level": "medium"
    }
  }'
```

## 🌐 WebSocket 프로토콜

### 연결

WebSocket을 통한 실시간 데이터 업데이트를 지원합니다.

```javascript
const ws = new WebSocket('ws://localhost:10501/ws');

ws.onopen = function(event) {
    console.log('Connected to Yesman-Agent WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    handleUpdate(data);
};
```

### 메시지 타입

#### 세션 업데이트

```json
{
  "type": "session_update",
  "data": {
    "session_name": "my-project",
    "status": "active",
    "uptime": 3600,
    "windows": 3,
    "cpu_usage": 15.5
  }
}
```

#### 건강도 업데이트

```json
{
  "type": "health_update",
  "data": {
    "overall_score": 85,
    "changed_categories": ["tests", "security"],
    "previous_score": 82
  }
}
```

#### 성능 업데이트

```json
{
  "type": "performance_update",
  "data": {
    "cpu_usage": 15.5,
    "memory_usage": 256.7,
    "response_time": 0.015,
    "timestamp": "2025-08-19T12:30:00Z"
  }
}
```

### 클라이언트 명령

클라이언트에서 서버로 명령을 전송할 수 있습니다.

```javascript
// 데이터 새로고침 요청
ws.send(JSON.stringify({
    "type": "refresh",
    "target": "sessions"
}));

// 테마 변경
ws.send(JSON.stringify({
    "type": "theme_change",
    "theme": "default_dark"
}));

// 구독 설정
ws.send(JSON.stringify({
    "type": "subscribe",
    "topics": ["sessions", "health", "performance"]
}));
```

## ❌ 에러 처리

### 표준 에러 응답

모든 API 에러는 다음 형식으로 반환됩니다:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional error details"
    },
    "timestamp": "2025-08-19T12:30:00Z"
  }
}
```

### HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 409 | 충돌 (이미 존재) |
| 422 | 유효성 검사 실패 |
| 500 | 서버 내부 오류 |

### 에러 코드

| 코드 | 설명 |
|------|------|
| `SESSION_NOT_FOUND` | 세션을 찾을 수 없음 |
| `SESSION_ALREADY_EXISTS` | 세션이 이미 존재 |
| `CONTROLLER_NOT_RUNNING` | 컨트롤러가 실행 중이 아님 |
| `INVALID_TEMPLATE` | 잘못된 템플릿 |
| `THEME_NOT_FOUND` | 테마를 찾을 수 없음 |
| `CONFIG_VALIDATION_ERROR` | 설정 유효성 검사 실패 |
| `TMUX_CONNECTION_ERROR` | tmux 연결 오류 |
| `PERMISSION_DENIED` | 권한 거부 |

### 에러 응답 예시

```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session 'nonexistent-session' not found",
    "details": {
      "session_name": "nonexistent-session",
      "available_sessions": ["project1", "project2"]
    },
    "timestamp": "2025-08-19T12:30:00Z"
  }
}
```

## 📝 사용 예시

### Python 클라이언트

```python
import requests
import json

# 기본 설정
BASE_URL = "http://localhost:10501/api"
headers = {"Content-Type": "application/json"}

# 세션 목록 조회
response = requests.get(f"{BASE_URL}/sessions")
sessions = response.json()
print(f"Active sessions: {len(sessions['sessions'])}")

# 새 세션 생성
session_data = {
    "name": "my-new-project",
    "template": "django",
    "config": {
        "start_directory": "/home/user/my-new-project",
        "auto_start_claude": True
    }
}

response = requests.post(
    f"{BASE_URL}/sessions",
    headers=headers,
    data=json.dumps(session_data)
)

if response.status_code == 201:
    print("Session created successfully")
else:
    print(f"Error: {response.json()}")
```

### JavaScript 클라이언트

```javascript
class YesmanClient {
    constructor(baseUrl = 'http://localhost:10501/api') {
        this.baseUrl = baseUrl;
    }

    async getSessions() {
        const response = await fetch(`${this.baseUrl}/sessions`);
        return response.json();
    }

    async createSession(sessionData) {
        const response = await fetch(`${this.baseUrl}/sessions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sessionData)
        });
        return response.json();
    }

    async getHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }
}

// 사용 예시
const client = new YesmanClient();

// 세션 목록 조회
client.getSessions().then(data => {
    console.log('Sessions:', data.sessions);
});

// 건강도 조회
client.getHealth().then(data => {
    console.log('Health score:', data.overall_score);
});
```

---

**마지막 업데이트**: 2025-08-19  
**API 버전**: v1.0  
**지원 프로토콜**: HTTP/1.1, WebSocket