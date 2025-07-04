<script lang="ts">
  import { page } from '$app/stores';
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  // 네비게이션 메뉴 아이템
  const navItems = [
    {
      path: '/',
      icon: '🏠',
      label: 'Dashboard',
      description: 'Main overview'
    },
    {
      path: '/sessions',
      icon: '🖥️',
      label: 'Sessions',
      description: 'Tmux sessions'
    },
    {
      path: '/controllers',
      icon: '🤖',
      label: 'Controllers',
      description: 'Claude managers'
    },
    {
      path: '/logs',
      icon: '📋',
      label: 'Logs',
      description: 'Activity logs'
    },
    {
      path: '/settings',
      icon: '⚙️',
      label: 'Settings',
      description: 'Configuration'
    }
  ];
  
  // 빠른 액션 버튼들
  const quickActions = [
    {
      action: 'refresh',
      icon: '🔄',
      label: 'Refresh All',
      variant: 'btn-outline'
    },
    {
      action: 'setup',
      icon: '⚡',
      label: 'Setup Sessions',
      variant: 'btn-primary'
    },
    {
      action: 'teardown',
      icon: '🛑',
      label: 'Teardown All',
      variant: 'btn-error'
    }
  ];
  
  function handleQuickAction(action: string) {
    dispatch('quickAction', { action });
  }
  
  // 현재 경로 확인
  $: currentPath = $page.url.pathname;
</script>

<aside class="sidebar bg-base-200 w-64 min-h-screen p-4 space-y-6">
  <!-- 로고 및 타이틀 -->
  <div class="sidebar-header">
    <div class="flex items-center gap-3 mb-2">
      <div class="avatar placeholder">
        <div class="bg-primary text-primary-content rounded-full w-10">
          <span class="text-xl">🚀</span>
        </div>
      </div>
      <div>
        <h1 class="text-lg font-bold text-base-content">Yesman</h1>
        <p class="text-xs text-base-content/60">Claude Dashboard</p>
      </div>
    </div>
  </div>
  
  <!-- 네비게이션 메뉴 -->
  <nav class="navigation">
    <h2 class="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
      Navigation
    </h2>
    
    <ul class="menu menu-vertical space-y-1">
      {#each navItems as item}
        <li>
          <a 
            href={item.path}
            class="menu-item flex items-center gap-3 p-3 rounded-lg transition-colors"
            class:active={currentPath === item.path}
          >
            <span class="text-xl">{item.icon}</span>
            <div class="flex-1">
              <div class="font-medium text-sm">{item.label}</div>
              <div class="text-xs text-base-content/60">{item.description}</div>
            </div>
          </a>
        </li>
      {/each}
    </ul>
  </nav>
  
  <!-- 빠른 액션 -->
  <div class="quick-actions">
    <h2 class="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
      Quick Actions
    </h2>
    
    <div class="space-y-2">
      {#each quickActions as action}
        <button 
          class="btn {action.variant} btn-sm w-full justify-start gap-2"
          on:click={() => handleQuickAction(action.action)}
        >
          <span>{action.icon}</span>
          <span class="text-xs">{action.label}</span>
        </button>
      {/each}
    </div>
  </div>
  
  <!-- 상태 정보 -->
  <div class="status-info">
    <h2 class="text-xs font-semibold text-base-content/60 uppercase tracking-wider mb-3">
      System Status
    </h2>
    
    <div class="space-y-2">
      <div class="stat-item bg-base-100 p-2 rounded-lg">
        <div class="flex justify-between items-center">
          <span class="text-xs text-base-content/70">Uptime</span>
          <span class="text-xs font-mono text-base-content">2h 34m</span>
        </div>
      </div>
      
      <div class="stat-item bg-base-100 p-2 rounded-lg">
        <div class="flex justify-between items-center">
          <span class="text-xs text-base-content/70">Memory</span>
          <span class="text-xs font-mono text-base-content">142MB</span>
        </div>
      </div>
      
      <div class="stat-item bg-base-100 p-2 rounded-lg">
        <div class="flex justify-between items-center">
          <span class="text-xs text-base-content/70">Sessions</span>
          <span class="text-xs font-mono text-base-content badge badge-primary badge-sm">3</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 하단 정보 -->
  <div class="sidebar-footer mt-auto pt-4 border-t border-base-content/10">
    <div class="text-center">
      <p class="text-xs text-base-content/50">
        v1.0.0 • Tauri + Svelte
      </p>
      <p class="text-xs text-base-content/30 mt-1">
        Built with ❤️
      </p>
    </div>
  </div>
</aside>

<style>
  .sidebar {
    @apply flex flex-col;
  }
  
  .menu-item {
    @apply hover:bg-base-300;
  }
  
  .menu-item.active {
    @apply bg-primary text-primary-content;
  }
  
  .menu-item.active .text-base-content\/60 {
    @apply text-primary-content/70;
  }
  
  .stat-item {
    @apply border border-base-content/5;
  }
  
  .sidebar-footer {
    @apply mt-auto;
  }
</style>