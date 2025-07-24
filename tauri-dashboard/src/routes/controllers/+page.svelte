<script lang="ts">
  import { onMount } from 'svelte';
  import SessionCard from '$lib/components/session/SessionCard.svelte';
  import SessionFilters from '$lib/components/session/SessionFilters.svelte';
  import {
    filteredSessions,
    sessionStats,
    isLoading,
    error,
    refreshSessions,
    startController,
    stopController,
    restartController,
    viewSessionLogs
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

  async function handleStartSession(event: CustomEvent) {
    console.log('handleStartSession called with event:', event);
    const { session } = event.detail;
    console.log('Starting session:', session);
    
    try {
      const url = `http://localhost:8000/api/sessions/${session}/start`;
      console.log('Calling API:', url);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(errorData.detail || 'Failed to start session');
      }
      
      const result = await response.json();
      console.log('Success result:', result);
      showNotification('success', 'Session Started', `Session ${session} started successfully`);
      
      // 세션 목록 새로고침
      setTimeout(() => refreshSessions(), 1000);
    } catch (error) {
      console.error('Failed to start session:', error);
      showNotification('error', 'Start Failed', `Failed to start session: ${error.message}`);
    }
  }

  async function handleStopSession(event: CustomEvent) {
    const { session } = event.detail;
    try {
      const response = await fetch(`http://localhost:8000/api/sessions/${session}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to stop session');
      }
      
      const result = await response.json();
      showNotification('success', 'Session Stopped', `Session ${session} stopped successfully`);
      
      // 세션 목록 새로고침
      setTimeout(() => refreshSessions(), 1000);
    } catch (error) {
      console.error('Failed to stop session:', error);
      showNotification('error', 'Stop Failed', `Failed to stop session: ${error.message}`);
    }
  }

  // 컨트롤러 상태별 세션 필터링
  $: sessionsWithControllers = $filteredSessions.filter(session =>
    session.controller_status && session.controller_status !== 'unknown'
  );

  $: runningControllers = sessionsWithControllers.filter(s => s.controller_status === 'running');
  $: stoppedControllers = sessionsWithControllers.filter(s => s.controller_status === 'not running');
  $: errorControllers = sessionsWithControllers.filter(s => s.controller_error !== null && s.controller_error !== undefined);

  // 일괄 컨트롤러 작업
  async function startAllControllers() {
    try {
      for (const session of stoppedControllers) {
        await startController(session.session_name);
      }
      showNotification('success', 'Controllers Started', `Started ${stoppedControllers.length} controllers`);
    } catch (error) {
      showNotification('error', 'Start Failed', 'Failed to start some controllers');
    }
  }

  async function stopAllControllers() {
    try {
      for (const session of runningControllers) {
        await stopController(session.session_name);
      }
      showNotification('success', 'Controllers Stopped', `Stopped ${runningControllers.length} controllers`);
    } catch (error) {
      showNotification('error', 'Stop Failed', 'Failed to stop some controllers');
    }
  }
</script>

<svelte:head>
  <title>Controllers - Yesman Dashboard</title>
</svelte:head>

<div class="controllers-page p-6 space-y-6">
  <!-- 페이지 헤더 -->
  <div class="page-header">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-3xl font-bold text-base-content flex items-center gap-3">
          🤖 Claude Controllers
        </h1>
        <p class="text-base-content/70 mt-2">
          Monitor and manage Claude Code controllers across all sessions
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
      </div>
    </div>
  </div>

  <!-- 에러 표시 -->
  {#if $error}
    <div class="alert alert-error">
      <div>
        <h3 class="font-bold">Error loading controllers</h3>
        <div class="text-xs">{$error}</div>
      </div>
    </div>
  {/if}

  <!-- 컨트롤러 통계 -->
  <div class="controllers-stats mb-6">
    <div class="stats stats-horizontal shadow">
      <div class="stat">
        <div class="stat-title">Total Controllers</div>
        <div class="stat-value text-primary">{sessionsWithControllers.length}</div>
        <div class="stat-desc">Across all sessions</div>
      </div>

      <div class="stat">
        <div class="stat-title">Running</div>
        <div class="stat-value text-success">{runningControllers.length}</div>
        <div class="stat-desc">Active controllers</div>
      </div>

      <div class="stat">
        <div class="stat-title">Stopped</div>
        <div class="stat-value text-warning">{stoppedControllers.length}</div>
        <div class="stat-desc">Inactive controllers</div>
      </div>

      <div class="stat">
        <div class="stat-title">Errors</div>
        <div class="stat-value text-error">{errorControllers.length}</div>
        <div class="stat-desc">Failed controllers</div>
      </div>
    </div>
  </div>

  <!-- 컨트롤러 관리 액션 -->
  <div class="controller-actions bg-base-100 border border-base-content/10 rounded-lg p-6 mb-6">
    <h3 class="text-lg font-semibold mb-4">🚀 Bulk Controller Actions</h3>
    <div class="flex gap-4">
      <button
        class="btn btn-success"
        disabled={stoppedControllers.length === 0 || $isLoading}
        on:click={startAllControllers}
      >
        ▶️ Start All Stopped ({stoppedControllers.length})
      </button>

      <button
        class="btn btn-error"
        disabled={runningControllers.length === 0 || $isLoading}
        on:click={stopAllControllers}
      >
        ⏹️ Stop All Running ({runningControllers.length})
      </button>

      <button
        class="btn btn-outline"
        disabled={errorControllers.length === 0 || $isLoading}
        on:click={() => showNotification('info', 'Feature Coming Soon', 'Restart failed controllers feature is coming soon')}
      >
        🔄 Restart Failed ({errorControllers.length})
      </button>
    </div>
  </div>

  <!-- 필터 섹션 -->
  <div class="filters-section">
    <SessionFilters />
  </div>

  <!-- 컨트롤러 목록 -->
  <div class="controllers-content">
    {#if $isLoading}
      <div class="loading-container flex justify-center items-center py-20">
        <div class="text-center">
          <span class="loading loading-spinner loading-lg"></span>
          <p class="mt-4 text-base-content/70">Loading controllers...</p>
        </div>
      </div>
    {:else if sessionsWithControllers.length === 0}
      <div class="no-controllers text-center py-20">
        <div class="text-8xl mb-6">🤖</div>
        <h3 class="text-2xl font-semibold mb-4">No controllers found</h3>
        <p class="text-base-content/70 mb-6 max-w-md mx-auto">
          {#if $error}
            There was an error loading controllers. Please try refreshing.
          {:else}
            No sessions with Claude controllers were found. Start some sessions first.
          {/if}
        </p>

        <div class="flex justify-center gap-4">
          <button
            class="btn btn-primary"
            on:click={() => window.location.href = '/sessions'}
          >
            📋 Go to Sessions
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
      <!-- 컨트롤러별 세션 그룹화 -->
      <div class="controllers-grid space-y-6">
        <!-- 실행 중인 컨트롤러 -->
        {#if runningControllers.length > 0}
          <div class="controller-group">
            <h3 class="text-xl font-semibold mb-4 flex items-center gap-2">
              <span class="badge badge-success">🟢</span>
              Running Controllers ({runningControllers.length})
            </h3>
            <div class="space-y-4">
              {#each runningControllers as session (session.session_name)}
                <SessionCard
                  {session}
                  on:startController={handleStartController}
                  on:stopController={handleStopController}
                  on:restartController={handleRestartController}
                  on:viewLogs={handleViewLogs}
                  on:attachSession={handleAttachSession}
                  on:viewDetails={handleViewDetails}
                  on:startSession={handleStartSession}
                  on:stopSession={handleStopSession}
                />
              {/each}
            </div>
          </div>
        {/if}

        <!-- 중지된 컨트롤러 -->
        {#if stoppedControllers.length > 0}
          <div class="controller-group">
            <h3 class="text-xl font-semibold mb-4 flex items-center gap-2">
              <span class="badge badge-warning">⏹️</span>
              Stopped Controllers ({stoppedControllers.length})
            </h3>
            <div class="space-y-4">
              {#each stoppedControllers as session (session.session_name)}
                <SessionCard
                  {session}
                  on:startController={handleStartController}
                  on:stopController={handleStopController}
                  on:restartController={handleRestartController}
                  on:viewLogs={handleViewLogs}
                  on:attachSession={handleAttachSession}
                  on:viewDetails={handleViewDetails}
                  on:startSession={handleStartSession}
                  on:stopSession={handleStopSession}
                />
              {/each}
            </div>
          </div>
        {/if}

        <!-- 오류가 있는 컨트롤러 -->
        {#if errorControllers.length > 0}
          <div class="controller-group">
            <h3 class="text-xl font-semibold mb-4 flex items-center gap-2">
              <span class="badge badge-error">❌</span>
              Failed Controllers ({errorControllers.length})
            </h3>
            <div class="space-y-4">
              {#each errorControllers as session (session.session_name)}
                <SessionCard
                  {session}
                  on:startController={handleStartController}
                  on:stopController={handleStopController}
                  on:restartController={handleRestartController}
                  on:viewLogs={handleViewLogs}
                  on:attachSession={handleAttachSession}
                  on:viewDetails={handleViewDetails}
                  on:startSession={handleStartSession}
                  on:stopSession={handleStopSession}
                />
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .controllers-page {
    @apply max-w-7xl mx-auto;
  }

  .controllers-grid {
    @apply max-w-none;
  }

  .loading-container {
    @apply min-h-[400px];
  }

  .no-controllers {
    @apply min-h-[500px];
  }

  .controllers-stats {
    @apply mb-6;
  }

  .controller-group {
    @apply border border-base-content/10 rounded-lg p-6 bg-base-200;
  }
</style>
