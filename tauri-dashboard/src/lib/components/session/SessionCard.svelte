<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { Session } from '$lib/types/session';
  
  export let session: Session;
  
  const dispatch = createEventDispatcher();
  
  // 상태별 스타일 정의
  const statusStyles = {
    active: {
      badge: 'badge-success',
      icon: '🟢',
      bg: 'bg-success/10'
    },
    inactive: {
      badge: 'badge-error',
      icon: '🔴',
      bg: 'bg-error/10'
    },
    unknown: {
      badge: 'badge-warning',
      icon: '🟡',
      bg: 'bg-warning/10'
    }
  };
  
  const controllerStyles = {
    running: {
      badge: 'badge-success',
      icon: '🤖',
      text: 'Running'
    },
    stopped: {
      badge: 'badge-error',
      icon: '⏹️',
      text: 'Stopped'
    },
    error: {
      badge: 'badge-error',
      icon: '❌',
      text: 'Error'
    },
    unknown: {
      badge: 'badge-warning',
      icon: '❓',
      text: 'Unknown'
    }
  };
  
  // 세션 상태 계산
  $: sessionStyle = statusStyles[session.status as keyof typeof statusStyles] || statusStyles.unknown;
  $: controllerStyle = controllerStyles[session.controller_status as keyof typeof controllerStyles] || controllerStyles.unknown;
  
  // 세션이 실행 중인지 확인
  $: isSessionRunning = session.status === 'active';
  $: canStartController = isSessionRunning && session.controller_status !== 'running';
  
  // 시간 포맷팅
  function formatUptime(uptime: string | null): string {
    if (!uptime) return 'N/A';
    return uptime;
  }
  
  function formatLastActivity(timestamp: number | null): string {
    if (!timestamp) return 'No activity';
    
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  }
  
  // 이벤트 핸들러
  function handleStartController() {
    dispatch('startController', { session: session.session_name });
  }
  
  function handleStopController() {
    dispatch('stopController', { session: session.session_name });
  }
  
  function handleRestartController() {
    dispatch('restartController', { session: session.session_name });
  }
  
  function handleViewLogs() {
    dispatch('viewLogs', { session: session.session_name });
  }
  
  function handleAttachSession() {
    dispatch('attachSession', { session: session.session_name });
  }
  
  function handleViewDetails() {
    dispatch('viewDetails', { session: session.session_name });
  }
  
  function handleToggleStatus() {
    if (session.controller_status === 'running') {
      handleStopController();
    } else {
      handleStartController();
    }
  }
</script>

<div class="session-card card bg-base-100 shadow-lg border border-base-content/10 hover:shadow-xl transition-shadow">
  <div class="card-body p-6">
    <!-- 카드 헤더 -->
    <div class="card-header flex items-start justify-between mb-4">
      <div class="session-info flex-1">
        <div class="flex items-center gap-3 mb-2">
          <h3 class="card-title text-lg font-semibold">{session.session_name}</h3>
          <div class="badge {sessionStyle.badge} badge-sm">
            {sessionStyle.icon} {session.status}
          </div>
        </div>
        
        {#if session.project_name && session.project_name !== session.session_name}
          <p class="text-sm text-base-content/70">
            Project: <span class="font-medium">{session.project_name}</span>
          </p>
        {/if}
        
        {#if session.description}
          <p class="text-sm text-base-content/60 mt-1">{session.description}</p>
        {/if}
      </div>
      
      <div class="session-actions flex gap-2">
        <button 
          class="btn btn-ghost btn-sm"
          on:click={handleViewDetails}
          title="View details"
        >
          📊
        </button>
        
        <div class="dropdown dropdown-end">
          <button class="btn btn-ghost btn-sm">⋮</button>
          <ul class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
            <li><button on:click={handleAttachSession}>🔗 Attach to Session</button></li>
            <li><button on:click={handleViewLogs}>📋 View Logs</button></li>
            <li><hr></li>
            <li><button on:click={handleRestartController}>🔄 Restart Controller</button></li>
          </ul>
        </div>
      </div>
    </div>
    
    <!-- 세션 통계 -->
    <div class="session-stats grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Windows</div>
        <div class="stat-value text-lg font-bold">{session.windows?.length || 0}</div>
      </div>
      
      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Panes</div>
        <div class="stat-value text-lg font-bold">{session.total_panes || 0}</div>
      </div>
      
      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Uptime</div>
        <div class="stat-value text-sm font-mono">{formatUptime(session.uptime)}</div>
      </div>
      
      <div class="stat-item bg-base-200 p-3 rounded-lg">
        <div class="stat-title text-xs text-base-content/60">Last Activity</div>
        <div class="stat-value text-sm">{formatLastActivity(session.last_activity_timestamp)}</div>
      </div>
    </div>
    
    <!-- 컨트롤러 상태 -->
    <div class="controller-section">
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-sm font-semibold text-base-content/80">Claude Controller</h4>
        <div class="badge {controllerStyle.badge} badge-sm">
          {controllerStyle.icon} {controllerStyle.text}
        </div>
      </div>
      
      <div class="controller-info bg-base-200 p-3 rounded-lg mb-3">
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-base-content/60">Process ID:</span>
            <span class="font-mono ml-2">{session.controller_pid || 'N/A'}</span>
          </div>
          <div>
            <span class="text-base-content/60">Start Time:</span>
            <span class="ml-2">{session.controller_start_time || 'N/A'}</span>
          </div>
        </div>
        
        {#if session.controller_error}
          <div class="mt-2 p-2 bg-error/10 border border-error/20 rounded text-sm">
            <span class="text-error font-medium">Error:</span>
            <span class="ml-2">{session.controller_error}</span>
          </div>
        {/if}
        
        {#if session.last_response}
          <div class="mt-2 p-2 bg-success/10 border border-success/20 rounded text-sm">
            <span class="text-success font-medium">Last Response:</span>
            <span class="ml-2">{session.last_response}</span>
          </div>
        {/if}
      </div>
      
      <!-- 세션 상태 경고 -->
      {#if !isSessionRunning}
        <div class="session-warning bg-warning/10 border border-warning/20 p-3 rounded-lg mb-3">
          <div class="flex items-center gap-2">
            <span class="text-warning">⚠️</span>
            <div>
              <div class="text-sm font-medium text-warning">Session Not Running</div>
              <div class="text-xs text-base-content/60">
                Start the tmux session first before managing the controller
              </div>
            </div>
          </div>
        </div>
      {/if}
      
      <!-- 컨트롤러 액션 버튼 -->
      <div class="controller-actions flex gap-2">
        {#if session.controller_status === 'running'}
          <button 
            class="btn btn-error btn-sm flex-1"
            on:click={handleStopController}
          >
            ⏹️ Stop Controller
          </button>
        {:else}
          <button 
            class="btn btn-success btn-sm flex-1"
            class:btn-disabled={!canStartController}
            on:click={handleStartController}
            disabled={!canStartController}
            title={!isSessionRunning ? 'Session must be running to start controller' : 'Start Claude controller'}
          >
            ▶️ Start Controller
          </button>
        {/if}
        
        <button 
          class="btn btn-outline btn-sm"
          on:click={handleRestartController}
          disabled={!isSessionRunning || session.controller_status === 'unknown'}
          title={!isSessionRunning ? 'Session must be running to restart controller' : 'Restart Claude controller'}
        >
          🔄 Restart
        </button>
        
        <button 
          class="btn btn-ghost btn-sm"
          on:click={handleViewLogs}
        >
          📋 Logs
        </button>
      </div>
    </div>
    
    <!-- 윈도우 목록 (접기/펼치기) -->
    {#if session.windows && session.windows.length > 0}
      <div class="windows-section mt-4">
        <div class="collapse collapse-arrow bg-base-200">
          <input type="checkbox" />
          <div class="collapse-title text-sm font-medium">
            📋 Windows ({session.windows.length})
          </div>
          <div class="collapse-content">
            <div class="space-y-2">
              {#each session.windows as window}
                <div class="window-item bg-base-100 p-2 rounded border border-base-content/5">
                  <div class="flex items-center justify-between">
                    <span class="text-sm font-medium">{window.name}</span>
                    <div class="flex items-center gap-2 text-xs text-base-content/60">
                      <span>{window.panes?.length || 0} panes</span>
                      {#if window.active}
                        <span class="badge badge-primary badge-xs">active</span>
                      {/if}
                    </div>
                  </div>
                  {#if window.layout}
                    <div class="text-xs text-base-content/50 mt-1">Layout: {window.layout}</div>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .session-card {
    @apply transition-all duration-200;
  }
  
  .session-card:hover {
    @apply border-primary/20;
  }
  
  .stat-item {
    @apply text-center border border-base-content/5;
  }
  
  .stat-title {
    @apply block mb-1;
  }
  
  .stat-value {
    @apply block;
  }
  
  .controller-section {
    @apply border-t border-base-content/10 pt-4;
  }
  
  .window-item {
    @apply hover:bg-base-200 transition-colors;
  }
</style>