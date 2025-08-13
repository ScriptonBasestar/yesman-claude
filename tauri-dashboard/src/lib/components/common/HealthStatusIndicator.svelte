<script lang="ts">
  import { health, healthStatus, isHealthy, isUnhealthy } from '$lib/stores/health';
  import { onMount } from 'svelte';
  import { api } from '$lib/utils/api';

  export let showDetails = false;
  export let showTimestamp = true;
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let orientation: 'horizontal' | 'vertical' = 'horizontal';

  let expanded = false;
  let isLoading = false;

  onMount(() => {
    refreshHealthStatus();
  });

  async function refreshHealthStatus() {
    if (isLoading) return;
    
    isLoading = true;
    try {
      const response = await api.getHealthStatus();
      if (response.success && response.data) {
        health.update(current => ({
          ...current,
          overall: response.data.overall,
          components: response.data.components,
          lastUpdated: new Date()
        }));
      }
    } catch (error) {
      console.error('Failed to refresh health status:', error);
    } finally {
      isLoading = false;
    }
  }

  function getHealthIcon(status: string): string {
    switch (status) {
      case 'healthy': return '🟢';
      case 'warning': return '🟡';
      case 'error': return '🔴';
      default: return '⚪';
    }
  }

  function getHealthColor(status: string): string {
    switch (status) {
      case 'healthy': return 'text-success';
      case 'warning': return 'text-warning';
      case 'error': return 'text-error';
      default: return 'text-base-content/50';
    }
  }

  function getComponentStatusClass(status: string): string {
    switch (status) {
      case 'healthy': return 'badge-success';
      case 'warning': return 'badge-warning';
      case 'error': return 'badge-error';
      default: return 'badge-ghost';
    }
  }

  function getSizeClass(): string {
    switch (size) {
      case 'sm': return 'text-sm';
      case 'lg': return 'text-lg';
      default: return 'text-base';
    }
  }

  function formatTimestamp(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}시간 전`;
    const days = Math.floor(hours / 24);
    return `${days}일 전`;
  }

  // Component health summary
  $: componentStats = Object.values($health.components).reduce((stats, component) => {
    stats[component.status] = (stats[component.status] || 0) + 1;
    stats.total = (stats.total || 0) + 1;
    return stats;
  }, {} as Record<string, number>);

  $: healthPercentage = componentStats.total > 0 
    ? Math.round(((componentStats.healthy || 0) / componentStats.total) * 100)
    : 0;
</script>

<div class="health-status-indicator {getSizeClass()}" class:vertical={orientation === 'vertical'}>
  <!-- Main status display -->
  <div class="flex items-center gap-2" class:flex-col={orientation === 'vertical'}>
    <!-- Status icon and text -->
    <div class="flex items-center gap-2 cursor-pointer" 
         class:tooltip={!expanded}
         data-tip="클릭하여 세부사항 보기"
         on:click={() => expanded = !expanded}
         on:keydown={(e) => e.key === 'Enter' && (expanded = !expanded)}
         role="button"
         tabindex="0">
      
      <span class="text-lg">{getHealthIcon($health.overall)}</span>
      
      <div class="flex flex-col" class:items-center={orientation === 'vertical'}>
        <span class="font-medium {getHealthColor($health.overall)}">
          {$healthStatus}
        </span>
        
        {#if showTimestamp && size !== 'sm'}
          <span class="text-xs text-base-content/50">
            {formatTimestamp($health.lastUpdated)}
          </span>
        {/if}
      </div>
      
      <!-- Loading indicator -->
      {#if isLoading}
        <span class="loading loading-spinner loading-xs"></span>
      {/if}
    </div>

    <!-- Quick stats for larger sizes -->
    {#if size === 'lg' && componentStats.total > 0}
      <div class="flex gap-1" class:flex-col={orientation === 'vertical'}>
        <div class="badge badge-success badge-sm">
          ✓ {componentStats.healthy || 0}
        </div>
        {#if componentStats.warning}
          <div class="badge badge-warning badge-sm">
            ⚠ {componentStats.warning}
          </div>
        {/if}
        {#if componentStats.error}
          <div class="badge badge-error badge-sm">
            ✗ {componentStats.error}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Refresh button -->
    <button 
      class="btn btn-ghost btn-xs" 
      class:loading={isLoading}
      disabled={isLoading}
      on:click={refreshHealthStatus}
      title="상태 새로고침"
    >
      {#if !isLoading}
        🔄
      {/if}
    </button>
  </div>

  <!-- Expanded details -->
  {#if expanded || showDetails}
    <div class="mt-3 p-3 bg-base-200 rounded-lg" transition:slide>
      <div class="flex justify-between items-center mb-3">
        <h4 class="font-semibold">시스템 구성요소 상태</h4>
        <div class="text-xs text-base-content/70">
          전체 상태: {healthPercentage}% 정상
        </div>
      </div>

      {#if Object.keys($health.components).length > 0}
        <div class="grid gap-2" class:grid-cols-1={orientation === 'vertical'} class:grid-cols-2={orientation === 'horizontal' && size === 'lg'}>
          {#each Object.entries($health.components) as [name, component]}
            <div class="flex items-center justify-between p-2 bg-base-100 rounded">
              <div class="flex items-center gap-2">
                <span>{getHealthIcon(component.status)}</span>
                <span class="font-medium">{name}</span>
              </div>
              
              <div class="flex items-center gap-2">
                <div class="badge badge-sm {getComponentStatusClass(component.status)}">
                  {component.status}
                </div>
                
                {#if component.message}
                  <div class="tooltip tooltip-left" data-tip={component.message}>
                    <span class="text-xs text-base-content/50">ℹ️</span>
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>

        <!-- Health summary -->
        <div class="mt-3 p-2 bg-base-300 rounded text-xs">
          <div class="flex justify-between items-center">
            <span>총 {componentStats.total}개 구성요소</span>
            <span>마지막 업데이트: {$health.lastUpdated.toLocaleTimeString()}</span>
          </div>
          
          {#if componentStats.total > 0}
            <div class="flex gap-4 mt-1">
              <span class="text-success">정상: {componentStats.healthy || 0}</span>
              {#if componentStats.warning}
                <span class="text-warning">경고: {componentStats.warning}</span>
              {/if}
              {#if componentStats.error}
                <span class="text-error">오류: {componentStats.error}</span>
              {/if}
            </div>
          {/if}
        </div>
      {:else}
        <div class="text-center py-4 text-base-content/50">
          <p>구성요소 정보를 불러올 수 없습니다.</p>
          <button class="btn btn-sm btn-outline mt-2" on:click={refreshHealthStatus}>
            다시 시도
          </button>
        </div>
      {/if}

      <!-- Quick actions -->
      {#if size === 'lg'}
        <div class="flex gap-2 mt-3">
          <button class="btn btn-sm btn-outline" on:click={() => window.location.href = '/monitoring'}>
            상세 모니터링
          </button>
          <button class="btn btn-sm btn-outline" on:click={() => window.location.href = '/help'}>
            문제 해결
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .health-status-indicator.vertical {
    max-width: 200px;
  }
  
  .health-status-indicator :global(.slide-transition) {
    transition: all 0.3s ease;
  }
</style>