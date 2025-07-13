<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { page } from '$app/stores';
  import { sessions, isLoading } from '$lib/stores/sessions';
  import { notifications } from '$lib/stores/notifications';

  const dispatch = createEventDispatcher();

  // 현재 시간 업데이트
  let currentTime = new Date();
  setInterval(() => {
    currentTime = new Date();
  }, 1000);

  // 페이지 타이틀 매핑
  const pageTitles: Record<string, string> = {
    '/': 'Dashboard Overview',
    '/sessions': 'Tmux Sessions',
    '/controllers': 'Claude Controllers',
    '/logs': 'Activity Logs',
    '/settings': 'Settings'
  };

  // 세션 통계 계산
  $: totalSessions = $sessions.length;
  $: activeSessions = $sessions.filter(s => s.status === 'active').length;
  $: runningControllers = $sessions.filter(s => s.controller_status === 'running').length;
  $: unreadNotifications = $notifications.filter(n => !n.read).length;

  // 현재 페이지 타이틀
  $: currentPageTitle = pageTitles[$page.url.pathname] || 'Yesman Dashboard';

  function handleNotificationClick() {
    dispatch('toggleNotifications');
  }

  function handleSettingsClick() {
    dispatch('openSettings');
  }

  function handleRefresh() {
    dispatch('refresh');
  }
</script>

<header class="header bg-base-100 border-b border-base-content/10 px-6 py-4">
  <div class="flex items-center justify-between">
    <!-- 왼쪽: 페이지 정보 -->
    <div class="header-left flex items-center gap-4">
      <div class="page-info">
        <h1 class="text-xl font-semibold text-base-content">{currentPageTitle}</h1>
        <p class="text-sm text-base-content/60">
          {currentTime.toLocaleString('ko-KR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </p>
      </div>
    </div>

    <!-- 가운데: 주요 메트릭 -->
    <div class="header-center flex items-center gap-6">
      <div class="metrics flex gap-4">
        <!-- 세션 통계 -->
        <div class="metric-item">
          <div class="stat">
            <div class="stat-figure text-primary">
              <span class="text-2xl">🖥️</span>
            </div>
            <div class="stat-title text-xs">Sessions</div>
            <div class="stat-value text-sm">{activeSessions}/{totalSessions}</div>
            <div class="stat-desc text-xs">Active/Total</div>
          </div>
        </div>

        <!-- 컨트롤러 통계 -->
        <div class="metric-item">
          <div class="stat">
            <div class="stat-figure text-secondary">
              <span class="text-2xl">🤖</span>
            </div>
            <div class="stat-title text-xs">Controllers</div>
            <div class="stat-value text-sm">{runningControllers}</div>
            <div class="stat-desc text-xs">Running</div>
          </div>
        </div>

        <!-- 로딩 상태 -->
        {#if $isLoading}
          <div class="metric-item">
            <div class="stat">
              <div class="stat-figure text-warning">
                <span class="loading loading-spinner loading-sm"></span>
              </div>
              <div class="stat-title text-xs">Status</div>
              <div class="stat-value text-sm">Loading</div>
              <div class="stat-desc text-xs">Updating...</div>
            </div>
          </div>
        {/if}
      </div>
    </div>

    <!-- 오른쪽: 액션 버튼들 -->
    <div class="header-right flex items-center gap-3">
      <!-- 새로고침 버튼 -->
      <button
        class="btn btn-ghost btn-sm"
        class:loading={$isLoading}
        on:click={handleRefresh}
        disabled={$isLoading}
        title="Refresh data"
      >
        <span class="text-lg">🔄</span>
      </button>

      <!-- 알림 버튼 -->
      <button
        class="btn btn-ghost btn-sm relative"
        on:click={handleNotificationClick}
        title="Notifications"
      >
        <span class="text-lg">🔔</span>
        {#if unreadNotifications > 0}
          <div class="badge badge-error badge-xs absolute -top-1 -right-1">
            {unreadNotifications > 99 ? '99+' : unreadNotifications}
          </div>
        {/if}
      </button>

      <!-- 설정 버튼 -->
      <button
        class="btn btn-ghost btn-sm"
        on:click={handleSettingsClick}
        title="Settings"
      >
        <span class="text-lg">⚙️</span>
      </button>

      <!-- 사용자 프로필 -->
      <div class="dropdown dropdown-end">
        <button class="btn btn-ghost btn-circle avatar">
          <div class="avatar placeholder">
            <div class="bg-neutral-focus text-neutral-content rounded-full w-8">
              <span class="text-xs">👤</span>
            </div>
          </div>
        </button>
        <ul class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
          <li><a href="/profile">👤 Profile</a></li>
          <li><a href="/settings">⚙️ Settings</a></li>
          <li><hr class="my-1"></li>
          <li><a href="/help">❓ Help</a></li>
          <li><a href="/about">ℹ️ About</a></li>
        </ul>
      </div>
    </div>
  </div>
</header>

<style>
  .header {
    @apply sticky top-0 z-40;
  }

  .metric-item {
    @apply bg-base-200 rounded-lg p-2;
  }

  .metrics {
    @apply hidden md:flex;
  }

  .stat {
    @apply text-center;
  }

  .stat-figure {
    @apply text-lg;
  }

  .stat-value {
    @apply font-bold;
  }

  .stat-title,
  .stat-desc {
    @apply text-base-content/60;
  }

  @media (max-width: 768px) {
    .header-center {
      @apply hidden;
    }
  }
</style>
