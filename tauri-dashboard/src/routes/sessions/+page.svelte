<script lang="ts">
  import { onMount } from 'svelte';
  import SessionCard from '$lib/components/session/SessionCard.svelte';
  import SessionFilters from '$lib/components/session/SessionFilters.svelte';
  import { 
    filteredSessions, 
    sessionStats, // 1. Import sessionStats
    isLoading, 
    error, 
    refreshSessions,
    startController,
    stopController,
    restartController,
    viewSessionLogs
    // 2. Remove setupTmuxSession
  } from '$lib/stores/sessions';
  import { showNotification } from '$lib/stores/notifications';

  onMount(() => {
    refreshSessions();
  });

  // 세션 카드 이벤트 핸들러
  async function handleStartController(event: CustomEvent) {
    const { session } = event.detail;
    try {
      await startController(session);
    } catch (error) {
      console.error('Failed to start controller:', error);
    }
  }

  async function handleStopController(event: CustomEvent) {
    const { session } = event.detail;
    try {
      await stopController(session);
    } catch (error) {
      console.error('Failed to stop controller:', error);
    }
  }

  async function handleRestartController(event: CustomEvent) {
    const { session } = event.detail;
    try {
      await restartController(session);
    } catch (error) {
      console.error('Failed to restart controller:', error);
    }
  }

  async function handleViewLogs(event: CustomEvent) {
    const { session } = event.detail;
    try {
      await viewSessionLogs(session);
    } catch (error) {
      console.error('Failed to view logs:', error);
    }
  }

  async function handleAttachSession(event: CustomEvent) {
    const { session } = event.detail;
    showNotification('info', 'Attach Session', `Opening terminal for ${session}...`);
    // 터미널에서 tmux attach 명령 실행
    // 실제 구현은 Tauri command로 처리
  }

  async function handleViewDetails(event: CustomEvent) {
    const { session } = event.detail;
    // 세션 상세 페이지로 이동
    window.location.href = `/sessions/${session}`;
  }

  function handleCreateSession() {
    showNotification('info', 'Create Session', 'Opening session creation dialog...');
    // 세션 생성 모달 또는 페이지로 이동
  }
</script>

<svelte:head>
  <title>Sessions - Yesman Dashboard</title>
</svelte:head>

<div class="sessions-page p-6 space-y-6">
  <!-- 페이지 헤더 -->
  <div class="page-header">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-3xl font-bold text-base-content flex items-center gap-3">
          🖥️ Tmux Sessions
        </h1>
        <p class="text-base-content/70 mt-2">
          Manage your tmux sessions and Claude controllers
        </p>
      </div>
      
      <div class="header-actions flex gap-3">
        <button 
          class="btn btn-outline btn-sm"
          class:loading={$isLoading}
          on:click={() => refreshSessions()}
          disabled={$isLoading}
        >
          🔄 Refresh
        </button>
        
        <button 
          class="btn btn-primary btn-sm"
          on:click={handleCreateSession}
        >
          ➕ New Session
        </button>
      </div>
    </div>
  </div>

  <!-- 에러 표시 -->
  {#if $error}
    <div class="alert alert-error">
      <div>
        <h3 class="font-bold">Error loading sessions</h3>
        <div class="text-xs">{$error}</div>
      </div>
    </div>
  {/if}

  <!-- 필터 섹션 -->
  <div class="filters-section">
    <SessionFilters />
  </div>

  <!-- 세션 목록 -->
  <div class="sessions-content">
    {#if $isLoading}
      <div class="loading-container flex justify-center items-center py-20">
        <div class="text-center">
          <span class="loading loading-spinner loading-lg"></span>
          <p class="mt-4 text-base-content/70">Loading sessions...</p>
        </div>
      </div>
    {:else if $filteredSessions.length === 0}
      <div class="no-sessions text-center py-20">
        <div class="text-8xl mb-6">🖥️</div>
        <h3 class="text-2xl font-semibold mb-4">No sessions found</h3>
        <p class="text-base-content/70 mb-6 max-w-md mx-auto">
          {#if $error}
            There was an error loading sessions. Please try refreshing.
          {:else}
            You don't have any tmux sessions yet. Create your first session to get started.
          {/if}
        </p>
        
        <div class="flex justify-center gap-4">
          <button 
            class="btn btn-primary"
            on:click={handleCreateSession}
          >
            ➕ Create First Session
          </button>
          
          <button 
            class="btn btn-outline"
            on:click={() => refreshSessions()}
          >
            🔄 Refresh
          </button>
        </div>
      </div>
    {:else}
      <!-- 세션 통계 -->
      <div class="sessions-stats mb-6">
        <div class="stats stats-horizontal shadow">
          <div class="stat">
            <div class="stat-title">Total Sessions</div>
            <div class="stat-value text-primary">{$sessionStats.total}</div>
          </div>
          
          <div class="stat">
            <div class="stat-title">Active</div>
            <div class="stat-value text-success">
              {$sessionStats.active}
            </div>
          </div>
          
          <div class="stat">
            <div class="stat-title">Running Controllers</div>
            <div class="stat-value text-info">
              {$sessionStats.runningControllers}
            </div>
          </div>
          
          <div class="stat">
            <div class="stat-title">Errors</div>
            <div class="stat-value text-error">
              {$sessionStats.errorControllers}
            </div>
          </div>
        </div>
      </div>

      <!-- 세션 그리드 -->
      <div class="sessions-grid space-y-6">
        {#each $filteredSessions as session (session.session_name)}
          <SessionCard 
            {session}
            on:startController={handleStartController}
            on:stopController={handleStopController}
            on:restartController={handleRestartController}
            on:viewLogs={handleViewLogs}
            on:attachSession={handleAttachSession}
            on:viewDetails={handleViewDetails}
          />
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .sessions-page {
    @apply max-w-7xl mx-auto;
  }
  
  .sessions-grid {
    @apply grid grid-cols-1 gap-6;
  }
  
  .loading-container {
    @apply min-h-[400px];
  }
  
  .no-sessions {
    @apply min-h-[500px];
  }
  
  .sessions-stats {
    @apply mb-6;
  }
  
  @media (min-width: 768px) {
    .sessions-grid {
      @apply grid-cols-1;
    }
  }
</style>