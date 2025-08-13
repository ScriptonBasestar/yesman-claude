<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { api } from '$lib/utils/api';

  const dispatch = createEventDispatcher();

  export let title = '시작하기 가이드';
  export let autoStart = false;

  let currentStep = 0;
  let isCompleted = false;
  let isSkipped = false;
  let stepResults: Record<number, any> = {};
  let isProcessing = false;

  const steps = [
    {
      id: 'welcome',
      title: '환영합니다!',
      description: 'Yesman Agent 대시보드에 오신 것을 환영합니다.',
      type: 'info',
      content: `
        <div class="text-center">
          <h2 class="text-2xl font-bold mb-4">🎉 환영합니다!</h2>
          <p class="mb-4">Yesman Agent는 강력한 자동화 및 모니터링 도구입니다.</p>
          <p class="mb-4">이 가이드를 통해 기본 설정과 주요 기능을 안내해드리겠습니다.</p>
          <div class="alert alert-info">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>이 가이드는 언제든지 건너뛸 수 있습니다.</span>
          </div>
        </div>
      `
    },
    {
      id: 'system_check',
      title: '시스템 확인',
      description: '시스템 상태와 연결성을 확인합니다.',
      type: 'action',
      action: async () => {
        const health = await api.getHealthStatus();
        const performance = await api.getPerformanceMetrics();
        
        return {
          health: health.success ? 'healthy' : 'warning',
          performance: performance.success ? 'good' : 'warning',
          details: {
            health_status: health.data?.overall || 'unknown',
            cpu_usage: performance.data?.cpu?.percent || 0,
            memory_usage: performance.data?.memory?.percent || 0
          }
        };
      }
    },
    {
      id: 'features_overview',
      title: '주요 기능 소개',
      description: '대시보드의 주요 기능들을 살펴봅니다.',
      type: 'info',
      content: `
        <div class="space-y-4">
          <h3 class="text-lg font-semibold">🔍 주요 기능</h3>
          
          <div class="grid gap-4 md:grid-cols-2">
            <div class="card bg-base-200 p-4">
              <h4 class="font-medium mb-2">📊 성능 모니터링</h4>
              <p class="text-sm">실시간 시스템 리소스 사용량 모니터링</p>
            </div>
            
            <div class="card bg-base-200 p-4">
              <h4 class="font-medium mb-2">🏥 상태 점검</h4>
              <p class="text-sm">서비스 상태 및 헬스 체크</p>
            </div>
            
            <div class="card bg-base-200 p-4">
              <h4 class="font-medium mb-2">🚀 배포 관리</h4>
              <p class="text-sm">카나리 배포 및 롤백 관리</p>
            </div>
            
            <div class="card bg-base-200 p-4">
              <h4 class="font-medium mb-2">📋 프로세스 관리</h4>
              <p class="text-sm">실행 중인 프로세스 모니터링 및 관리</p>
            </div>
          </div>
          
          <div class="alert alert-success">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>모든 기능은 왼쪽 사이드바에서 쉽게 접근할 수 있습니다.</span>
          </div>
        </div>
      `
    },
    {
      id: 'navigation_tour',
      title: '화면 구성 안내',
      description: '대시보드 화면 구성과 네비게이션을 안내합니다.',
      type: 'info',
      content: `
        <div class="space-y-4">
          <h3 class="text-lg font-semibold">🧭 화면 구성</h3>
          
          <div class="space-y-3">
            <div class="flex items-start gap-3">
              <div class="badge badge-primary">1</div>
              <div>
                <h4 class="font-medium">상단 헤더</h4>
                <p class="text-sm text-base-content/70">현재 시간, 시스템 상태, 알림 등</p>
              </div>
            </div>
            
            <div class="flex items-start gap-3">
              <div class="badge badge-primary">2</div>
              <div>
                <h4 class="font-medium">왼쪽 사이드바</h4>
                <p class="text-sm text-base-content/70">주요 메뉴 및 네비게이션</p>
              </div>
            </div>
            
            <div class="flex items-start gap-3">
              <div class="badge badge-primary">3</div>
              <div>
                <h4 class="font-medium">메인 콘텐츠</h4>
                <p class="text-sm text-base-content/70">선택한 기능의 상세 화면</p>
              </div>
            </div>
            
            <div class="flex items-start gap-3">
              <div class="badge badge-primary">4</div>
              <div>
                <h4 class="font-medium">상태 표시줄</h4>
                <p class="text-sm text-base-content/70">현재 작업 상태 및 진행률</p>
              </div>
            </div>
          </div>
          
          <div class="divider"></div>
          
          <div class="alert alert-info">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span><strong>팁:</strong> 키보드 단축키를 사용하여 빠르게 탐색할 수 있습니다!</span>
          </div>
        </div>
      `
    },
    {
      id: 'configuration',
      title: '기본 설정',
      description: '기본 설정을 확인하고 조정합니다.',
      type: 'action',
      action: async () => {
        const config = await api.getDashboardConfig();
        
        return {
          config_loaded: config.success,
          default_settings: {
            theme: 'light',
            refresh_interval: 30,
            auto_refresh: true,
            notifications: true
          }
        };
      }
    },
    {
      id: 'completion',
      title: '설정 완료',
      description: '온보딩이 완료되었습니다!',
      type: 'completion',
      content: `
        <div class="text-center">
          <h2 class="text-2xl font-bold mb-4">🎊 설정 완료!</h2>
          <p class="mb-4">Yesman Agent 대시보드 설정이 완료되었습니다.</p>
          
          <div class="stats stats-vertical lg:stats-horizontal shadow mb-6">
            <div class="stat">
              <div class="stat-title">완료된 단계</div>
              <div class="stat-value text-primary">${steps.length}</div>
            </div>
            <div class="stat">
              <div class="stat-title">상태</div>
              <div class="stat-value text-success">준비됨</div>
            </div>
          </div>
          
          <div class="space-y-3">
            <p><strong>이제 다음을 할 수 있습니다:</strong></p>
            <ul class="text-sm space-y-1">
              <li>✅ 실시간 시스템 모니터링</li>
              <li>✅ 서비스 상태 확인</li>
              <li>✅ 성능 메트릭 분석</li>
              <li>✅ 배포 관리</li>
            </ul>
          </div>
          
          <div class="alert alert-success mt-4">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>도움이 필요하시면 언제든지 도움말 페이지를 방문해주세요!</span>
          </div>
        </div>
      `
    }
  ];

  // Auto-start if enabled
  if (autoStart && currentStep === 0) {
    setTimeout(() => {
      if (!isSkipped && !isCompleted) {
        nextStep();
      }
    }, 1000);
  }

  async function nextStep() {
    const step = steps[currentStep];
    
    if (step.type === 'action' && step.action) {
      isProcessing = true;
      try {
        const result = await step.action();
        stepResults[currentStep] = result;
      } catch (error) {
        stepResults[currentStep] = { error: error instanceof Error ? error.message : String(error) };
      } finally {
        isProcessing = false;
      }
    }

    if (currentStep < steps.length - 1) {
      currentStep++;
    } else {
      completeWizard();
    }
  }

  function previousStep() {
    if (currentStep > 0) {
      currentStep--;
    }
  }

  function skipWizard() {
    isSkipped = true;
    dispatch('skip');
  }

  function completeWizard() {
    isCompleted = true;
    dispatch('complete', {
      steps_completed: currentStep + 1,
      results: stepResults
    });
  }

  function restartWizard() {
    currentStep = 0;
    isCompleted = false;
    isSkipped = false;
    stepResults = {};
  }

  function getStepIcon(step: any, index: number): string {
    if (index < currentStep) return '✅';
    if (index === currentStep) return '▶️';
    return '⭕';
  }

  function getStepStatus(index: number): string {
    if (index < currentStep) return 'completed';
    if (index === currentStep) return 'current';
    return 'pending';
  }
</script>

<div class="card bg-base-100 shadow-xl max-w-4xl mx-auto">
  <div class="card-header">
    <h2 class="card-title">{title}</h2>
    {#if !isCompleted && !isSkipped}
      <div class="flex items-center gap-2">
        <span class="text-sm">진행률:</span>
        <progress class="progress progress-primary w-32" value={currentStep + 1} max={steps.length}></progress>
        <span class="text-sm">{currentStep + 1}/{steps.length}</span>
      </div>
    {/if}
  </div>

  <div class="card-body">
    {#if !isSkipped && !isCompleted}
      <!-- Steps progress indicator -->
      <div class="mb-6">
        <ul class="steps steps-horizontal w-full">
          {#each steps as step, index}
            <li class="step" class:step-primary={getStepStatus(index) === 'completed' || getStepStatus(index) === 'current'}>
              <div class="flex flex-col items-center">
                <span class="mb-1">{getStepIcon(step, index)}</span>
                <span class="text-xs text-center">{step.title}</span>
              </div>
            </li>
          {/each}
        </ul>
      </div>

      <!-- Current step content -->
      {@const step = steps[currentStep]}
      <div class="min-h-64">
        <div class="mb-4">
          <h3 class="text-xl font-semibold mb-2">{step.title}</h3>
          <p class="text-base-content/70">{step.description}</p>
        </div>

        {#if step.type === 'info' || step.type === 'completion'}
          <div class="prose max-w-none">
            {@html step.content}
          </div>
        {:else if step.type === 'action'}
          <div class="space-y-4">
            {#if isProcessing}
              <div class="flex items-center justify-center py-8">
                <span class="loading loading-spinner loading-lg"></span>
                <span class="ml-3">처리 중...</span>
              </div>
            {:else if stepResults[currentStep]}
              {@const result = stepResults[currentStep]}
              <div class="alert" class:alert-success={!result.error} class:alert-error={result.error}>
                <div>
                  {#if result.error}
                    <h4 class="font-medium">오류 발생</h4>
                    <p>{result.error}</p>
                  {:else}
                    <h4 class="font-medium">확인 완료</h4>
                    <div class="text-sm mt-2">
                      {#if result.details}
                        <ul class="list-disc list-inside">
                          {#each Object.entries(result.details) as [key, value]}
                            <li>{key}: {value}</li>
                          {/each}
                        </ul>
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>
            {:else}
              <div class="alert alert-info">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-6 h-6">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>'{step.title}' 단계를 실행할 준비가 되었습니다.</span>
              </div>
            {/if}
          </div>
        {/if}
      </div>

      <!-- Navigation buttons -->
      <div class="card-actions justify-between mt-6">
        <div class="flex gap-2">
          {#if currentStep > 0}
            <button class="btn btn-outline" on:click={previousStep}>
              이전
            </button>
          {/if}
          <button class="btn btn-ghost" on:click={skipWizard}>
            건너뛰기
          </button>
        </div>

        <div class="flex gap-2">
          {#if currentStep < steps.length - 1}
            <button 
              class="btn btn-primary" 
              class:loading={isProcessing}
              disabled={isProcessing}
              on:click={nextStep}
            >
              {isProcessing ? '처리 중...' : step.type === 'action' && !stepResults[currentStep] ? '실행' : '다음'}
            </button>
          {:else}
            <button class="btn btn-success" on:click={completeWizard}>
              완료
            </button>
          {/if}
        </div>
      </div>

    {:else if isCompleted}
      <!-- Completion screen -->
      <div class="text-center py-8">
        <div class="text-6xl mb-4">🎉</div>
        <h3 class="text-2xl font-bold mb-2">온보딩 완료!</h3>
        <p class="text-base-content/70 mb-6">Yesman Agent 대시보드를 사용할 준비가 되었습니다.</p>
        
        <div class="flex gap-3 justify-center">
          <button class="btn btn-primary" on:click={() => dispatch('complete')}>
            대시보드로 이동
          </button>
          <button class="btn btn-outline" on:click={restartWizard}>
            다시 시작
          </button>
        </div>
      </div>

    {:else if isSkipped}
      <!-- Skipped screen -->
      <div class="text-center py-8">
        <div class="text-4xl mb-4">⏭️</div>
        <h3 class="text-xl font-bold mb-2">온보딩을 건너뛰었습니다</h3>
        <p class="text-base-content/70 mb-6">언제든지 도움말에서 가이드를 다시 볼 수 있습니다.</p>
        
        <div class="flex gap-3 justify-center">
          <button class="btn btn-primary" on:click={() => dispatch('skip')}>
            대시보드로 이동
          </button>
          <button class="btn btn-outline" on:click={restartWizard}>
            가이드 다시 보기
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>