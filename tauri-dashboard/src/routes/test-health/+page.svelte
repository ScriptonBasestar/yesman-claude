<script lang="ts">
  import { health, isHealthy, healthStatus, formatLastCheck } from '$lib/stores/health';
  import { api } from '$lib/utils/api';
  
  async function manualCheck() {
    await health.check();
  }
  
  async function simulateError() {
    // Temporarily change API URL to simulate error
    const originalUrl = import.meta.env.VITE_API_URL;
    // @ts-ignore
    import.meta.env.VITE_API_URL = 'http://localhost:9999';
    await health.check();
    // @ts-ignore
    import.meta.env.VITE_API_URL = originalUrl;
  }
</script>

<svelte:head>
  <title>Health Check Test - Yesman</title>
</svelte:head>

<div class="p-6 max-w-4xl mx-auto">
  <h1 class="text-2xl font-bold mb-6">API Health Check Test</h1>
  
  <div class="card bg-base-200 shadow-xl mb-6">
    <div class="card-body">
      <h2 class="card-title">Current Status</h2>
      
      <div class="stats shadow">
        <div class="stat">
          <div class="stat-title">Connection Status</div>
          <div class="stat-value text-{$healthStatus.color}">
            <span class="text-2xl mr-2">{$healthStatus.icon}</span>
            {$healthStatus.text}
          </div>
          <div class="stat-desc">
            {#if $health.lastCheck}
              Last checked: {formatLastCheck($health.lastCheck)}
            {:else}
              Never checked
            {/if}
          </div>
        </div>
        
        <div class="stat">
          <div class="stat-title">API Details</div>
          <div class="stat-value text-sm">
            {#if $health.service}
              {$health.service}
            {:else}
              Unknown
            {/if}
          </div>
          <div class="stat-desc">
            Version: {$health.version || 'Unknown'}
          </div>
        </div>
        
        <div class="stat">
          <div class="stat-title">Retry Count</div>
          <div class="stat-value">{$health.retryCount}</div>
          <div class="stat-desc">
            {#if $health.error}
              Error: {$health.error}
            {:else}
              No errors
            {/if}
          </div>
        </div>
      </div>
      
      <div class="card-actions justify-end mt-4">
        <button class="btn btn-primary" on:click={manualCheck}>
          Manual Check
        </button>
        <button class="btn btn-error" on:click={simulateError}>
          Simulate Error
        </button>
      </div>
    </div>
  </div>
  
  <div class="card bg-base-200 shadow-xl">
    <div class="card-body">
      <h2 class="card-title">Raw State</h2>
      <pre class="bg-base-300 p-4 rounded overflow-auto">{JSON.stringify($health, null, 2)}</pre>
    </div>
  </div>
  
  <div class="mt-6">
    <p class="text-sm text-base-content/70">
      This page tests the health check functionality. The health check runs automatically every 30 seconds,
      but you can also trigger manual checks or simulate errors.
    </p>
  </div>
</div>