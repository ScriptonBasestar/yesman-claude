<script lang="ts">
  import { onMount } from 'svelte';
  import SessionCard from '$lib/components/session/SessionCard.svelte';
  import MetricsDashboard from '$lib/components/metrics/MetricsDashboard.svelte';
  import SessionFilters from '$lib/components/session/SessionFilters.svelte';
  import QuickActions from '$lib/components/session/QuickActions.svelte';
  import DashboardStats from '$lib/components/dashboard/DashboardStats.svelte';
  import {
    filteredSessions,
    isLoading,
    isBackgroundLoading,
    error,
    refreshSessions,
    updateControllerStatus
  } from '$lib/stores/sessions';
  import { notifySuccess, notifyError } from '$lib/stores/notifications';

  // 세션 상태 변경 핸들러
  function handleSessionStatusChanged(event: CustomEvent) {
    const { session } = event.detail;
    updateControllerStatus(session);
    notifySuccess('Status Updated', `Controller status updated for ${session}`);
  }

  // 세션 상세보기 핸들러
  function handleViewDetails(event: CustomEvent) {
    const { session } = event.detail;
    // 상세 페이지로 이동 (추후 구현)
    console.log('View details for:', session);
  }

  // 빠른 액션 핸들러
  async function handleQuickAction(event: CustomEvent) {
    const { action } = event.detail;

    switch (action) {
      case 'refresh':
        refreshSessions();
        notifySuccess('Refreshed', 'Session data refreshed');
        break;
      case 'setup':
        try {
          const { setupAllSessions } = await import('$lib/stores/sessions');
          await setupAllSessions();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Setup Failed', `Failed to setup sessions: ${errorMessage}`);
        }
        break;
      case 'teardown':
        try {
          const { teardownAllSessions } = await import('$lib/stores/sessions');
          await teardownAllSessions();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Teardown Failed', `Failed to teardown sessions: ${errorMessage}`);
        }
        break;
      case 'start_all':
        try {
          const { startAllControllers } = await import('$lib/stores/sessions');
          await startAllControllers();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Start Failed', `Failed to start controllers: ${errorMessage}`);
        }
        break;
      case 'stop_all':
        try {
          const { stopAllControllers } = await import('$lib/stores/sessions');
          await stopAllControllers();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Stop Failed', `Failed to stop controllers: ${errorMessage}`);
        }
        break;
      default:
        console.warn('Unknown action:', action);
    }
  }
</script>

<svelte:head>
  <title>Dashboard - Yesman</title>
</svelte:head>

<div class="dashboard-page p-6 space-y-6">
  <!-- 대시보드 헤더 및 통계 -->
  <div class="dashboard-header">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-3xl font-bold text-base-content">🚀 Yesman Claude Dashboard</h1>
        <p class="text-base-content/70 mt-1">Monitor and control your tmux sessions and Claude controllers</p>
      </div>

      <div class="flex gap-2">
        <button
          class="btn btn-primary btn-sm"
          class:loading={$isLoading || $isBackgroundLoading}
          on:click={() => refreshSessions(false)}
          disabled={$isLoading}
        >
          {#if $isBackgroundLoading}
            ⏳ Updating...
          {:else}
            🔄 Refresh
          {/if}
        </button>
      </div>
    </div>

    <!-- 대시보드 통계 -->
    <DashboardStats />
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

  <!-- 메트릭 대시보드 -->
  <div class="metrics-section">
    <h2 class="text-xl font-semibold mb-4">📊 Performance Metrics</h2>
    <MetricsDashboard />
  </div>

  <!-- 빠른 액션 -->
  <div class="quick-actions-section">
    <QuickActions on:action={handleQuickAction} />
  </div>

  <!-- 세션 관리 -->
  <div class="sessions-section">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">🖥️ Tmux Sessions</h2>
      <div class="text-sm text-base-content/70">
        {#if $filteredSessions.length > 0}
          Showing {$filteredSessions.length} sessions
        {:else}
          No sessions found
        {/if}
      </div>
    </div>

    <!-- 필터 -->
    <div class="mb-6">
      <SessionFilters />
    </div>

    <!-- 세션 목록 -->
    <div class="sessions-grid space-y-4">
      {#if $isLoading}
        <div class="loading-container flex justify-center items-center py-12">
          <span class="loading loading-spinner loading-lg"></span>
          <span class="ml-3">Loading sessions...</span>
        </div>
      {:else if $filteredSessions.length === 0}
        <div class="no-sessions text-center py-12">
          <div class="text-6xl mb-4">🔍</div>
          <h3 class="text-lg font-semibold mb-2">No sessions found</h3>
          <p class="text-base-content/70 mb-4">
            {#if $error}
              There was an error loading sessions. Please try refreshing.
            {:else}
              Run <code class="bg-base-200 px-2 py-1 rounded">./yesman.py setup</code> to create sessions.
            {/if}
          </p>
          <button
            class="btn btn-primary"
            on:click={() => refreshSessions()}
          >
            🔄 Refresh Sessions
          </button>
        </div>
      {:else}
        {#each $filteredSessions as session (session.session_name)}
          <SessionCard
            {session}
            on:statusChanged={handleSessionStatusChanged}
            on:viewDetails={handleViewDetails}
          />
        {/each}
      {/if}
    </div>
  </div>
</div>

<style>
  .dashboard-page {
    @apply max-w-7xl mx-auto;
  }

  .sessions-grid {
    @apply max-w-none;
  }

  .loading-container {
    @apply text-base-content/70;
  }

  .no-sessions {
    @apply text-base-content;
  }

  .no-sessions code {
    @apply text-sm;
  }
</style>
