<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/utils/api';
  import { health, healthStatus } from '$lib/stores/health';

  export let title = '문제 해결';
  export let showAdvanced = false;

  let diagnostics: any[] = [];
  let isRunningDiagnostics = false;
  let selectedDiagnostic: string | null = null;
  let diagnosticResults: Record<string, any> = {};
  let logMessages: string[] = [];
  let showLogs = false;

  const commonIssues = [
    {
      id: 'connection_failed',
      title: '연결 실패',
      description: '서비스에 연결할 수 없습니다',
      solutions: [
        '네트워크 연결 상태 확인',
        '서비스 상태 확인',
        '방화벽 설정 검토',
        '포트 가용성 확인'
      ]
    },
    {
      id: 'performance_slow',
      title: '성능 저하',
      description: '시스템 응답이 느려졌습니다',
      solutions: [
        'CPU 및 메모리 사용량 확인',
        '디스크 공간 확인',
        '불필요한 프로세스 종료',
        '시스템 재시작 고려'
      ]
    },
    {
      id: 'health_check_failed',
      title: '상태 점검 실패',
      description: '헬스 체크가 실패했습니다',
      solutions: [
        '의존 서비스 상태 확인',
        '설정 파일 검증',
        '로그 파일 분석',
        '서비스 재시작'
      ]
    },
    {
      id: 'deployment_error',
      title: '배포 오류',
      description: '배포 과정에서 문제가 발생했습니다',
      solutions: [
        '배포 설정 검토',
        '의존성 확인',
        '롤백 실행',
        '배포 로그 분석'
      ]
    }
  ];

  const diagnosticTests = [
    {
      id: 'connectivity',
      name: '연결성 테스트',
      description: '네트워크 및 서비스 연결 상태 확인'
    },
    {
      id: 'health',
      name: '상태 점검',
      description: '전체 시스템 상태 검사'
    },
    {
      id: 'performance',
      name: '성능 분석',
      description: '시스템 성능 및 리소스 사용량 분석'
    },
    {
      id: 'logs',
      name: '로그 분석',
      description: '최근 오류 및 경고 로그 분석'
    }
  ];

  onMount(() => {
    loadRecentLogs();
  });

  async function runDiagnostic(testId: string) {
    isRunningDiagnostics = true;
    selectedDiagnostic = testId;

    try {
      let result: any = {};

      switch (testId) {
        case 'connectivity':
          result = await runConnectivityTest();
          break;
        case 'health':
          result = await runHealthCheck();
          break;
        case 'performance':
          result = await runPerformanceAnalysis();
          break;
        case 'logs':
          result = await analyzeLogs();
          break;
        default:
          result = { error: '알 수 없는 진단 테스트입니다' };
      }

      diagnosticResults[testId] = {
        ...result,
        timestamp: new Date(),
        duration: Math.random() * 2000 + 500 // Mock duration
      };

    } catch (error) {
      diagnosticResults[testId] = {
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date()
      };
    } finally {
      isRunningDiagnostics = false;
      selectedDiagnostic = null;
    }
  }

  async function runConnectivityTest() {
    const response = await api.getHealthStatus();
    
    if (response.success) {
      return {
        status: 'success',
        message: '모든 서비스에 정상적으로 연결되었습니다',
        details: {
          components: Object.keys(response.data?.components || {}),
          overall_status: response.data?.overall
        }
      };
    } else {
      return {
        status: 'error',
        message: '일부 서비스에 연결할 수 없습니다',
        error: response.error
      };
    }
  }

  async function runHealthCheck() {
    const response = await api.runHealthCheck();
    
    if (response.success) {
      return {
        status: 'success',
        message: '시스템 상태가 정상입니다',
        details: response.data
      };
    } else {
      return {
        status: 'warning',
        message: '일부 상태 점검에서 문제가 발견되었습니다',
        error: response.error
      };
    }
  }

  async function runPerformanceAnalysis() {
    const response = await api.getPerformanceMetrics();
    
    if (response.success) {
      const metrics = response.data;
      const issues: string[] = [];
      
      if (metrics?.cpu?.percent > 80) {
        issues.push('CPU 사용률이 높습니다');
      }
      if (metrics?.memory?.percent > 85) {
        issues.push('메모리 사용률이 높습니다');
      }
      if (metrics?.disk?.percent > 90) {
        issues.push('디스크 공간이 부족합니다');
      }

      return {
        status: issues.length > 0 ? 'warning' : 'success',
        message: issues.length > 0 ? '성능 문제가 발견되었습니다' : '시스템 성능이 정상입니다',
        details: metrics,
        issues
      };
    } else {
      return {
        status: 'error',
        message: '성능 메트릭을 가져올 수 없습니다',
        error: response.error
      };
    }
  }

  async function analyzeLogs() {
    const response = await api.getLogs(undefined, 100);
    
    if (response.success) {
      const logs = response.data || [];
      const errorLogs = logs.filter((log: any) => 
        log.level === 'ERROR' || log.message.toLowerCase().includes('error')
      );
      const warningLogs = logs.filter((log: any) => 
        log.level === 'WARNING' || log.message.toLowerCase().includes('warning')
      );

      return {
        status: errorLogs.length > 0 ? 'error' : warningLogs.length > 0 ? 'warning' : 'success',
        message: `최근 ${logs.length}개 로그 중 오류 ${errorLogs.length}개, 경고 ${warningLogs.length}개 발견`,
        details: {
          total: logs.length,
          errors: errorLogs.length,
          warnings: warningLogs.length,
          recent_errors: errorLogs.slice(0, 5),
          recent_warnings: warningLogs.slice(0, 5)
        }
      };
    } else {
      return {
        status: 'error',
        message: '로그를 분석할 수 없습니다',
        error: response.error
      };
    }
  }

  async function loadRecentLogs() {
    try {
      const response = await api.getLogs(undefined, 20);
      if (response.success) {
        logMessages = (response.data || []).map((log: any) => 
          `[${log.timestamp}] ${log.level}: ${log.message}`
        );
      }
    } catch (error) {
      console.error('Failed to load logs:', error);
    }
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'success': return 'text-success';
      case 'warning': return 'text-warning';
      case 'error': return 'text-error';
      default: return 'text-base-content';
    }
  }

  function getStatusIcon(status: string): string {
    switch (status) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return '❓';
    }
  }
</script>

<div class="card bg-base-100 shadow-lg">
  <div class="card-header">
    <h3 class="card-title">{title}</h3>
    <div class="card-actions">
      <label class="label cursor-pointer">
        <span class="label-text mr-2">고급 모드</span>
        <input type="checkbox" bind:checked={showAdvanced} class="checkbox checkbox-sm" />
      </label>
    </div>
  </div>

  <div class="card-body">
    <!-- 일반적인 문제 해결 가이드 -->
    <div class="mb-6">
      <h4 class="font-semibold mb-3">일반적인 문제 해결</h4>
      <div class="grid gap-4 md:grid-cols-2">
        {#each commonIssues as issue}
          <div class="collapse collapse-arrow bg-base-200">
            <input type="checkbox" class="peer" />
            <div class="collapse-title font-medium">
              {issue.title}
              <p class="text-sm text-base-content/70 mt-1">{issue.description}</p>
            </div>
            <div class="collapse-content">
              <ul class="list-disc list-inside space-y-1">
                {#each issue.solutions as solution}
                  <li class="text-sm">{solution}</li>
                {/each}
              </ul>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- 진단 테스트 -->
    <div class="mb-6">
      <h4 class="font-semibold mb-3">자동 진단</h4>
      <div class="grid gap-3 md:grid-cols-2">
        {#each diagnosticTests as test}
          <div class="card bg-base-200 p-4">
            <div class="flex justify-between items-start mb-2">
              <div>
                <h5 class="font-medium">{test.name}</h5>
                <p class="text-sm text-base-content/70">{test.description}</p>
              </div>
              <button
                class="btn btn-sm btn-primary"
                class:loading={isRunningDiagnostics && selectedDiagnostic === test.id}
                disabled={isRunningDiagnostics}
                on:click={() => runDiagnostic(test.id)}
              >
                {isRunningDiagnostics && selectedDiagnostic === test.id ? '실행 중...' : '실행'}
              </button>
            </div>

            {#if diagnosticResults[test.id]}
              {@const result = diagnosticResults[test.id]}
              <div class="mt-3 p-3 bg-base-100 rounded">
                <div class="flex items-center gap-2 mb-2">
                  <span>{getStatusIcon(result.status || 'error')}</span>
                  <span class="font-medium {getStatusColor(result.status || 'error')}">
                    {result.message || result.error}
                  </span>
                </div>
                
                {#if showAdvanced && result.details}
                  <details class="mt-2">
                    <summary class="cursor-pointer text-sm text-base-content/70">세부 정보</summary>
                    <pre class="text-xs bg-base-200 p-2 rounded mt-2 overflow-auto">{JSON.stringify(result.details, null, 2)}</pre>
                  </details>
                {/if}

                {#if result.issues && result.issues.length > 0}
                  <div class="mt-2">
                    <p class="text-sm font-medium">발견된 문제:</p>
                    <ul class="text-sm list-disc list-inside">
                      {#each result.issues as issue}
                        <li>{issue}</li>
                      {/each}
                    </ul>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <!-- 로그 뷰어 (고급 모드) -->
    {#if showAdvanced}
      <div class="mb-6">
        <div class="flex justify-between items-center mb-3">
          <h4 class="font-semibold">최근 로그</h4>
          <button
            class="btn btn-sm btn-outline"
            on:click={() => showLogs = !showLogs}
          >
            {showLogs ? '숨기기' : '보기'}
          </button>
        </div>

        {#if showLogs}
          <div class="bg-base-200 p-4 rounded">
            {#if logMessages.length > 0}
              <div class="max-h-64 overflow-y-auto">
                {#each logMessages as message}
                  <div class="text-sm font-mono mb-1 p-1 hover:bg-base-300 rounded">
                    {message}
                  </div>
                {/each}
              </div>
            {:else}
              <p class="text-sm text-base-content/70">로그를 불러올 수 없습니다.</p>
            {/if}
            
            <div class="flex gap-2 mt-3">
              <button class="btn btn-sm btn-outline" on:click={loadRecentLogs}>
                새로고침
              </button>
              <button class="btn btn-sm btn-outline" on:click={() => api.clearLogs()}>
                로그 지우기
              </button>
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- 시스템 상태 요약 -->
    <div class="bg-base-200 p-4 rounded">
      <h4 class="font-semibold mb-2">현재 시스템 상태</h4>
      <div class="flex items-center gap-2">
        <div class="badge badge-lg" class:badge-success={$healthStatus === '시스템 정상'}
             class:badge-warning={$healthStatus === '주의 필요'}
             class:badge-error={$healthStatus === '오류 발생'}
             class:badge-ghost={$healthStatus === '상태 확인 중'}>
          {$healthStatus}
        </div>
        <span class="text-sm text-base-content/70">
          마지막 업데이트: {new Date($health.lastUpdated).toLocaleTimeString()}
        </span>
      </div>
    </div>
  </div>
</div>