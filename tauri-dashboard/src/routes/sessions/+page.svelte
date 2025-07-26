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
    viewSessionLogs,
    createTmuxSession,
    getAvailableProjects
  } from '$lib/stores/sessions';
  import { showNotification } from '$lib/stores/notifications';
  import { api } from '$lib/utils/api';

  // 세션 생성 모달 상태
  let showCreateModal = false;
  let availableProjects: string[] = [];
  let selectedProject = '';
  let isCreatingSession = false;

  onMount(async () => {
    refreshSessions();
    // 사용 가능한 프로젝트 목록 로드
    try {
      availableProjects = await getAvailableProjects();
    } catch (error) {
      console.error('Failed to load available projects:', error);
    }
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
    const { session } = event.detail;
    console.log('Starting session:', session);
    
    try {
      const result = await api.sessions.start(session);
      console.log('Success result:', result);
      showNotification('success', 'Session Started', `Session "${session}" has been started successfully.`);
      // 세션 목록 새로고침 - 세션이 완전히 시작될 때까지 약간의 지연 필요
      setTimeout(() => refreshSessions(), 1500);
    } catch (error) {
      console.error('Failed to start session:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      showNotification('error', 'Start Failed', `Failed to start session: ${errorMessage}`);
    }
  }

  async function handleStopSession(event: CustomEvent) {
    const { session } = event.detail;
    try {
      await api.sessions.stop(session);
      showNotification('success', 'Session Stopped', `Session "${session}" has been stopped successfully.`);
      // 세션 목록 새로고침
      setTimeout(() => refreshSessions(), 1000);
    } catch (error) {
      console.error('Failed to stop session:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      showNotification('error', 'Stop Failed', `Failed to stop session: ${errorMessage}`);
    }
  }

  function handleCreateSession() {
    if (availableProjects.length === 0) {
      showNotification('warning', 'No Projects', 'No projects found in configuration. Please check your projects.yaml file.');
      return;
    }
    selectedProject = availableProjects[0]; // 첫 번째 프로젝트를 기본 선택
    showCreateModal = true;
  }

  async function createSession() {
    if (!selectedProject) {
      showNotification('warning', 'No Project Selected', 'Please select a project to create a session.');
      return;
    }

    isCreatingSession = true;
    try {
      await createTmuxSession(selectedProject);
      showCreateModal = false;
      selectedProject = '';
    } catch (error) {
      console.error('Failed to create session:', error);
    } finally {
      isCreatingSession = false;
    }
  }

  function cancelCreateSession() {
    showCreateModal = false;
    selectedProject = '';
    isCreatingSession = false;
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
            on:startSession={handleStartSession}
            on:stopSession={handleStopSession}
          />
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- 세션 생성 모달 -->
{#if showCreateModal}
  <div class="modal modal-open">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">Create New Session</h3>

      <div class="form-control mb-4">
        <label for="project-select" class="label">
          <span class="label-text">Select Project</span>
        </label>
        <select
          id="project-select"
          class="select select-bordered w-full"
          bind:value={selectedProject}
          disabled={isCreatingSession}
        >
          {#each availableProjects as project}
            <option value={project}>{project}</option>
          {/each}
        </select>
        <div class="label">
          <span class="label-text-alt">Choose from projects.yaml configuration</span>
        </div>
      </div>

      <div class="modal-action">
        <button
          class="btn btn-primary"
          class:loading={isCreatingSession}
          disabled={isCreatingSession || !selectedProject}
          on:click={createSession}
        >
          {isCreatingSession ? 'Creating...' : 'Create Session'}
        </button>
        <button
          class="btn btn-ghost"
          disabled={isCreatingSession}
          on:click={cancelCreateSession}
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
{/if}

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
