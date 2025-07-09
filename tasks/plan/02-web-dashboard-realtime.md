# 🔄 Phase 2: Web Dashboard 실시간 기능

**Phase ID**: WEB-REALTIME  
**예상 시간**: 1주 (5일)  
**선행 조건**: Phase 1 완료 (웹 대시보드 기반 구조)  
**후행 Phase**: PHASE-3 공통 렌더러 시스템

## 🎯 Phase 목표

웹 대시보드에 실시간 업데이트 기능을 구현하여 세션 상태 변화와 프로젝트 활동을 실시간으로 모니터링할 수 있도록 한다.

## 📋 상세 작업 계획

### Day 1: WebSocket 인프라 구축

#### 1.1 FastAPI WebSocket 서버 구현
**파일**: `api/routers/websocket.py`
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    """WebSocket 연결 관리자"""
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
            "sessions": set(),
            "health": set(),
            "activity": set()
        }
        self.session_states: Dict[str, Dict] = {}
        self.health_data: Dict = {}
        self.activity_data: Dict = {}
        
    async def connect(self, websocket: WebSocket, channel: str = "dashboard"):
        await websocket.accept()
        self.active_connections[channel].add(websocket)
        logger.info(f"Client connected to {channel} channel")
        
        # 초기 데이터 전송
        await self.send_initial_data(websocket, channel)
        
    def disconnect(self, websocket: WebSocket, channel: str = "dashboard"):
        self.active_connections[channel].discard(websocket)
        logger.info(f"Client disconnected from {channel} channel")
        
    async def send_initial_data(self, websocket: WebSocket, channel: str):
        """연결 시 초기 데이터 전송"""
        initial_data = {
            "type": "initial",
            "channel": channel,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        if channel == "sessions":
            initial_data["data"] = {"sessions": self.session_states}
        elif channel == "health":
            initial_data["data"] = {"health": self.health_data}
        elif channel == "activity":
            initial_data["data"] = {"activity": self.activity_data}
        
        await websocket.send_json(initial_data)
        
    async def broadcast_to_channel(self, channel: str, message: dict):
        """특정 채널의 모든 클라이언트에게 메시지 전송"""
        disconnected = set()
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.add(connection)
                
        # 연결이 끊긴 클라이언트 제거
        for conn in disconnected:
            self.disconnect(conn, channel)
            
    async def broadcast_session_update(self, session_name: str, session_data: dict):
        """세션 업데이트 브로드캐스트"""
        self.session_states[session_name] = session_data
        
        message = {
            "type": "session_update",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "session_name": session_name,
                "session": session_data
            }
        }
        
        await self.broadcast_to_channel("sessions", message)
        await self.broadcast_to_channel("dashboard", message)
        
    async def broadcast_health_update(self, health_data: dict):
        """건강도 업데이트 브로드캐스트"""
        self.health_data = health_data
        
        message = {
            "type": "health_update",
            "timestamp": datetime.now().isoformat(),
            "data": {"health": health_data}
        }
        
        await self.broadcast_to_channel("health", message)
        await self.broadcast_to_channel("dashboard", message)
        
    async def broadcast_activity_update(self, activity_data: dict):
        """활동 데이터 업데이트 브로드캐스트"""
        self.activity_data = activity_data
        
        message = {
            "type": "activity_update",
            "timestamp": datetime.now().isoformat(),
            "data": {"activity": activity_data}
        }
        
        await self.broadcast_to_channel("activity", message)
        await self.broadcast_to_channel("dashboard", message)

# 전역 연결 관리자 인스턴스
manager = ConnectionManager()

@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """대시보드 WebSocket 엔드포인트"""
    await manager.connect(websocket, "dashboard")
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_json()
            
            # 요청 타입에 따른 처리
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            elif data.get("type") == "subscribe":
                # 특정 채널 구독 요청 처리
                channels = data.get("channels", [])
                for channel in channels:
                    if channel in manager.active_connections:
                        manager.active_connections[channel].add(websocket)
                        
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, "dashboard")

@router.websocket("/sessions")
async def websocket_sessions(websocket: WebSocket):
    """세션 전용 WebSocket 엔드포인트"""
    await manager.connect(websocket, "sessions")
    try:
        while True:
            await asyncio.sleep(1)  # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "sessions")

@router.websocket("/health")
async def websocket_health(websocket: WebSocket):
    """건강도 전용 WebSocket 엔드포인트"""
    await manager.connect(websocket, "health")
    try:
        while True:
            await asyncio.sleep(1)  # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "health")

@router.websocket("/activity")
async def websocket_activity(websocket: WebSocket):
    """활동 데이터 전용 WebSocket 엔드포인트"""
    await manager.connect(websocket, "activity")
    try:
        while True:
            await asyncio.sleep(1)  # Keep-alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "activity")
```

#### 1.2 백그라운드 태스크 시스템
**파일**: `api/background_tasks.py`
```python
import asyncio
from datetime import datetime
import logging
from typing import Optional

from libs.core.session_manager import SessionManager
from libs.dashboard.health_calculator import HealthCalculator
from api.routers.websocket import manager

logger = logging.getLogger(__name__)

class BackgroundTaskRunner:
    """백그라운드 태스크 실행기"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.health_calculator = HealthCalculator()
        self.running = False
        self.tasks = []
        
    async def start(self):
        """백그라운드 태스크 시작"""
        if self.running:
            return
            
        self.running = True
        
        # 각 태스크 시작
        self.tasks = [
            asyncio.create_task(self.monitor_sessions()),
            asyncio.create_task(self.monitor_health()),
            asyncio.create_task(self.monitor_activity()),
            asyncio.create_task(self.cleanup_connections())
        ]
        
        logger.info("Background tasks started")
        
    async def stop(self):
        """백그라운드 태스크 중지"""
        self.running = False
        
        # 모든 태스크 취소
        for task in self.tasks:
            task.cancel()
            
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Background tasks stopped")
        
    async def monitor_sessions(self):
        """세션 상태 모니터링"""
        last_sessions = {}
        
        while self.running:
            try:
                # 현재 세션 상태 가져오기
                current_sessions = self.session_manager.get_cached_sessions_list()
                
                # 변경 사항 감지
                for session in current_sessions:
                    session_name = session['session_name']
                    session_data = self.session_manager.get_session_info(session_name)
                    
                    # 이전 상태와 비교
                    if session_name not in last_sessions or last_sessions[session_name] != session_data:
                        # 변경사항 브로드캐스트
                        await manager.broadcast_session_update(session_name, session_data)
                        last_sessions[session_name] = session_data
                        
                # 삭제된 세션 처리
                removed_sessions = set(last_sessions.keys()) - set(s['session_name'] for s in current_sessions)
                for session_name in removed_sessions:
                    await manager.broadcast_session_update(session_name, {"status": "removed"})
                    del last_sessions[session_name]
                    
            except Exception as e:
                logger.error(f"Error monitoring sessions: {e}")
                
            await asyncio.sleep(1)  # 1초마다 체크
            
    async def monitor_health(self):
        """프로젝트 건강도 모니터링"""
        last_health = {}
        
        while self.running:
            try:
                # 건강도 계산
                health_data = await self.health_calculator.calculate_async()
                
                # 변경 사항 감지
                if health_data != last_health:
                    await manager.broadcast_health_update(health_data)
                    last_health = health_data
                    
            except Exception as e:
                logger.error(f"Error monitoring health: {e}")
                
            await asyncio.sleep(30)  # 30초마다 체크
            
    async def monitor_activity(self):
        """활동 데이터 모니터링"""
        while self.running:
            try:
                # 활동 데이터 수집 (git 활동, 세션 활동 등)
                activity_data = await self.collect_activity_data()
                
                # 업데이트 브로드캐스트
                await manager.broadcast_activity_update(activity_data)
                
            except Exception as e:
                logger.error(f"Error monitoring activity: {e}")
                
            await asyncio.sleep(60)  # 1분마다 체크
            
    async def collect_activity_data(self):
        """활동 데이터 수집"""
        # 실제 구현에서는 git log, 세션 활동 등을 수집
        return {
            "last_commit": datetime.now().isoformat(),
            "active_sessions": len(self.session_manager.get_cached_sessions_list()),
            "recent_activities": []
        }
        
    async def cleanup_connections(self):
        """오래된 연결 정리"""
        while self.running:
            try:
                # 연결 상태 점검 및 정리 로직
                pass
            except Exception as e:
                logger.error(f"Error cleaning up connections: {e}")
                
            await asyncio.sleep(300)  # 5분마다

# 전역 태스크 러너
task_runner = BackgroundTaskRunner()
```

### Day 2: 클라이언트 WebSocket 구현

#### 2.1 WebSocket 클라이언트 모듈
**파일**: `web-dashboard/static/js/utils/websocket.js`
```javascript
class WebSocketManager {
    constructor() {
        this.connections = {};
        this.reconnectInterval = 5000;
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = {};
        this.callbacks = {};
        this.isConnected = false;
    }
    
    connect(channel = 'dashboard') {
        if (this.connections[channel]) {
            console.warn(`Already connected to ${channel}`);
            return;
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws/${channel}`;
        
        console.log(`Connecting to WebSocket: ${url}`);
        
        const ws = new WebSocket(url);
        this.connections[channel] = ws;
        this.reconnectAttempts[channel] = 0;
        
        ws.onopen = () => {
            console.log(`WebSocket connected to ${channel}`);
            this.isConnected = true;
            this.reconnectAttempts[channel] = 0;
            
            // 연결 성공 콜백 실행
            this.trigger('connected', { channel });
            
            // 핑-퐁 시작
            this.startHeartbeat(channel);
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(channel, data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error(`WebSocket error on ${channel}:`, error);
            this.trigger('error', { channel, error });
        };
        
        ws.onclose = () => {
            console.log(`WebSocket disconnected from ${channel}`);
            this.isConnected = false;
            delete this.connections[channel];
            
            this.trigger('disconnected', { channel });
            
            // 자동 재연결
            if (this.reconnectAttempts[channel] < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts[channel]++;
                    console.log(`Reconnecting to ${channel}... (attempt ${this.reconnectAttempts[channel]})`);
                    this.connect(channel);
                }, this.reconnectInterval);
            }
        };
    }
    
    disconnect(channel = 'dashboard') {
        const ws = this.connections[channel];
        if (ws) {
            this.reconnectAttempts[channel] = this.maxReconnectAttempts; // 재연결 방지
            ws.close();
            delete this.connections[channel];
        }
    }
    
    send(channel, data) {
        const ws = this.connections[channel];
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
        } else {
            console.warn(`Cannot send message: ${channel} is not connected`);
        }
    }
    
    subscribe(channels) {
        this.send('dashboard', {
            type: 'subscribe',
            channels: channels
        });
    }
    
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
        
        return () => {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        };
    }
    
    off(event, callback) {
        if (this.callbacks[event]) {
            const index = this.callbacks[event].indexOf(callback);
            if (index > -1) {
                this.callbacks[event].splice(index, 1);
            }
        }
    }
    
    trigger(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} callback:`, error);
                }
            });
        }
    }
    
    handleMessage(channel, data) {
        console.log(`Received message on ${channel}:`, data);
        
        // 메시지 타입별 처리
        switch (data.type) {
            case 'initial':
                this.trigger('initial_data', { channel, data: data.data });
                break;
                
            case 'session_update':
                this.trigger('session_update', data.data);
                break;
                
            case 'health_update':
                this.trigger('health_update', data.data);
                break;
                
            case 'activity_update':
                this.trigger('activity_update', data.data);
                break;
                
            case 'pong':
                // 핑-퐁 응답 처리
                break;
                
            default:
                this.trigger('message', { channel, data });
        }
    }
    
    startHeartbeat(channel) {
        // 30초마다 핑 전송
        const intervalId = setInterval(() => {
            const ws = this.connections[channel];
            if (ws && ws.readyState === WebSocket.OPEN) {
                this.send(channel, { type: 'ping' });
            } else {
                clearInterval(intervalId);
            }
        }, 30000);
    }
}

// 전역 WebSocket 관리자
window.wsManager = new WebSocketManager();
```

#### 2.2 실시간 업데이트 통합
**파일**: `web-dashboard/static/js/main.js` (업데이트)
```javascript
// 기존 코드에 추가

// WebSocket 연결 초기화
document.addEventListener('DOMContentLoaded', () => {
    // WebSocket 연결
    window.wsManager.connect('dashboard');
    
    // 이벤트 리스너 등록
    window.wsManager.on('connected', (data) => {
        console.log('Connected to WebSocket:', data);
        showNotification('Connected to real-time updates', 'success');
    });
    
    window.wsManager.on('disconnected', (data) => {
        console.log('Disconnected from WebSocket:', data);
        showNotification('Disconnected from real-time updates', 'warning');
    });
    
    window.wsManager.on('session_update', (data) => {
        console.log('Session update:', data);
        updateSessionDisplay(data);
    });
    
    window.wsManager.on('health_update', (data) => {
        console.log('Health update:', data);
        updateHealthDisplay(data);
    });
    
    window.wsManager.on('activity_update', (data) => {
        console.log('Activity update:', data);
        updateActivityDisplay(data);
    });
    
    // 채널 구독
    window.wsManager.subscribe(['sessions', 'health', 'activity']);
});

// 실시간 업데이트 함수들
function updateSessionDisplay(data) {
    const sessionBrowser = document.querySelector('session-browser');
    if (sessionBrowser) {
        sessionBrowser.updateSession(data.session_name, data.session);
    }
    
    // 통계 업데이트
    const statsElement = document.querySelector('[x-data="dashboard()"]');
    if (statsElement && statsElement.__x) {
        statsElement.__x.$data.stats.activeSessions = Object.keys(window.wsManager.sessions || {}).length;
        statsElement.__x.$data.stats.lastUpdate = new Date().toLocaleString();
    }
}

function updateHealthDisplay(data) {
    const healthWidget = document.querySelector('health-widget');
    if (healthWidget) {
        healthWidget.updateHealth(data.health);
    }
}

function updateActivityDisplay(data) {
    const activityHeatmap = document.querySelector('activity-heatmap');
    if (activityHeatmap) {
        activityHeatmap.updateActivity(data.activity);
    }
}

// 알림 표시 함수
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg shadow-lg z-50 transition-all transform translate-x-0`;
    
    switch (type) {
        case 'success':
            notification.classList.add('bg-green-500', 'text-white');
            break;
        case 'warning':
            notification.classList.add('bg-yellow-500', 'text-white');
            break;
        case 'error':
            notification.classList.add('bg-red-500', 'text-white');
            break;
        default:
            notification.classList.add('bg-blue-500', 'text-white');
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // 3초 후 제거
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
```

### Day 3: 컴포넌트 실시간 업데이트 구현

#### 3.1 세션 브라우저 실시간 업데이트
**파일**: `web-dashboard/static/js/components/session-browser.js` (업데이트)
```javascript
// 기존 SessionBrowser 클래스에 추가

class SessionBrowser extends HTMLElement {
    constructor() {
        super();
        this.sessions = {};  // 객체로 변경하여 빠른 접근
        this.viewMode = 'list';
        this.autoUpdate = true;
    }
    
    connectedCallback() {
        this.render();
        this.loadSessions();
        this.setupRealtimeUpdates();
    }
    
    disconnectedCallback() {
        // 컴포넌트 제거 시 이벤트 리스너 정리
        if (this.unsubscribe) {
            this.unsubscribe();
        }
    }
    
    setupRealtimeUpdates() {
        // WebSocket 세션 업데이트 구독
        this.unsubscribe = window.wsManager.on('session_update', (data) => {
            this.updateSession(data.session_name, data.session);
        });
    }
    
    updateSession(sessionName, sessionData) {
        if (!this.autoUpdate) return;
        
        if (sessionData.status === 'removed') {
            // 세션 제거
            delete this.sessions[sessionName];
            this.animateRemoval(sessionName);
        } else {
            // 세션 추가/업데이트
            const isNew = !this.sessions[sessionName];
            this.sessions[sessionName] = sessionData;
            
            if (isNew) {
                this.animateAddition(sessionName);
            } else {
                this.animateUpdate(sessionName);
            }
        }
        
        // 디스플레이 업데이트
        this.render();
    }
    
    animateAddition(sessionName) {
        setTimeout(() => {
            const element = this.querySelector(`[data-session="${sessionName}"]`);
            if (element) {
                element.classList.add('animate-slide-in');
                element.style.backgroundColor = 'rgba(34, 197, 94, 0.1)';
                setTimeout(() => {
                    element.style.backgroundColor = '';
                }, 1000);
            }
        }, 10);
    }
    
    animateUpdate(sessionName) {
        const element = this.querySelector(`[data-session="${sessionName}"]`);
        if (element) {
            element.classList.add('animate-pulse-once');
            setTimeout(() => {
                element.classList.remove('animate-pulse-once');
            }, 1000);
        }
    }
    
    animateRemoval(sessionName) {
        const element = this.querySelector(`[data-session="${sessionName}"]`);
        if (element) {
            element.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
            element.style.opacity = '0';
            element.style.transform = 'translateX(-100%)';
            setTimeout(() => {
                element.remove();
            }, 300);
        }
    }
    
    renderListView() {
        const sessionArray = Object.entries(this.sessions).map(([name, data]) => ({
            name,
            ...data
        }));
        
        return `
            <div class="space-y-2">
                ${sessionArray.map(session => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg transition-all duration-300"
                         data-session="${session.name}">
                        <div class="flex items-center space-x-3">
                            <div class="relative">
                                <div class="w-3 h-3 rounded-full ${session.active ? 'bg-green-500' : 'bg-gray-400'}"></div>
                                ${session.active ? `
                                    <div class="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping"></div>
                                ` : ''}
                            </div>
                            <span class="font-medium">${session.name}</span>
                            <span class="text-sm text-gray-500">${session.windows?.length || 0} windows</span>
                            ${session.last_activity ? `
                                <span class="text-xs text-gray-400">Active ${this.formatTimeAgo(session.last_activity)}</span>
                            ` : ''}
                        </div>
                        <div class="flex items-center space-x-2">
                            ${session.claude_active ? `
                                <span class="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">Claude Active</span>
                            ` : ''}
                            <button class="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                                    onclick="window.enterSession('${session.name}')">
                                Enter
                            </button>
                            <button class="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                                    onclick="window.stopSession('${session.name}')">
                                Stop
                            </button>
                        </div>
                    </div>
                `).join('')}
                
                ${sessionArray.length === 0 ? `
                    <div class="text-center py-8 text-gray-500">
                        <div class="text-4xl mb-2">🖥️</div>
                        <p>No active sessions</p>
                        <button class="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                                onclick="window.createNewSession()">
                            Create Session
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    formatTimeAgo(timestamp) {
        const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
        
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    }
}
```

### Day 4: 고급 실시간 기능

#### 4.1 서버 전송 이벤트(SSE) 대안 구현
**파일**: `api/routers/sse.py`
```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator

router = APIRouter(prefix="/sse", tags=["server-sent-events"])

async def event_generator(request: Request) -> AsyncGenerator:
    """SSE 이벤트 생성기"""
    client_id = id(request)
    
    try:
        while True:
            # 연결 유지를 위한 주석 전송
            if await request.is_disconnected():
                break
                
            # 실시간 데이터 전송
            data = {
                "timestamp": datetime.now().isoformat(),
                "sessions": await get_session_summary(),
                "health": await get_health_summary()
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            
            await asyncio.sleep(2)  # 2초마다 업데이트
            
    except asyncio.CancelledError:
        pass
    finally:
        print(f"SSE client {client_id} disconnected")

@router.get("/stream")
async def sse_stream(request: Request):
    """SSE 스트림 엔드포인트"""
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx 버퍼링 비활성화
        }
    )

async def get_session_summary():
    """세션 요약 정보"""
    # 실제 구현에서는 SessionManager 사용
    return {
        "active": 5,
        "total": 8,
        "recent_activity": "2 minutes ago"
    }

async def get_health_summary():
    """건강도 요약 정보"""
    # 실제 구현에서는 HealthCalculator 사용
    return {
        "score": 85,
        "trend": "improving",
        "issues": 2
    }
```

#### 4.2 실시간 로그 스트리밍
**파일**: `web-dashboard/static/js/components/log-viewer.js`
```javascript
class LogViewer extends HTMLElement {
    constructor() {
        super();
        this.logs = [];
        this.maxLogs = 1000;
        this.filters = {
            level: 'all',
            source: 'all',
            search: ''
        };
        this.autoScroll = true;
        this.isPaused = false;
    }
    
    connectedCallback() {
        this.render();
        this.setupLogStream();
    }
    
    setupLogStream() {
        // WebSocket을 통한 로그 스트리밍
        window.wsManager.on('log_entry', (data) => {
            if (!this.isPaused) {
                this.addLog(data);
            }
        });
    }
    
    addLog(logEntry) {
        this.logs.push({
            ...logEntry,
            id: Date.now() + Math.random()
        });
        
        // 최대 로그 수 제한
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }
        
        // 필터링된 로그만 표시
        if (this.matchesFilters(logEntry)) {
            this.appendLogElement(logEntry);
            
            if (this.autoScroll) {
                this.scrollToBottom();
            }
        }
    }
    
    matchesFilters(log) {
        // 레벨 필터
        if (this.filters.level !== 'all' && log.level !== this.filters.level) {
            return false;
        }
        
        // 소스 필터
        if (this.filters.source !== 'all' && log.source !== this.filters.source) {
            return false;
        }
        
        // 검색 필터
        if (this.filters.search && !log.message.toLowerCase().includes(this.filters.search.toLowerCase())) {
            return false;
        }
        
        return true;
    }
    
    render() {
        this.innerHTML = `
            <div class="flex flex-col h-full">
                <!-- 컨트롤 바 -->
                <div class="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 border-b">
                    <div class="flex items-center space-x-2">
                        <!-- 필터 선택 -->
                        <select class="px-2 py-1 text-sm border rounded" onchange="this.closest('log-viewer').setFilter('level', this.value)">
                            <option value="all">All Levels</option>
                            <option value="debug">Debug</option>
                            <option value="info">Info</option>
                            <option value="warning">Warning</option>
                            <option value="error">Error</option>
                        </select>
                        
                        <input type="text" 
                               placeholder="Search logs..." 
                               class="px-2 py-1 text-sm border rounded"
                               oninput="this.closest('log-viewer').setFilter('search', this.value)">
                    </div>
                    
                    <div class="flex items-center space-x-2">
                        <!-- 컨트롤 버튼 -->
                        <button class="px-2 py-1 text-sm bg-blue-500 text-white rounded ${this.isPaused ? '' : 'opacity-50'}"
                                onclick="this.closest('log-viewer').togglePause()">
                            ${this.isPaused ? '▶️ Resume' : '⏸️ Pause'}
                        </button>
                        
                        <button class="px-2 py-1 text-sm bg-gray-500 text-white rounded"
                                onclick="this.closest('log-viewer').clearLogs()">
                            🗑️ Clear
                        </button>
                        
                        <label class="flex items-center text-sm">
                            <input type="checkbox" 
                                   ${this.autoScroll ? 'checked' : ''} 
                                   onchange="this.closest('log-viewer').autoScroll = this.checked">
                            <span class="ml-1">Auto-scroll</span>
                        </label>
                    </div>
                </div>
                
                <!-- 로그 컨테이너 -->
                <div class="flex-1 overflow-y-auto font-mono text-sm p-2 bg-gray-900 text-gray-100" 
                     id="log-container">
                    ${this.renderLogs()}
                </div>
                
                <!-- 상태 바 -->
                <div class="p-1 bg-gray-100 dark:bg-gray-800 border-t text-xs text-gray-600">
                    <span>${this.logs.length} logs</span>
                    ${this.isPaused ? '<span class="ml-2 text-yellow-600">• Paused</span>' : ''}
                </div>
            </div>
        `;
    }
    
    renderLogs() {
        const filteredLogs = this.logs.filter(log => this.matchesFilters(log));
        
        return filteredLogs.map(log => `
            <div class="log-entry ${this.getLogClass(log.level)}" data-log-id="${log.id}">
                <span class="text-gray-500">${this.formatTimestamp(log.timestamp)}</span>
                <span class="level-badge ${this.getLevelClass(log.level)}">${log.level}</span>
                <span class="text-blue-400">[${log.source}]</span>
                <span class="message">${this.escapeHtml(log.message)}</span>
            </div>
        `).join('');
    }
    
    appendLogElement(log) {
        const container = this.querySelector('#log-container');
        const logHtml = `
            <div class="log-entry ${this.getLogClass(log.level)} animate-fade-in" data-log-id="${log.id}">
                <span class="text-gray-500">${this.formatTimestamp(log.timestamp)}</span>
                <span class="level-badge ${this.getLevelClass(log.level)}">${log.level}</span>
                <span class="text-blue-400">[${log.source}]</span>
                <span class="message">${this.escapeHtml(log.message)}</span>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', logHtml);
        
        // 오래된 엘리먼트 제거
        const allEntries = container.querySelectorAll('.log-entry');
        if (allEntries.length > this.maxLogs) {
            allEntries[0].remove();
        }
    }
    
    getLogClass(level) {
        const classes = {
            'debug': 'text-gray-400',
            'info': 'text-gray-200',
            'warning': 'text-yellow-400',
            'error': 'text-red-400'
        };
        return classes[level] || '';
    }
    
    getLevelClass(level) {
        const classes = {
            'debug': 'text-gray-500',
            'info': 'text-blue-500',
            'warning': 'text-yellow-500',
            'error': 'text-red-500'
        };
        return classes[level] || '';
    }
    
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            fractionalSecondDigits: 3
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    setFilter(type, value) {
        this.filters[type] = value;
        this.render();
    }
    
    togglePause() {
        this.isPaused = !this.isPaused;
        this.render();
    }
    
    clearLogs() {
        this.logs = [];
        this.render();
    }
    
    scrollToBottom() {
        const container = this.querySelector('#log-container');
        container.scrollTop = container.scrollHeight;
    }
}

customElements.define('log-viewer', LogViewer);
```

### Day 5: 성능 최적화 및 테스트

#### 5.1 WebSocket 연결 풀링
**파일**: `web-dashboard/static/js/utils/connection-pool.js`
```javascript
class ConnectionPool {
    constructor(maxConnections = 5) {
        this.maxConnections = maxConnections;
        this.connections = new Map();
        this.messageQueue = new Map();
        this.roundRobinIndex = 0;
    }
    
    getConnection(channel) {
        // 채널별 연결 풀 관리
        if (!this.connections.has(channel)) {
            this.connections.set(channel, []);
        }
        
        const pool = this.connections.get(channel);
        
        // 연결이 부족하면 새로 생성
        if (pool.length < this.maxConnections) {
            const conn = this.createConnection(channel);
            pool.push(conn);
            return conn;
        }
        
        // 라운드 로빈으로 연결 선택
        const conn = pool[this.roundRobinIndex % pool.length];
        this.roundRobinIndex++;
        return conn;
    }
    
    createConnection(channel) {
        const ws = new WebSocket(`ws://${window.location.host}/ws/${channel}`);
        
        ws.onopen = () => {
            // 큐에 있던 메시지 전송
            const queue = this.messageQueue.get(channel) || [];
            queue.forEach(msg => ws.send(JSON.stringify(msg)));
            this.messageQueue.delete(channel);
        };
        
        ws.onerror = (error) => {
            console.error(`Connection error on ${channel}:`, error);
            this.removeConnection(channel, ws);
        };
        
        ws.onclose = () => {
            this.removeConnection(channel, ws);
        };
        
        return ws;
    }
    
    removeConnection(channel, ws) {
        const pool = this.connections.get(channel) || [];
        const index = pool.indexOf(ws);
        if (index > -1) {
            pool.splice(index, 1);
        }
    }
    
    send(channel, data) {
        const conn = this.getConnection(channel);
        
        if (conn.readyState === WebSocket.OPEN) {
            conn.send(JSON.stringify(data));
        } else {
            // 연결이 아직 열리지 않았으면 큐에 저장
            if (!this.messageQueue.has(channel)) {
                this.messageQueue.set(channel, []);
            }
            this.messageQueue.get(channel).push(data);
        }
    }
    
    broadcast(data) {
        // 모든 채널에 브로드캐스트
        for (const [channel, pool] of this.connections) {
            pool.forEach(conn => {
                if (conn.readyState === WebSocket.OPEN) {
                    conn.send(JSON.stringify(data));
                }
            });
        }
    }
    
    closeAll() {
        for (const [channel, pool] of this.connections) {
            pool.forEach(conn => conn.close());
        }
        this.connections.clear();
    }
}

// 전역 연결 풀
window.connectionPool = new ConnectionPool();
```

#### 5.2 메시지 배치 처리
**파일**: `api/utils/batch_processor.py`
```python
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import json

class MessageBatchProcessor:
    """WebSocket 메시지 배치 처리기"""
    
    def __init__(self, batch_size: int = 10, batch_interval: float = 0.1):
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.message_queues: Dict[str, List[Dict]] = {}
        self.processing = False
        
    async def start(self):
        """배치 처리 시작"""
        self.processing = True
        asyncio.create_task(self.process_batches())
        
    async def stop(self):
        """배치 처리 중지"""
        self.processing = False
        
    async def add_message(self, channel: str, message: Dict[str, Any]):
        """메시지를 배치 큐에 추가"""
        if channel not in self.message_queues:
            self.message_queues[channel] = []
            
        self.message_queues[channel].append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 배치 크기 도달 시 즉시 처리
        if len(self.message_queues[channel]) >= self.batch_size:
            await self.process_channel_batch(channel)
            
    async def process_batches(self):
        """주기적으로 배치 처리"""
        while self.processing:
            for channel in list(self.message_queues.keys()):
                if self.message_queues[channel]:
                    await self.process_channel_batch(channel)
                    
            await asyncio.sleep(self.batch_interval)
            
    async def process_channel_batch(self, channel: str):
        """특정 채널의 배치 처리"""
        if channel not in self.message_queues or not self.message_queues[channel]:
            return
            
        # 배치 추출
        batch = self.message_queues[channel][:self.batch_size]
        self.message_queues[channel] = self.message_queues[channel][self.batch_size:]
        
        # 배치 메시지 생성
        batch_message = {
            "type": "batch",
            "channel": channel,
            "messages": batch,
            "batch_size": len(batch),
            "timestamp": datetime.now().isoformat()
        }
        
        # WebSocket 매니저로 전송
        from api.routers.websocket import manager
        await manager.broadcast_to_channel(channel, batch_message)
        
    def get_queue_status(self) -> Dict[str, int]:
        """큐 상태 조회"""
        return {
            channel: len(queue) 
            for channel, queue in self.message_queues.items()
        }
```

## ✅ Phase 2 완료 기준

### 기능적 요구사항
- [ ] WebSocket 연결 및 자동 재연결
- [ ] 실시간 세션 상태 업데이트
- [ ] 실시간 건강도 모니터링
- [ ] 실시간 활동 데이터 업데이트
- [ ] 로그 스트리밍 기능
- [ ] 연결 상태 표시 및 알림

### 기술적 요구사항
- [ ] WebSocket 서버 구현
- [ ] 클라이언트 WebSocket 관리자
- [ ] 백그라운드 태스크 시스템
- [ ] 메시지 배치 처리
- [ ] 연결 풀링 구현
- [ ] SSE 대안 구현

### 성능 요구사항
- [ ] 100개 동시 연결 지원
- [ ] 메시지 지연 시간 < 100ms
- [ ] 자동 재연결 시간 < 5초
- [ ] 메모리 사용량 안정적
- [ ] CPU 사용률 < 10%

### 테스트 요구사항
- [ ] WebSocket 연결 테스트
- [ ] 메시지 송수신 테스트
- [ ] 재연결 시나리오 테스트
- [ ] 다중 클라이언트 테스트
- [ ] 부하 테스트

## 🔧 테스트 및 디버깅

### 테스트 명령어
```bash
# WebSocket 테스트 클라이언트
python -m pytest tests/test_websocket.py

# 부하 테스트
locust -f tests/load_test.py --host=http://localhost:8000

# WebSocket 디버깅
wscat -c ws://localhost:8000/ws/dashboard
```

### 모니터링 도구
- Chrome DevTools WebSocket 프레임 검사
- `websocat` CLI 도구
- FastAPI `/docs` WebSocket 테스트
- 실시간 로그 모니터링

---

**다음 단계**: Phase 2 완료 후 `03-common-renderer-system.md` 진행