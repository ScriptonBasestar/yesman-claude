<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { sessions } from '$lib/stores/sessions';

  // 차트 데이터 타입
  interface ChartDataPoint {
    timestamp: number;
    value: number;
    label: string;
  }

  interface MetricHistory {
    sessions: ChartDataPoint[];
    controllers: ChartDataPoint[];
    memory: ChartDataPoint[];
    cpu: ChartDataPoint[];
  }

  // 메트릭 히스토리 데이터
  let metricHistory: MetricHistory = {
    sessions: [],
    controllers: [],
    memory: [],
    cpu: []
  };

  // 실시간 메트릭
  let currentMetrics = {
    activeSessions: 0,
    runningControllers: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    responseTime: 0,
    errorRate: 0
  };

  // 차트 설정
  const maxDataPoints = 20;
  const updateInterval = 5000; // 5초마다 업데이트
  let metricsInterval: ReturnType<typeof setInterval>;

  // 현재 메트릭 계산
  $: {
    const activeSessions = $sessions.filter(s => s.status === 'running').length;
    const runningControllers = $sessions.filter(s => s.controller_status === 'running').length;

    currentMetrics = {
      activeSessions,
      runningControllers,
      memoryUsage: Math.floor(Math.random() * 30) + 70, // 임시 데이터
      cpuUsage: Math.floor(Math.random() * 50) + 10,
      responseTime: Math.floor(Math.random() * 100) + 50,
      errorRate: Math.floor(Math.random() * 5)
    };
  }

  // 메트릭 히스토리 업데이트
  function updateMetricHistory() {
    const now = Date.now();
    const timeLabel = new Date().toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });

    // 새 데이터 포인트 추가
    const newPoints = {
      sessions: {
        timestamp: now,
        value: currentMetrics.activeSessions,
        label: timeLabel
      },
      controllers: {
        timestamp: now,
        value: currentMetrics.runningControllers,
        label: timeLabel
      },
      memory: {
        timestamp: now,
        value: currentMetrics.memoryUsage,
        label: timeLabel
      },
      cpu: {
        timestamp: now,
        value: currentMetrics.cpuUsage,
        label: timeLabel
      }
    };

    // 히스토리 업데이트 (최대 20개 포인트 유지)
    metricHistory = {
      sessions: [...metricHistory.sessions, newPoints.sessions].slice(-maxDataPoints),
      controllers: [...metricHistory.controllers, newPoints.controllers].slice(-maxDataPoints),
      memory: [...metricHistory.memory, newPoints.memory].slice(-maxDataPoints),
      cpu: [...metricHistory.cpu, newPoints.cpu].slice(-maxDataPoints)
    };
  }

  // 간단한 선형 차트 SVG 생성
  function generateChartPath(data: ChartDataPoint[], maxValue: number = 100): string {
    if (data.length < 2) return '';

    const width = 300;
    const height = 60;
    const padding = 10;

    const xStep = (width - padding * 2) / (data.length - 1);
    const yScale = (height - padding * 2) / maxValue;

    let path = '';

    data.forEach((point, index) => {
      const x = padding + index * xStep;
      const y = height - padding - (point.value * yScale);

      if (index === 0) {
        path += `M ${x} ${y}`;
      } else {
        path += ` L ${x} ${y}`;
      }
    });

    return path;
  }

  // 메트릭 상태 색상 결정
  function getMetricColor(value: number, type: string): string {
    switch (type) {
      case 'memory':
        if (value > 90) return 'text-error';
        if (value > 70) return 'text-warning';
        return 'text-success';
      case 'cpu':
        if (value > 80) return 'text-error';
        if (value > 50) return 'text-warning';
        return 'text-success';
      case 'responseTime':
        if (value > 100) return 'text-error';
        if (value > 50) return 'text-warning';
        return 'text-success';
      default:
        return 'text-info';
    }
  }

  onMount(() => {
    // 초기 데이터 로드
    updateMetricHistory();

    // 주기적 업데이트 시작
    metricsInterval = setInterval(updateMetricHistory, updateInterval);
  });

  onDestroy(() => {
    if (metricsInterval) {
      clearInterval(metricsInterval);
    }
  });
</script>

<div class="metrics-dashboard space-y-6">
  <!-- 실시간 메트릭 카드들 -->
  <div class="real-time-metrics grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
    <!-- 활성 세션 -->
    <div class="metric-card bg-primary/10 border border-primary/20 rounded-lg p-4">
      <div class="metric-header flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-primary">Active Sessions</span>
        <span class="text-lg">🖥️</span>
      </div>
      <div class="metric-value text-2xl font-bold text-primary">
        {currentMetrics.activeSessions}
      </div>
      <div class="metric-change text-xs text-primary/70 mt-1">
        Total: {$sessions.length}
      </div>
    </div>

    <!-- 실행 중인 컨트롤러 -->
    <div class="metric-card bg-secondary/10 border border-secondary/20 rounded-lg p-4">
      <div class="metric-header flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-secondary">Controllers</span>
        <span class="text-lg">🤖</span>
      </div>
      <div class="metric-value text-2xl font-bold text-secondary">
        {currentMetrics.runningControllers}
      </div>
      <div class="metric-change text-xs text-secondary/70 mt-1">
        Running
      </div>
    </div>

    <!-- 메모리 사용량 -->
    <div class="metric-card bg-warning/10 border border-warning/20 rounded-lg p-4">
      <div class="metric-header flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-warning">Memory</span>
        <span class="text-lg">💾</span>
      </div>
      <div class="metric-value text-2xl font-bold {getMetricColor(currentMetrics.memoryUsage, 'memory')}">
        {currentMetrics.memoryUsage}%
      </div>
      <div class="metric-change text-xs text-warning/70 mt-1">
        {Math.round(currentMetrics.memoryUsage * 2.56)}MB
      </div>
    </div>

    <!-- CPU 사용량 -->
    <div class="metric-card bg-info/10 border border-info/20 rounded-lg p-4">
      <div class="metric-header flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-info">CPU</span>
        <span class="text-lg">⚡</span>
      </div>
      <div class="metric-value text-2xl font-bold {getMetricColor(currentMetrics.cpuUsage, 'cpu')}">
        {currentMetrics.cpuUsage}%
      </div>
      <div class="metric-change text-xs text-info/70 mt-1">
        Usage
      </div>
    </div>

    <!-- 응답 시간 -->
    <div class="metric-card bg-success/10 border border-success/20 rounded-lg p-4">
      <div class="metric-header flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-success">Response</span>
        <span class="text-lg">⏱️</span>
      </div>
      <div class="metric-value text-2xl font-bold {getMetricColor(currentMetrics.responseTime, 'responseTime')}">
        {currentMetrics.responseTime}ms
      </div>
      <div class="metric-change text-xs text-success/70 mt-1">
        Avg
      </div>
    </div>

    <!-- 에러율 -->
    <div class="metric-card bg-error/10 border border-error/20 rounded-lg p-4">
      <div class="metric-header flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-error">Error Rate</span>
        <span class="text-lg">❌</span>
      </div>
      <div class="metric-value text-2xl font-bold text-error">
        {currentMetrics.errorRate}%
      </div>
      <div class="metric-change text-xs text-error/70 mt-1">
        Last 1h
      </div>
    </div>
  </div>

  <!-- 차트 섹션 -->
  <div class="charts-section grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- 세션 추세 차트 -->
    <div class="chart-card bg-base-100 border border-base-content/10 rounded-lg p-6">
      <div class="chart-header flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold">📈 Session Trends</h3>
        <div class="text-xs text-base-content/60">Last {maxDataPoints} updates</div>
      </div>

      <div class="chart-container relative">
        <svg viewBox="0 0 300 80" class="w-full h-20 border border-base-content/10 rounded bg-base-200/50">
          <!-- 배경 그리드 -->
          <defs>
            <pattern id="grid" width="30" height="20" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 20" fill="none" stroke="currentColor" stroke-width="0.5" opacity="0.3"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          <!-- 세션 라인 -->
          {#if metricHistory.sessions.length > 1}
            <path
              d={generateChartPath(metricHistory.sessions, Math.max(...metricHistory.sessions.map(d => d.value)) || 10)}
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-primary"
            />
          {/if}

          <!-- 컨트롤러 라인 -->
          {#if metricHistory.controllers.length > 1}
            <path
              d={generateChartPath(metricHistory.controllers, Math.max(...metricHistory.controllers.map(d => d.value)) || 10)}
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-dasharray="5,5"
              class="text-secondary"
            />
          {/if}
        </svg>

        <div class="chart-legend flex gap-4 mt-2 text-xs">
          <div class="flex items-center gap-1">
            <div class="w-3 h-0.5 bg-primary"></div>
            <span>Sessions</span>
          </div>
          <div class="flex items-center gap-1">
            <div class="w-3 h-0.5 bg-secondary border-dashed"></div>
            <span>Controllers</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 리소스 사용량 차트 -->
    <div class="chart-card bg-base-100 border border-base-content/10 rounded-lg p-6">
      <div class="chart-header flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold">🖥️ Resource Usage</h3>
        <div class="text-xs text-base-content/60">Real-time</div>
      </div>

      <div class="chart-container relative">
        <svg viewBox="0 0 300 80" class="w-full h-20 border border-base-content/10 rounded bg-base-200/50">
          <!-- 배경 그리드 -->
          <rect width="100%" height="100%" fill="url(#grid)" />

          <!-- 메모리 라인 -->
          {#if metricHistory.memory.length > 1}
            <path
              d={generateChartPath(metricHistory.memory, 100)}
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="text-warning"
            />
          {/if}

          <!-- CPU 라인 -->
          {#if metricHistory.cpu.length > 1}
            <path
              d={generateChartPath(metricHistory.cpu, 100)}
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-dasharray="3,3"
              class="text-info"
            />
          {/if}
        </svg>

        <div class="chart-legend flex gap-4 mt-2 text-xs">
          <div class="flex items-center gap-1">
            <div class="w-3 h-0.5 bg-warning"></div>
            <span>Memory ({currentMetrics.memoryUsage}%)</span>
          </div>
          <div class="flex items-center gap-1">
            <div class="w-3 h-0.5 bg-info border-dashed"></div>
            <span>CPU ({currentMetrics.cpuUsage}%)</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 성능 표시기 -->
  <div class="performance-indicators bg-base-100 border border-base-content/10 rounded-lg p-6">
    <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
      🎯 Performance Indicators
    </h3>

    <div class="indicators-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 시스템 안정성 -->
      <div class="indicator-item">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium">System Stability</span>
          <span class="text-xs text-success">Excellent</span>
        </div>
        <div class="w-full bg-base-200 rounded-full h-2">
          <div class="bg-success h-2 rounded-full" style="width: 95%"></div>
        </div>
        <div class="text-xs text-base-content/60 mt-1">95% uptime</div>
      </div>

      <!-- 처리량 -->
      <div class="indicator-item">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium">Throughput</span>
          <span class="text-xs text-info">Good</span>
        </div>
        <div class="w-full bg-base-200 rounded-full h-2">
          <div class="bg-info h-2 rounded-full" style="width: 78%"></div>
        </div>
        <div class="text-xs text-base-content/60 mt-1">{metricHistory.sessions.length * 12}/min</div>
      </div>

      <!-- 응답성 -->
      <div class="indicator-item">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium">Responsiveness</span>
          <span class="text-xs {getMetricColor(currentMetrics.responseTime, 'responseTime')}">
            {currentMetrics.responseTime < 50 ? 'Excellent' : currentMetrics.responseTime < 100 ? 'Good' : 'Fair'}
          </span>
        </div>
        <div class="w-full bg-base-200 rounded-full h-2">
          <div
            class="h-2 rounded-full {currentMetrics.responseTime < 50 ? 'bg-success' : currentMetrics.responseTime < 100 ? 'bg-warning' : 'bg-error'}"
            style="width: {100 - currentMetrics.responseTime}%"
          ></div>
        </div>
        <div class="text-xs text-base-content/60 mt-1">~{currentMetrics.responseTime}ms avg</div>
      </div>

      <!-- 효율성 -->
      <div class="indicator-item">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium">Efficiency</span>
          <span class="text-xs text-warning">Good</span>
        </div>
        <div class="w-full bg-base-200 rounded-full h-2">
          <div class="bg-warning h-2 rounded-full" style="width: 82%"></div>
        </div>
        <div class="text-xs text-base-content/60 mt-1">82% optimal</div>
      </div>
    </div>
  </div>
</div>

<style>
  .metric-card {
    @apply transition-all duration-200 hover:shadow-md;
  }

  .metric-value {
    @apply transition-colors duration-300;
  }

  .chart-container svg {
    @apply transition-all duration-300;
  }

  .chart-legend {
    @apply text-base-content/70;
  }

  .indicator-item {
    @apply bg-base-200/50 p-4 rounded-lg;
  }

  /* 반응형 조정 */
  @media (max-width: 768px) {
    .real-time-metrics {
      @apply grid-cols-2;
    }

    .charts-section {
      @apply grid-cols-1;
    }

    .indicators-grid {
      @apply grid-cols-1;
    }
  }
</style>
