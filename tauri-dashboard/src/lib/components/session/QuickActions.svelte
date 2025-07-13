<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { sessions, isLoading } from '$lib/stores/sessions';
  import { showNotification } from '$lib/stores/notifications';
  
  const dispatch = createEventDispatcher();
  
  // 빠른 액션 정의
  const quickActions = [
    {
      id: 'refresh',
      icon: '🔄',
      label: 'Refresh All',
      description: 'Refresh session data',
      variant: 'btn-outline',
      hotkey: 'R'
    },
    {
      id: 'setup',
      icon: '⚡',
      label: 'Setup Sessions',
      description: 'Create all sessions from config',
      variant: 'btn-primary',
      hotkey: 'S'
    },
    {
      id: 'start_all',
      icon: '▶️',
      label: 'Start All Controllers',
      description: 'Start all Claude controllers',
      variant: 'btn-success',
      hotkey: 'Ctrl+S'
    },
    {
      id: 'stop_all',
      icon: '⏹️',
      label: 'Stop All Controllers',
      description: 'Stop all Claude controllers',
      variant: 'btn-error',
      hotkey: 'Ctrl+T'
    },
    {
      id: 'teardown',
      icon: '🛑',
      label: 'Teardown Sessions',
      description: 'Stop and remove all sessions',
      variant: 'btn-error btn-outline',
      hotkey: 'Ctrl+D',
      confirmRequired: true
    }
  ];
  
  // 세션 통계 계산
  $: totalSessions = $sessions.length;
  $: activeSessions = $sessions.filter(s => s.status === 'active').length;
  $: runningControllers = $sessions.filter(s => s.controller_status === 'running').length;
  $: stoppedControllers = $sessions.filter(s => s.controller_status === 'stopped').length;
  $: errorControllers = $sessions.filter(s => s.controller_status === 'error').length;
  
  // 액션 핸들러
  function handleAction(actionId: string) {
    const action = quickActions.find(a => a.id === actionId);
    
    if (action?.confirmRequired) {
      if (!confirm(`Are you sure you want to ${action.label.toLowerCase()}?`)) {
        return;
      }
    }
    
    dispatch('action', { action: actionId });
  }
  
  // 키보드 단축키 처리
  function handleKeydown(event: KeyboardEvent) {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return; // 입력 필드에서는 단축키 무시
    }
    
    const action = quickActions.find(a => {
      if (a.hotkey.includes('Ctrl+')) {
        return event.ctrlKey && event.key.toLowerCase() === a.hotkey.split('+')[1].toLowerCase();
      }
      return event.key.toLowerCase() === a.hotkey.toLowerCase();
    });
    
    if (action) {
      event.preventDefault();
      handleAction(action.id);
    }
  }
  
  // 액션 가용성 확인
  function isActionDisabled(actionId: string): boolean {
    switch (actionId) {
      case 'start_all':
        return stoppedControllers === 0;
      case 'stop_all':
        return runningControllers === 0;
      case 'teardown':
        return activeSessions === 0;
      default:
        return false;
    }
  }
  
  function getActionTooltip(action: any): string {
    let tooltip = `${action.description}`;
    if (action.hotkey) {
      tooltip += ` (${action.hotkey})`;
    }
    
    if (isActionDisabled(action.id)) {
      switch (action.id) {
        case 'start_all':
          tooltip += ' - No stopped controllers';
          break;
        case 'stop_all':
          tooltip += ' - No running controllers';
          break;
        case 'teardown':
          tooltip += ' - No active sessions';
          break;
      }
    }
    
    return tooltip;
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="quick-actions bg-base-100 border border-base-content/10 rounded-lg p-6">
  <!-- 섹션 헤더 ---->
  <div class="actions-header flex items-center justify-between mb-6">
    <div>
      <h3 class="text-lg font-semibold text-base-content flex items-center gap-2">
        ⚡ Quick Actions
      </h3>
      <p class="text-sm text-base-content/60 mt-1">
        Manage sessions and controllers with one click
      </p>
    </div>
    
    <!-- 세션 상태 요약 -->
    <div class="status-summary hidden lg:flex items-center gap-4 text-sm">
      <div class="stat-badge bg-primary/10 text-primary px-3 py-1 rounded-full">
        <span class="font-semibold">{activeSessions}</span>
        <span class="text-xs ml-1">Active</span>
      </div>
      <div class="stat-badge bg-success/10 text-success px-3 py-1 rounded-full">
        <span class="font-semibold">{runningControllers}</span>
        <span class="text-xs ml-1">Running</span>
      </div>
      {#if errorControllers > 0}
        <div class="stat-badge bg-error/10 text-error px-3 py-1 rounded-full">
          <span class="font-semibold">{errorControllers}</span>
          <span class="text-xs ml-1">Errors</span>
        </div>
      {/if}
    </div>
  </div>
  
  <!-- 액션 버튼들 -->
  <div class="actions-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
    {#each quickActions as action}
      <div class="action-card">
        <button
          class="btn {action.variant} w-full h-auto p-4 flex-col gap-2 relative"
          class:loading={$isLoading && (action.id === 'refresh' || action.id === 'setup')}
          disabled={$isLoading || isActionDisabled(action.id)}
          on:click={() => handleAction(action.id)}
          title={getActionTooltip(action)}
        >
          <!-- 액션 아이콘 -->
          <div class="action-icon text-2xl">
            {action.icon}
          </div>
          
          <!-- 액션 텍스트 -->
          <div class="action-text text-center">
            <div class="font-semibold text-sm">{action.label}</div>
            <div class="text-xs opacity-70 mt-1">{action.description}</div>
          </div>
          
          <!-- 단축키 표시 -->
          {#if action.hotkey}
            <div class="hotkey-badge absolute top-1 right-1 text-xs opacity-50 bg-base-content/10 px-1 rounded">
              {action.hotkey}
            </div>
          {/if}
          
          <!-- 확인 필요 표시 -->
          {#if action.confirmRequired}
            <div class="confirm-badge absolute top-1 left-1 text-xs">
              ⚠️
            </div>
          {/if}
        </button>
        
        <!-- 액션별 추가 정보 -->
        {#if action.id === 'start_all' && stoppedControllers > 0}
          <div class="action-info text-xs text-center mt-2 text-base-content/60">
            {stoppedControllers} controller{stoppedControllers > 1 ? 's' : ''} to start
          </div>
        {:else if action.id === 'stop_all' && runningControllers > 0}
          <div class="action-info text-xs text-center mt-2 text-base-content/60">
            {runningControllers} controller{runningControllers > 1 ? 's' : ''} to stop
          </div>
        {:else if action.id === 'teardown' && activeSessions > 0}
          <div class="action-info text-xs text-center mt-2 text-base-content/60">
            {activeSessions} session{activeSessions > 1 ? 's' : ''} to teardown
          </div>
        {/if}
      </div>
    {/each}
  </div>
  
  <!-- 배치 작업 섹션 -->
  <div class="batch-operations mt-6 pt-6 border-t border-base-content/10">
    <h4 class="text-sm font-semibold text-base-content/80 mb-3 flex items-center gap-2">
      📦 Batch Operations
    </h4>
    
    <div class="batch-grid grid grid-cols-1 md:grid-cols-3 gap-3">
      <!-- 선택된 세션들에 대한 배치 작업 -->
      <button 
        class="btn btn-sm btn-outline"
        disabled={$isLoading}
        on:click={() => handleAction('restart_failed')}
      >
        🔄 Restart Failed Controllers
      </button>
      
      <button 
        class="btn btn-sm btn-outline"
        disabled={$isLoading}
        on:click={() => handleAction('view_all_logs')}
      >
        📋 Open All Logs
      </button>
      
      <button 
        class="btn btn-sm btn-outline"
        disabled={$isLoading}
        on:click={() => handleAction('export_config')}
      >
        💾 Export Configuration
      </button>
    </div>
  </div>
  
  <!-- 단축키 도움말 -->
  <div class="keyboard-help mt-4 text-xs text-base-content/50">
    <details class="collapse collapse-arrow">
      <summary class="collapse-title text-xs font-medium">⌨️ Keyboard Shortcuts</summary>
      <div class="collapse-content">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
          {#each quickActions.filter(a => a.hotkey) as action}
            <div class="flex justify-between items-center p-2 bg-base-200 rounded">
              <span>{action.label}</span>
              <kbd class="kbd kbd-xs">{action.hotkey}</kbd>
            </div>
          {/each}
        </div>
      </div>
    </details>
  </div>
</div>

<style>
  .action-card {
    @apply relative;
  }
  
  .action-icon {
    @apply transition-transform duration-200;
  }
  
  .btn:hover .action-icon {
    @apply scale-110;
  }
  
  .hotkey-badge {
    @apply font-mono;
  }
  
  .stat-badge {
    @apply font-medium;
  }
  
  .batch-grid {
    @apply text-sm;
  }
  
  @media (max-width: 768px) {
    .actions-grid {
      @apply grid-cols-2;
    }
    
    .batch-grid {
      @apply grid-cols-1;
    }
    
    .status-summary {
      @apply hidden;
    }
  }
</style>