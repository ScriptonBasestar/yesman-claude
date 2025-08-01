<script lang="ts">
  import { sessions, isLoading } from '$lib/stores/sessions';
  import { onMount } from 'svelte';
  import { health, healthState, isHealthy, isUnhealthy } from '$lib/stores/health';

  // Helper function to format last check time
  function formatLastCheck(lastCheck: Date | null): string {
    if (!lastCheck) return 'Never';
    
    const now = new Date();
    const diffMs = now.getTime() - lastCheck.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    
    if (diffSecs < 60) {
      return `${diffSecs}s ago`;
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else {
      const diffHours = Math.floor(diffMins / 60);
      return `${diffHours}h ago`;
    }
  }

  // 통계 데이터 계산
  $: totalSessions = $sessions.length;
  $: activeSessions = $sessions.filter(s => s.status === 'running').length;
  $: inactiveSessions = $sessions.filter(s => s.status === 'stopped').length;
  $: unknownSessions = $sessions.filter(s => s.status === 'unknown').length;

  $: runningControllers = $sessions.filter(s => s.controller_status === 'running').length;
  $: stoppedControllers = $sessions.filter(s => s.controller_status === 'not running').length;
  $: errorControllers = $sessions.filter(s => s.controller_error !== null && s.controller_error !== undefined).length;
  $: unknownControllers = $sessions.filter(s => s.controller_status === 'unknown').length;

  $: totalWindows = $sessions.reduce((sum, s) => sum + (s.windows?.length || 0), 0);
  $: totalPanes = $sessions.reduce((sum, s) => sum + (s.total_panes || 0), 0);

  // 시스템 상태 계산
  $: systemHealth = calculateSystemHealth();
  $: uptime = calculateUptime();

  function calculateSystemHealth(): { status: string; percentage: number; color: string } {
    if (totalSessions === 0) {
      return { status: 'No Data', percentage: 0, color: 'text-base-content/50' };
    }

    const healthScore = (activeSessions + runningControllers * 0.5) / (totalSessions + totalSessions * 0.5);
    const percentage = Math.round(healthScore * 100);

    if (percentage >= 90) return { status: 'Excellent', percentage, color: 'text-success' };
    if (percentage >= 70) return { status: 'Good', percentage, color: 'text-info' };
    if (percentage >= 50) return { status: 'Fair', percentage, color: 'text-warning' };
    return { status: 'Poor', percentage, color: 'text-error' };
  }

  function calculateUptime(): string {
    // 실제로는 시스템 시작 시간부터 계산해야 하지만, 임시로 고정값 사용
    const hours = Math.floor(Math.random() * 24) + 1;
    const minutes = Math.floor(Math.random() * 60);
    return `${hours}h ${minutes}m`;
  }

  // 성능 메트릭 (실제로는 백엔드에서 받아와야 함)
  let performanceMetrics = {
    memoryUsage: 0,
    cpuUsage: 0,
    responseTime: 0
  };

  onMount(() => {
    // 실제 메트릭 수집 (임시로 랜덤값 사용)
    const interval = setInterval(() => {
      performanceMetrics = {
        memoryUsage: Math.floor(Math.random() * 30) + 70, // 70-100%
        cpuUsage: Math.floor(Math.random() * 50) + 10,   // 10-60%
        responseTime: Math.floor(Math.random() * 100) + 50 // 50-150ms
      };
    }, 5000);

    return () => clearInterval(interval);
  });
</script>

<div class="dashboard-stats">
  <!-- 메인 통계 카드들 -->
  <div class="stats-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-6">
    <!-- API 서버 상태 -->
    <div class="stat-card bg-gradient-to-br from-base-300 to-base-200 border border-base-content/20 rounded-xl p-6">
      <div class="stat-header flex items-center justify-between mb-4">
        <div class="stat-icon {$isHealthy ? 'text-success' : $isUnhealthy ? 'text-error' : 'text-warning'}">
          <span class="text-3xl">{$isHealthy ? '✅' : $isUnhealthy ? '❌' : '⚠️'}</span>
        </div>
        <div class="stat-trend text-xs {$isHealthy ? 'text-success' : $isUnhealthy ? 'text-error' : 'text-warning'}">
          {$isHealthy ? 'Healthy' : $isUnhealthy ? 'Unhealthy' : 'Degraded'}
        </div>
      </div>

      <div class="stat-content">
        <div class="stat-title text-lg font-bold text-base-content">
          API Server
        </div>
        <div class="stat-subtitle text-sm text-base-content/70">
          Backend Service
        </div>

        <div class="stat-breakdown mt-3 space-y-2 text-xs">
          <div class="flex justify-between">
            <span class="text-base-content/60">Version:</span>
            <span class="font-semibold">v1.0.0</span>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">Last Check:</span>
            <span class="font-semibold">{$healthState.lastCheck ? formatLastCheck($healthState.lastCheck) : 'Never'}</span>
          </div>
          {#if $healthState.consecutiveFailures > 0}
            <div class="flex justify-between">
              <span class="text-base-content/60">Failures:</span>
              <span class="font-semibold text-warning">{$healthState.consecutiveFailures}</span>
            </div>
          {/if}
        </div>
      </div>
    </div>
    
    <!-- 세션 통계 -->
    <div class="stat-card bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20 rounded-xl p-6">
      <div class="stat-header flex items-center justify-between mb-4">
        <div class="stat-icon text-primary">
          <span class="text-3xl">🖥️</span>
        </div>
        <div class="stat-trend text-xs text-primary">
          {activeSessions}/{totalSessions} active
        </div>
      </div>

      <div class="stat-content">
        <div class="stat-title text-lg font-bold text-base-content">
          {totalSessions}
        </div>
        <div class="stat-subtitle text-sm text-base-content/70">
          Tmux Sessions
        </div>

        <div class="stat-breakdown mt-3 grid grid-cols-3 gap-2 text-xs">
          <div class="text-center">
            <div class="font-semibold text-success">{activeSessions}</div>
            <div class="text-base-content/60">Active</div>
          </div>
          <div class="text-center">
            <div class="font-semibold text-error">{inactiveSessions}</div>
            <div class="text-base-content/60">Inactive</div>
          </div>
          <div class="text-center">
            <div class="font-semibold text-warning">{unknownSessions}</div>
            <div class="text-base-content/60">Unknown</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 컨트롤러 통계 -->
    <div class="stat-card bg-gradient-to-br from-secondary/10 to-secondary/5 border border-secondary/20 rounded-xl p-6">
      <div class="stat-header flex items-center justify-between mb-4">
        <div class="stat-icon text-secondary">
          <span class="text-3xl">🤖</span>
        </div>
        <div class="stat-trend text-xs text-secondary">
          {runningControllers} running
        </div>
      </div>

      <div class="stat-content">
        <div class="stat-title text-lg font-bold text-base-content">
          {runningControllers + stoppedControllers + errorControllers + unknownControllers}
        </div>
        <div class="stat-subtitle text-sm text-base-content/70">
          Claude Controllers
        </div>

        <div class="stat-breakdown mt-3 grid grid-cols-2 gap-2 text-xs">
          <div class="text-center">
            <div class="font-semibold text-success">{runningControllers}</div>
            <div class="text-base-content/60">Running</div>
          </div>
          <div class="text-center">
            <div class="font-semibold text-error">{stoppedControllers + errorControllers}</div>
            <div class="text-base-content/60">Stopped</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 시스템 건강도 -->
    <div class="stat-card bg-gradient-to-br from-accent/10 to-accent/5 border border-accent/20 rounded-xl p-6">
      <div class="stat-header flex items-center justify-between mb-4">
        <div class="stat-icon text-accent">
          <span class="text-3xl">💊</span>
        </div>
        <div class="stat-trend text-xs {systemHealth.color}">
          {systemHealth.percentage}%
        </div>
      </div>

      <div class="stat-content">
        <div class="stat-title text-lg font-bold {systemHealth.color}">
          {systemHealth.status}
        </div>
        <div class="stat-subtitle text-sm text-base-content/70">
          System Health
        </div>

        <div class="stat-progress mt-3">
          <div class="w-full bg-base-200 rounded-full h-2">
            <div
              class="bg-gradient-to-r from-accent to-accent/80 h-2 rounded-full transition-all duration-300"
              style="width: {systemHealth.percentage}%"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 리소스 사용량 -->
    <div class="stat-card bg-gradient-to-br from-info/10 to-info/5 border border-info/20 rounded-xl p-6">
      <div class="stat-header flex items-center justify-between mb-4">
        <div class="stat-icon text-info">
          <span class="text-3xl">📊</span>
        </div>
        <div class="stat-trend text-xs text-info">
          {uptime}
        </div>
      </div>

      <div class="stat-content">
        <div class="stat-title text-lg font-bold text-base-content">
          {totalWindows}W/{totalPanes}P
        </div>
        <div class="stat-subtitle text-sm text-base-content/70">
          Windows/Panes
        </div>

        <div class="stat-breakdown mt-3 space-y-2 text-xs">
          <div class="flex justify-between">
            <span class="text-base-content/60">Memory:</span>
            <span class="font-semibold">{performanceMetrics.memoryUsage}%</span>
          </div>
          <div class="flex justify-between">
            <span class="text-base-content/60">CPU:</span>
            <span class="font-semibold">{performanceMetrics.cpuUsage}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 상세 메트릭 바 -->
  <div class="detailed-metrics bg-base-100 border border-base-content/10 rounded-xl p-6">
    <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
      📈 Performance Metrics
    </h3>

    <div class="metrics-grid grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 메모리 사용량 -->
      <div class="metric-item">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-medium">Memory Usage</span>
          <span class="text-sm font-bold">{performanceMetrics.memoryUsage}%</span>
        </div>
        <div class="w-full bg-base-200 rounded-full h-2">
          <div
            class="bg-gradient-to-r from-warning to-error h-2 rounded-full transition-all duration-500"
            style="width: {performanceMetrics.memoryUsage}%"
          ></div>
        </div>
        <div class="text-xs text-base-content/60 mt-1">
          {Math.round(performanceMetrics.memoryUsage * 2.56)}MB / 256MB
        </div>
      </div>

      <!-- CPU 사용량 -->
      <div class="metric-item">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-medium">CPU Usage</span>
          <span class="text-sm font-bold">{performanceMetrics.cpuUsage}%</span>
        </div>
        <div class="w-full bg-base-200 rounded-full h-2">
          <div
            class="bg-gradient-to-r from-success to-info h-2 rounded-full transition-all duration-500"
            style="width: {performanceMetrics.cpuUsage}%"
          ></div>
        </div>
        <div class="text-xs text-base-content/60 mt-1">
          {runningControllers} processes active
        </div>
      </div>

      <!-- 응답 시간 -->
      <div class="metric-item">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-medium">Response Time</span>
          <span class="text-sm font-bold">{performanceMetrics.responseTime}ms</span>
        </div>
        <div class="w-full bg-base-200 rounded-full h-2">
          <div
            class="bg-gradient-to-r from-primary to-secondary h-2 rounded-full transition-all duration-500"
            style="width: {Math.min(performanceMetrics.responseTime / 2, 100)}%"
          ></div>
        </div>
        <div class="text-xs text-base-content/60 mt-1">
          Last update: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  </div>

  <!-- 로딩 오버레이 -->
  {#if $isLoading}
    <div class="loading-overlay absolute inset-0 bg-base-100/80 flex items-center justify-center rounded-xl">
      <div class="flex items-center gap-3">
        <span class="loading loading-spinner loading-lg"></span>
        <span class="text-lg font-medium">Updating statistics...</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .dashboard-stats {
    @apply relative;
  }

  .stat-card {
    @apply relative transition-all duration-200 hover:shadow-lg;
  }

  .stat-card:hover {
    @apply transform scale-[1.02];
  }

  .stat-icon {
    @apply p-2 rounded-lg bg-base-100/50;
  }

  .stat-progress {
    @apply relative;
  }

  .metric-item {
    @apply bg-base-200/50 p-4 rounded-lg;
  }

  .loading-overlay {
    @apply backdrop-blur-sm;
  }

  /* 반응형 조정 */
  @media (max-width: 768px) {
    .stats-grid {
      @apply grid-cols-1;
    }

    .metrics-grid {
      @apply grid-cols-1;
    }

    .stat-breakdown {
      @apply grid-cols-2;
    }
  }

  /* 애니메이션 */
  .stat-card {
    animation: fadeInUp 0.6s ease-out forwards;
  }

  .stat-card:nth-child(2) {
    animation-delay: 0.1s;
  }

  .stat-card:nth-child(3) {
    animation-delay: 0.2s;
  }

  .stat-card:nth-child(4) {
    animation-delay: 0.3s;
  }

  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
