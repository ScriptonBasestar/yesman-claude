<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { health, healthStatus, formatLastCheck } from '$lib/stores/health';
  import { api } from '$lib/utils/api';

  export let showText = true;
  export let showIcon = true;
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let refreshInterval = 30000; // 30 seconds
  export let clickable = true;

  let refreshTimer: NodeJS.Timeout | null = null;
  let isRefreshing = false;
  let lastError: string | null = null;
  let connectionCount = 0;
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 3;

  // Connection states
  let isConnected = true;
  let isConnecting = false;
  let hasError = false;

  onMount(() => {
    checkConnection();
    startAutoRefresh();
  });

  onDestroy(() => {
    stopAutoRefresh();
  });

  function startAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
    }
    
    refreshTimer = setInterval(() => {
      if (!isRefreshing) {
        checkConnection();
      }
    }, refreshInterval);
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  async function checkConnection() {
    if (isRefreshing) return;

    isRefreshing = true;
    isConnecting = true;
    hasError = false;
    lastError = null;

    try {
      const response = await api.getHealthStatus();
      
      if (response.success) {
        isConnected = true;
        connectionCount++;
        reconnectAttempts = 0;
        
        // Update health store if we have valid data
        if (response.data) {
          health.update(current => ({
            ...current,
            overall: response.data.overall,
            components: response.data.components,
            lastUpdated: new Date()
          }));
        }
      } else {
        throw new Error(response.error || 'Connection failed');
      }
    } catch (error) {
      isConnected = false;
      hasError = true;
      lastError = error instanceof Error ? error.message : String(error);
      reconnectAttempts++;
      
      // Try to reconnect if we haven't exceeded max attempts
      if (reconnectAttempts < maxReconnectAttempts) {
        setTimeout(() => {
          if (!isConnected) {
            checkConnection();
          }
        }, 2000 * reconnectAttempts); // Exponential backoff
      }
    } finally {
      isRefreshing = false;
      isConnecting = false;
    }
  }

  function handleClick() {
    if (clickable && !isRefreshing) {
      checkConnection();
    }
  }

  function getBadgeClass(): string {
    const baseClass = `badge`;
    
    let sizeClass = '';
    switch (size) {
      case 'sm':
        sizeClass = 'badge-sm';
        break;
      case 'lg':
        sizeClass = 'badge-lg';
        break;
      default:
        sizeClass = '';
    }

    let statusClass = '';
    if (isConnecting || isRefreshing) {
      statusClass = 'badge-warning';
    } else if (isConnected && !hasError) {
      statusClass = 'badge-success';
    } else if (hasError || !isConnected) {
      statusClass = 'badge-error';
    } else {
      statusClass = 'badge-ghost';
    }

    const clickableClass = clickable ? 'cursor-pointer hover:badge-outline' : '';

    return `${baseClass} ${sizeClass} ${statusClass} ${clickableClass}`.trim();
  }

  function getStatusText(): string {
    if (isConnecting || isRefreshing) {
      return '연결 확인 중...';
    } else if (isConnected && !hasError) {
      return '정상 연결됨';
    } else if (hasError || !isConnected) {
      return '연결 실패';
    } else {
      return '상태 확인 중';
    }
  }

  function getStatusIcon(): string {
    if (isConnecting || isRefreshing) {
      return '🔄';
    } else if (isConnected && !hasError) {
      return '🟢';
    } else if (hasError || !isConnected) {
      return '🔴';
    } else {
      return '🟡';
    }
  }

  // Reactive statements for status
  $: statusText = getStatusText();
  $: statusIcon = getStatusIcon();
  $: badgeClass = getBadgeClass();
  
  // Connection quality indicator
  $: connectionQuality = isConnected ? 
    (reconnectAttempts === 0 ? 'excellent' : 
     reconnectAttempts === 1 ? 'good' : 
     reconnectAttempts === 2 ? 'poor' : 'unstable') : 'disconnected';
</script>

<div class="flex items-center gap-2">
  <!-- Main status badge -->
  <div 
    class={badgeClass}
    class:animate-pulse={isConnecting || isRefreshing}
    title={lastError || statusText}
    role="button"
    tabindex={clickable ? 0 : -1}
    on:click={handleClick}
    on:keydown={(e) => e.key === 'Enter' && handleClick()}
  >
    {#if showIcon}
      <span class="mr-1">{statusIcon}</span>
    {/if}
    
    {#if showText}
      <span>{statusText}</span>
    {/if}
    
    {#if isRefreshing}
      <span class="loading loading-spinner loading-xs ml-1"></span>
    {/if}
  </div>

  <!-- Connection quality indicator (only show if connected) -->
  {#if isConnected && size !== 'sm'}
    <div class="tooltip tooltip-bottom" data-tip="연결 품질: {connectionQuality}">
      <div class="flex gap-1">
        <div class="w-1 h-3 bg-success rounded-full" class:opacity-30={connectionQuality === 'disconnected'}></div>
        <div class="w-1 h-3 bg-success rounded-full" class:opacity-30={['disconnected', 'unstable'].includes(connectionQuality)}></div>
        <div class="w-1 h-3 bg-success rounded-full" class:opacity-30={['disconnected', 'unstable', 'poor'].includes(connectionQuality)}></div>
        <div class="w-1 h-3 bg-success rounded-full" class:opacity-30={['disconnected', 'unstable', 'poor', 'good'].includes(connectionQuality)}></div>
      </div>
    </div>
  {/if}
</div>

<!-- Additional info for larger sizes -->
{#if size === 'lg' && (showText || lastError)}
  <div class="text-xs text-base-content/70 mt-1">
    {#if lastError && hasError}
      <div class="text-error">
        오류: {lastError}
      </div>
    {:else if isConnected}
      <div class="flex gap-4">
        <span>연결 수: {connectionCount}</span>
        <span>마지막 확인: {$formatLastCheck}</span>
        {#if reconnectAttempts > 0}
          <span class="text-warning">재시도: {reconnectAttempts}/{maxReconnectAttempts}</span>
        {/if}
      </div>
    {/if}
  </div>
{/if}

<!-- Debug info (only in development) -->
{#if import.meta.env.DEV && size === 'lg'}
  <details class="text-xs mt-2">
    <summary class="cursor-pointer text-base-content/50">디버그 정보</summary>
    <div class="mt-1 p-2 bg-base-200 rounded text-base-content/70">
      <div>연결 상태: {isConnected ? '연결됨' : '연결 안됨'}</div>
      <div>새로고침 중: {isRefreshing ? '예' : '아니오'}</div>
      <div>연결 중: {isConnecting ? '예' : '아니오'}</div>
      <div>오류 상태: {hasError ? '예' : '아니오'}</div>
      <div>재시도 횟수: {reconnectAttempts}</div>
      <div>연결 품질: {connectionQuality}</div>
      <div>전체 상태: {$health.overall}</div>
      <div>컴포넌트 수: {Object.keys($health.components).length}</div>
    </div>
  </details>
{/if}