# 🏗️ Phase 1: Web Dashboard 기반 구조

**Phase ID**: WEB-FOUNDATION  
**예상 시간**: 1주 (5일)  
**선행 조건**: 없음  
**후행 Phase**: PHASE-2 실시간 기능

## 🎯 Phase 목표

웹 대시보드의 기본 구조를 생성하고 정적 데이터 표시 기능을 구현한다.

## 📋 상세 작업 계획

### Day 1: 프로젝트 구조 및 환경 설정

#### 1.1 웹 대시보드 디렉토리 구조 생성
```bash
mkdir -p web-dashboard/{static/{js/{components,utils},css/{components,themes},templates},tests}
mkdir -p libs/dashboard/renderers
```

#### 1.2 패키지 관리 설정
```bash
# web-dashboard/package.json 생성
cd web-dashboard
npm init -y
npm install -D esbuild tailwindcss @tailwindcss/forms prettier eslint
npm install alpinejs axios socket.io-client chart.js
```

#### 1.3 빌드 시스템 구성
**파일**: `web-dashboard/build.js`
```javascript
// esbuild 설정으로 JS/CSS 번들링
// 개발/프로덕션 모드 지원
// 자동 리로드 기능
```

**파일**: `web-dashboard/tailwind.config.js`
```javascript
// Tauri 대시보드와 동일한 테마 설정
// 컴포넌트별 스타일 정의
```

#### 1.4 FastAPI 라우터 확장
**파일**: `api/routers/dashboard.py`
```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/web", tags=["web-dashboard"])
templates = Jinja2Templates(directory="web-dashboard/static/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """웹 대시보드 메인 페이지"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/api/sessions")
async def get_sessions():
    """세션 목록 API"""
    pass

@router.get("/api/health")
async def get_project_health():
    """프로젝트 건강도 API"""
    pass
```

### Day 2: HTML 템플릿 및 기본 레이아웃

#### 2.1 기본 HTML 템플릿
**파일**: `web-dashboard/static/templates/layout.html`
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Yesman Claude Dashboard{% endblock %}</title>
    <link href="/static/css/main.css" rel="stylesheet">
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-100 dark:bg-gray-900">
    <!-- 네비게이션 바 -->
    <nav class="bg-white dark:bg-gray-800 shadow-lg">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-semibold">Yesman Claude</h1>
                    <!-- 인터페이스 전환 버튼 -->
                    <div class="ml-6 flex space-x-4">
                        <button class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900">Web</button>
                        <button class="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">TUI</button>
                        <button class="px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">Desktop</button>
                    </div>
                </div>
                <!-- 다크모드 토글, 설정 등 -->
                <div class="flex items-center space-x-4">
                    <button id="theme-toggle" class="p-2 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700">
                        🌙
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- 메인 컨텐츠 -->
    <main class="max-w-7xl mx-auto py-6 px-4">
        {% block content %}{% endblock %}
    </main>

    <script src="/static/js/main.js"></script>
</body>
</html>
```

#### 2.2 대시보드 메인 페이지
**파일**: `web-dashboard/static/templates/dashboard.html`
```html
{% extends "layout.html" %}

{% block content %}
<div x-data="dashboard()" class="space-y-6">
    <!-- 상태 요약 카드 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div class="p-5">
                <div class="flex items-center">
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                            ✓
                        </div>
                    </div>
                    <div class="ml-5 w-0 flex-1">
                        <dl>
                            <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                                Active Sessions
                            </dt>
                            <dd class="text-lg font-medium text-gray-900 dark:text-white" x-text="stats.activeSessions">
                                --
                            </dd>
                        </dl>
                    </div>
                </div>
            </div>
        </div>

        <!-- 더 많은 상태 카드들... -->
    </div>

    <!-- 세션 브라우저 컴포넌트 -->
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                Session Browser
            </h3>
            <div class="mt-5">
                <session-browser></session-browser>
            </div>
        </div>
    </div>

    <!-- 프로젝트 건강도 위젯 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                    Project Health
                </h3>
                <div class="mt-5">
                    <health-widget></health-widget>
                </div>
            </div>
        </div>

        <!-- 활동 히트맵 -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
                <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                    Activity Heatmap
                </h3>
                <div class="mt-5">
                    <activity-heatmap></activity-heatmap>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Day 3: JavaScript 컴포넌트 기반 구조

#### 3.1 메인 JavaScript 파일
**파일**: `web-dashboard/static/js/main.js`
```javascript
// 전역 상태 관리
window.dashboard = {
    state: {
        sessions: [],
        health: {},
        theme: 'light'
    },
    
    api: {
        async getSessions() {
            const response = await fetch('/web/api/sessions');
            return response.json();
        },
        
        async getHealth() {
            const response = await fetch('/web/api/health');
            return response.json();
        }
    },
    
    utils: {
        formatDate(date) {
            return new Date(date).toLocaleString();
        },
        
        toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.classList.contains('dark') ? 'dark' : 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.classList.toggle('dark');
            localStorage.setItem('theme', newTheme);
            this.state.theme = newTheme;
        }
    }
};

// Alpine.js 컴포넌트
function dashboard() {
    return {
        stats: {
            activeSessions: 0,
            totalProjects: 0,
            healthScore: 0,
            lastUpdate: null
        },
        
        async init() {
            await this.loadData();
            this.setupTheme();
        },
        
        async loadData() {
            try {
                const [sessions, health] = await Promise.all([
                    window.dashboard.api.getSessions(),
                    window.dashboard.api.getHealth()
                ]);
                
                this.stats.activeSessions = sessions.length;
                this.stats.healthScore = health.overall_score;
                this.stats.lastUpdate = new Date().toLocaleString();
            } catch (error) {
                console.error('Failed to load data:', error);
            }
        },
        
        setupTheme() {
            const savedTheme = localStorage.getItem('theme') || 'light';
            if (savedTheme === 'dark') {
                document.documentElement.classList.add('dark');
            }
            window.dashboard.state.theme = savedTheme;
        }
    };
}

// 전역 초기화
document.addEventListener('DOMContentLoaded', () => {
    // 테마 토글 이벤트
    document.getElementById('theme-toggle')?.addEventListener('click', () => {
        window.dashboard.utils.toggleTheme();
    });
});
```

#### 3.2 세션 브라우저 컴포넌트
**파일**: `web-dashboard/static/js/components/session-browser.js`
```javascript
class SessionBrowser extends HTMLElement {
    constructor() {
        super();
        this.sessions = [];
        this.viewMode = 'list'; // list, grid, tree
    }
    
    connectedCallback() {
        this.render();
        this.loadSessions();
    }
    
    async loadSessions() {
        try {
            this.sessions = await window.dashboard.api.getSessions();
            this.render();
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }
    
    render() {
        this.innerHTML = `
            <div class="space-y-4">
                <!-- 뷰 모드 선택 -->
                <div class="flex space-x-2">
                    <button class="px-3 py-2 text-sm bg-blue-500 text-white rounded ${this.viewMode === 'list' ? 'ring-2 ring-blue-300' : ''}" 
                            onclick="this.parentElement.parentElement.parentElement.changeViewMode('list')">
                        List
                    </button>
                    <button class="px-3 py-2 text-sm bg-blue-500 text-white rounded ${this.viewMode === 'grid' ? 'ring-2 ring-blue-300' : ''}"
                            onclick="this.parentElement.parentElement.parentElement.changeViewMode('grid')">
                        Grid
                    </button>
                    <button class="px-3 py-2 text-sm bg-blue-500 text-white rounded ${this.viewMode === 'tree' ? 'ring-2 ring-blue-300' : ''}"
                            onclick="this.parentElement.parentElement.parentElement.changeViewMode('tree')">
                        Tree
                    </button>
                </div>
                
                <!-- 세션 목록 -->
                <div class="sessions-container">
                    ${this.renderSessions()}
                </div>
            </div>
        `;
    }
    
    renderSessions() {
        if (this.sessions.length === 0) {
            return '<p class="text-gray-500">No active sessions</p>';
        }
        
        switch (this.viewMode) {
            case 'list':
                return this.renderListView();
            case 'grid':
                return this.renderGridView();
            case 'tree':
                return this.renderTreeView();
            default:
                return this.renderListView();
        }
    }
    
    renderListView() {
        return `
            <div class="space-y-2">
                ${this.sessions.map(session => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div class="flex items-center space-x-3">
                            <div class="w-3 h-3 bg-green-500 rounded-full ${session.active ? 'bg-green-500' : 'bg-gray-400'}"></div>
                            <span class="font-medium">${session.name}</span>
                            <span class="text-sm text-gray-500">${session.windows?.length || 0} windows</span>
                        </div>
                        <div class="flex space-x-2">
                            <button class="px-2 py-1 text-xs bg-blue-500 text-white rounded">View</button>
                            <button class="px-2 py-1 text-xs bg-red-500 text-white rounded">Stop</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderGridView() {
        return `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${this.sessions.map(session => `
                    <div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow border">
                        <div class="flex items-center justify-between mb-2">
                            <h4 class="font-medium">${session.name}</h4>
                            <div class="w-3 h-3 rounded-full ${session.active ? 'bg-green-500' : 'bg-gray-400'}"></div>
                        </div>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                            ${session.windows?.length || 0} windows, ${session.panes?.length || 0} panes
                        </p>
                        <div class="flex space-x-2">
                            <button class="flex-1 px-2 py-1 text-xs bg-blue-500 text-white rounded">View</button>
                            <button class="flex-1 px-2 py-1 text-xs bg-red-500 text-white rounded">Stop</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderTreeView() {
        return `
            <div class="space-y-1">
                ${this.sessions.map(session => `
                    <details class="bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <summary class="p-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg">
                            <span class="inline-flex items-center space-x-2">
                                <div class="w-3 h-3 rounded-full ${session.active ? 'bg-green-500' : 'bg-gray-400'}"></div>
                                <span class="font-medium">${session.name}</span>
                                <span class="text-sm text-gray-500">(${session.windows?.length || 0} windows)</span>
                            </span>
                        </summary>
                        <div class="px-6 pb-3">
                            ${(session.windows || []).map(window => `
                                <div class="flex items-center space-x-2 py-1 text-sm">
                                    <span class="text-gray-400">├─</span>
                                    <span>${window.name}</span>
                                    <span class="text-gray-500">(${window.panes?.length || 0} panes)</span>
                                </div>
                            `).join('')}
                        </div>
                    </details>
                `).join('')}
            </div>
        `;
    }
    
    changeViewMode(mode) {
        this.viewMode = mode;
        this.render();
    }
}

customElements.define('session-browser', SessionBrowser);
```

### Day 4: 프로젝트 건강도 및 활동 위젯

#### 4.1 프로젝트 건강도 위젯
**파일**: `web-dashboard/static/js/components/health-widget.js`
```javascript
class HealthWidget extends HTMLElement {
    constructor() {
        super();
        this.health = null;
    }
    
    connectedCallback() {
        this.render();
        this.loadHealth();
    }
    
    async loadHealth() {
        try {
            this.health = await window.dashboard.api.getHealth();
            this.render();
        } catch (error) {
            console.error('Failed to load health data:', error);
        }
    }
    
    render() {
        if (!this.health) {
            this.innerHTML = '<div class="animate-pulse">Loading health data...</div>';
            return;
        }
        
        this.innerHTML = `
            <div class="space-y-4">
                <!-- 전체 건강도 점수 -->
                <div class="text-center">
                    <div class="text-3xl font-bold ${this.getScoreColor(this.health.overall_score)}">
                        ${this.health.overall_score}/100
                    </div>
                    <div class="text-sm text-gray-500">Overall Health Score</div>
                </div>
                
                <!-- 카테고리별 상세 점수 -->
                <div class="space-y-3">
                    ${Object.entries(this.health.categories || {}).map(([category, data]) => `
                        <div class="flex items-center justify-between">
                            <span class="text-sm font-medium">${this.formatCategoryName(category)}</span>
                            <div class="flex items-center space-x-2">
                                <div class="w-24 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                    <div class="h-2 rounded-full ${this.getScoreColor(data.score)}" 
                                         style="width: ${data.score}%"></div>
                                </div>
                                <span class="text-sm font-medium w-8">${data.score}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <!-- 개선 제안 -->
                ${this.health.suggestions?.length > 0 ? `
                    <div class="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                        <h4 class="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                            Improvement Suggestions
                        </h4>
                        <ul class="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                            ${this.health.suggestions.map(suggestion => `
                                <li>• ${suggestion}</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    getScoreColor(score) {
        if (score >= 80) return 'text-green-500 bg-green-500';
        if (score >= 60) return 'text-yellow-500 bg-yellow-500';
        return 'text-red-500 bg-red-500';
    }
    
    formatCategoryName(category) {
        return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
}

customElements.define('health-widget', HealthWidget);
```

#### 4.2 활동 히트맵 위젯
**파일**: `web-dashboard/static/js/components/activity-heatmap.js`
```javascript
class ActivityHeatmap extends HTMLElement {
    constructor() {
        super();
        this.activityData = null;
    }
    
    connectedCallback() {
        this.render();
        this.loadActivityData();
    }
    
    async loadActivityData() {
        try {
            const response = await fetch('/web/api/activity');
            this.activityData = await response.json();
            this.render();
        } catch (error) {
            console.error('Failed to load activity data:', error);
        }
    }
    
    render() {
        if (!this.activityData) {
            this.innerHTML = '<div class="animate-pulse">Loading activity data...</div>';
            return;
        }
        
        this.innerHTML = `
            <div class="space-y-4">
                <!-- 히트맵 그리드 -->
                <div class="heatmap-grid">
                    ${this.renderHeatmapGrid()}
                </div>
                
                <!-- 범례 -->
                <div class="flex items-center justify-between text-sm text-gray-500">
                    <span>Less</span>
                    <div class="flex space-x-1">
                        <div class="w-3 h-3 bg-gray-200 dark:bg-gray-700 rounded-sm"></div>
                        <div class="w-3 h-3 bg-green-200 dark:bg-green-800 rounded-sm"></div>
                        <div class="w-3 h-3 bg-green-400 dark:bg-green-600 rounded-sm"></div>
                        <div class="w-3 h-3 bg-green-600 dark:bg-green-400 rounded-sm"></div>
                        <div class="w-3 h-3 bg-green-800 dark:bg-green-200 rounded-sm"></div>
                    </div>
                    <span>More</span>
                </div>
                
                <!-- 통계 -->
                <div class="text-center text-sm text-gray-600 dark:text-gray-400">
                    ${this.activityData.total_days} days tracked • 
                    ${this.activityData.active_days} active days • 
                    ${Math.round((this.activityData.active_days / this.activityData.total_days) * 100)}% active
                </div>
            </div>
        `;
    }
    
    renderHeatmapGrid() {
        const weeks = this.groupByWeeks(this.activityData.days);
        const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        return `
            <div class="grid grid-cols-${weeks.length + 1} gap-1 text-xs">
                <!-- 요일 라벨 -->
                <div class="flex flex-col space-y-1">
                    <div class="h-3"></div>
                    ${dayLabels.map((day, index) => `
                        <div class="h-3 flex items-center ${index % 2 === 0 ? 'text-gray-500' : ''}">${index % 2 === 0 ? day : ''}</div>
                    `).join('')}
                </div>
                
                <!-- 주별 컬럼 -->
                ${weeks.map(week => `
                    <div class="flex flex-col space-y-1">
                        <div class="h-3 text-gray-500 text-center">${this.getWeekLabel(week[0])}</div>
                        ${week.map(day => `
                            <div class="w-3 h-3 rounded-sm cursor-pointer ${this.getActivityColor(day.activity)}"
                                 title="${day.date}: ${day.activity} activities"
                                 data-date="${day.date}">
                            </div>
                        `).join('')}
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    groupByWeeks(days) {
        const weeks = [];
        let currentWeek = [];
        
        days.forEach(day => {
            const dayOfWeek = new Date(day.date).getDay();
            
            if (dayOfWeek === 0 && currentWeek.length > 0) {
                weeks.push(currentWeek);
                currentWeek = [];
            }
            
            currentWeek.push(day);
        });
        
        if (currentWeek.length > 0) {
            weeks.push(currentWeek);
        }
        
        return weeks;
    }
    
    getActivityColor(activityCount) {
        if (activityCount === 0) return 'bg-gray-200 dark:bg-gray-700';
        if (activityCount <= 2) return 'bg-green-200 dark:bg-green-800';
        if (activityCount <= 5) return 'bg-green-400 dark:bg-green-600';
        if (activityCount <= 10) return 'bg-green-600 dark:bg-green-400';
        return 'bg-green-800 dark:bg-green-200';
    }
    
    getWeekLabel(firstDayOfWeek) {
        const date = new Date(firstDayOfWeek.date);
        const month = date.getMonth() + 1;
        const day = date.getDate();
        
        // 매월 첫 주만 라벨 표시
        if (day <= 7) {
            return month.toString();
        }
        return '';
    }
}

customElements.define('activity-heatmap', ActivityHeatmap);
```

### Day 5: CSS 스타일링 및 통합

#### 5.1 메인 스타일시트
**파일**: `web-dashboard/static/css/main.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* 커스텀 컴포넌트 스타일 */
@layer components {
    .heatmap-grid {
        @apply overflow-x-auto;
    }
    
    .session-card {
        @apply bg-white dark:bg-gray-800 rounded-lg shadow border;
        transition: all 0.2s ease-in-out;
    }
    
    .session-card:hover {
        @apply shadow-md border-blue-200 dark:border-blue-700;
    }
    
    .health-progress {
        @apply transition-all duration-300 ease-in-out;
    }
    
    .activity-cell {
        @apply transition-colors duration-200;
    }
    
    .activity-cell:hover {
        @apply ring-2 ring-blue-300 ring-opacity-50;
    }
}

/* 다크 모드 토글 애니메이션 */
.theme-transition {
    transition: background-color 0.3s ease, color 0.3s ease;
}

/* 로딩 애니메이션 */
@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: .5;
    }
}

.animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* 반응형 그리드 조정 */
@media (max-width: 768px) {
    .heatmap-grid {
        @apply text-xs;
    }
    
    .heatmap-grid .w-3 {
        @apply w-2;
    }
    
    .heatmap-grid .h-3 {
        @apply h-2;
    }
}
```

#### 5.2 FastAPI 라우터 구현 완성
**파일**: `api/routers/dashboard.py`
```python
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any
import asyncio
from datetime import datetime, timedelta
import random

from libs.dashboard.widgets.session_browser import SessionBrowser
from libs.dashboard.widgets.project_health import ProjectHealth
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmap
from libs.core.session_manager import SessionManager

router = APIRouter(prefix="/web", tags=["web-dashboard"])
templates = Jinja2Templates(directory="web-dashboard/static/templates")

# SessionManager 인스턴스
session_manager = SessionManager()

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """웹 대시보드 메인 페이지"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Yesman Claude Dashboard"
    })

@router.get("/api/sessions")
async def get_sessions():
    """세션 목록 조회"""
    try:
        # SessionManager에서 세션 정보 조회
        sessions = session_manager.get_cached_sessions_list()
        
        # 웹 인터페이스용 데이터 형식으로 변환
        web_sessions = []
        for session in sessions:
            session_detail = session_manager.get_session_info(session['session_name'])
            web_sessions.append({
                'name': session['session_name'],
                'id': session['session_id'],
                'active': True,  # 활성 세션 목록이므로
                'created': session.get('session_created'),
                'windows': session_detail.get('windows', []),
                'panes': sum(len(w.get('panes', [])) for w in session_detail.get('windows', []))
            })
        
        return {
            "sessions": web_sessions,
            "total": len(web_sessions),
            "active": len(web_sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.get("/api/health")
async def get_project_health():
    """프로젝트 건강도 조회"""
    try:
        # ProjectHealth 위젯 사용
        health_widget = ProjectHealth()
        health_data = health_widget.calculate_health()
        
        return {
            "overall_score": health_data.get('overall_score', 75),
            "categories": {
                "build": {"score": health_data.get('build_score', 85), "status": "good"},
                "tests": {"score": health_data.get('test_score', 70), "status": "warning"},
                "dependencies": {"score": health_data.get('deps_score', 90), "status": "good"},
                "security": {"score": health_data.get('security_score', 80), "status": "good"},
                "performance": {"score": health_data.get('perf_score', 65), "status": "warning"},
                "code_quality": {"score": health_data.get('quality_score', 85), "status": "good"},
                "git": {"score": health_data.get('git_score', 95), "status": "excellent"},
                "documentation": {"score": health_data.get('docs_score', 60), "status": "warning"}
            },
            "suggestions": health_data.get('suggestions', [
                "Consider increasing test coverage",
                "Update outdated dependencies",
                "Add more documentation"
            ]),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health data: {str(e)}")

@router.get("/api/activity")
async def get_activity_data():
    """활동 히트맵 데이터 조회"""
    try:
        # ActivityHeatmap 위젯 사용
        activity_widget = ActivityHeatmap()
        
        # 지난 365일 활동 데이터 생성 (실제로는 git 로그나 세션 활동 데이터 사용)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=364)
        
        days = []
        current_date = start_date
        while current_date <= end_date:
            # 실제 활동 데이터로 교체 필요
            activity_count = random.randint(0, 15) if random.random() > 0.3 else 0
            days.append({
                "date": current_date.isoformat(),
                "activity": activity_count
            })
            current_date += timedelta(days=1)
        
        active_days = sum(1 for day in days if day['activity'] > 0)
        
        return {
            "days": days,
            "total_days": len(days),
            "active_days": active_days,
            "max_activity": max(day['activity'] for day in days),
            "avg_activity": sum(day['activity'] for day in days) / len(days)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity data: {str(e)}")

@router.get("/api/stats")
async def get_dashboard_stats():
    """대시보드 통계 요약"""
    try:
        sessions = await get_sessions()
        health = await get_project_health()
        activity = await get_activity_data()
        
        return {
            "active_sessions": sessions["active"],
            "total_projects": 1,  # 현재 프로젝트 수
            "health_score": health["overall_score"],
            "activity_streak": activity["active_days"],
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
```

## ✅ Phase 1 완료 기준

### 기능적 요구사항
- [ ] 웹 대시보드 기본 페이지 렌더링
- [ ] 세션 목록 표시 (list/grid/tree 뷰)
- [ ] 프로젝트 건강도 위젯 표시
- [ ] 활동 히트맵 표시
- [ ] 다크모드 토글 기능
- [ ] 반응형 디자인 (모바일/태블릿/데스크톱)

### 기술적 요구사항
- [ ] FastAPI 라우터 정상 동작
- [ ] HTML 템플릿 렌더링
- [ ] JavaScript 컴포넌트 시스템
- [ ] Tailwind CSS 스타일링
- [ ] API 엔드포인트 구현

### 테스트 요구사항
- [ ] 브라우저에서 대시보드 접근 가능
- [ ] 모든 위젯 정상 렌더링
- [ ] API 응답 정상 확인
- [ ] 다크모드 전환 동작
- [ ] 다양한 화면 크기에서 정상 표시

## 🔧 개발 환경 설정

### 실행 명령어
```bash
# 웹 대시보드 개발 서버 시작
cd web-dashboard
npm run dev

# FastAPI 서버 시작 (다른 터미널)
cd api
uvicorn main:app --reload --port 8000

# 통합 테스트
curl http://localhost:8000/web/
curl http://localhost:8000/web/api/sessions
```

### 디버깅 도구
- 브라우저 개발자 도구
- FastAPI 자동 문서: `http://localhost:8000/docs`
- 네트워크 탭에서 API 호출 확인
- 콘솔에서 JavaScript 오류 확인

---

**다음 단계**: Phase 1 완료 후 `02-web-dashboard-realtime.md` 진행