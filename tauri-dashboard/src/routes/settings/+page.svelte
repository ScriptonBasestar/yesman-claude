<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    config, 
    isConfigLoading, 
    configError, 
    hasUnsavedChanges,
    updateConfig,
    updateThemeConfig,
    updateNotificationConfig,
    updateDashboardConfig,
    updateAdvancedConfig,
    saveConfig,
    resetConfig,
    exportConfig,
    importConfig,
    toggleDebugMode
  } from '$lib/stores/config';
  import { showNotification } from '$lib/stores/notifications';
  import { tauriUtils } from '$lib/utils/tauri';

  let activeTab = 'general';
  let importFileInput: HTMLInputElement;

  // 테마 옵션
  const themeOptions = [
    { value: 'light', label: 'Light', icon: '☀️' },
    { value: 'dark', label: 'Dark', icon: '🌙' },
    { value: 'auto', label: 'Auto', icon: '🔄' }
  ];

  // 언어 옵션
  const languageOptions = [
    { value: 'en', label: 'English', icon: '🇺🇸' },
    { value: 'ko', label: '한국어', icon: '🇰🇷' }
  ];

  // 로그 레벨 옵션
  const logLevelOptions = [
    { value: 'error', label: 'Error Only' },
    { value: 'warn', label: 'Warning & Error' },
    { value: 'info', label: 'Info & Above' },
    { value: 'debug', label: 'Debug (All)' }
  ];

  // 기본 뷰 옵션
  const defaultViewOptions = [
    { value: 'grid', label: 'Grid View', icon: '⊞' },
    { value: 'list', label: 'List View', icon: '☰' }
  ];

  onMount(() => {
    // 설정 페이지 진입 시 최신 설정 로드
    if (!$config) {
      // loadConfig(); // config store에서 자동 로드됨
    }
  });

  // 설정 저장
  async function handleSave() {
    try {
      await saveConfig();
      showNotification('success', 'Settings Saved', 'Your settings have been saved successfully');
    } catch (error) {
      showNotification('error', 'Save Failed', 'Failed to save settings');
    }
  }

  // 설정 리셋
  async function handleReset() {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      try {
        await resetConfig();
        showNotification('success', 'Settings Reset', 'All settings have been reset to defaults');
      } catch (error) {
        showNotification('error', 'Reset Failed', 'Failed to reset settings');
      }
    }
  }

  // 설정 내보내기
  function handleExport() {
    try {
      const configData = exportConfig();
      const blob = new Blob([configData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `yesman-config-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('success', 'Config Exported', 'Configuration exported successfully');
    } catch (error) {
      showNotification('error', 'Export Failed', 'Failed to export configuration');
    }
  }

  // 설정 가져오기
  async function handleImport(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    
    if (!file) return;

    try {
      const text = await file.text();
      const success = await importConfig(text);
      
      if (success) {
        showNotification('success', 'Config Imported', 'Configuration imported successfully');
      } else {
        showNotification('error', 'Import Failed', 'Invalid configuration file');
      }
    } catch (error) {
      showNotification('error', 'Import Failed', 'Failed to import configuration');
    }
    
    // 파일 입력 초기화
    target.value = '';
  }

  // 테스트 알림
  function handleTestNotification() {
    showNotification('info', 'Test Notification', 'This is a test notification to verify your settings');
  }

  // 로그 파일 열기
  async function handleOpenLogs() {
    try {
      await tauriUtils.openLogFile();
    } catch (error) {
      showNotification('error', 'Failed to Open Logs', 'Could not open log file');
    }
  }

  // 앱 재시작
  async function handleRestart() {
    if (confirm('Are you sure you want to restart the application?')) {
      try {
        await tauriUtils.restartApp();
      } catch (error) {
        showNotification('error', 'Restart Failed', 'Failed to restart application');
      }
    }
  }
</script>

<svelte:head>
  <title>Settings - Yesman Dashboard</title>
</svelte:head>

<div class="settings-page p-6">
  <!-- 페이지 헤더 -->
  <div class="page-header mb-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-3xl font-bold text-base-content flex items-center gap-3">
          ⚙️ Settings
        </h1>
        <p class="text-base-content/70 mt-2">
          Configure your dashboard preferences and behavior
        </p>
      </div>
      
      <div class="header-actions flex gap-3">
        {#if $hasUnsavedChanges}
          <div class="badge badge-warning gap-2">
            ⚠️ Unsaved Changes
          </div>
        {/if}
        
        <button 
          class="btn btn-outline btn-sm"
          on:click={handleReset}
          disabled={$isConfigLoading}
        >
          🔄 Reset
        </button>
        
        <button 
          class="btn btn-primary btn-sm"
          class:loading={$isConfigLoading}
          on:click={handleSave}
          disabled={$isConfigLoading || !$hasUnsavedChanges}
        >
          💾 Save Settings
        </button>
      </div>
    </div>
  </div>

  <!-- 에러 표시 -->
  {#if $configError}
    <div class="alert alert-error mb-6">
      <div>
        <h3 class="font-bold">Configuration Error</h3>
        <div class="text-xs">{$configError}</div>
      </div>
    </div>
  {/if}

  <div class="settings-container grid grid-cols-1 lg:grid-cols-4 gap-6">
    <!-- 설정 탭 사이드바 -->
    <div class="settings-sidebar">
      <ul class="menu bg-base-200 rounded-box">
        <li>
          <button 
            class="menu-item"
            class:active={activeTab === 'general'}
            on:click={() => activeTab = 'general'}
          >
            🎨 General
          </button>
        </li>
        <li>
          <button 
            class="menu-item"
            class:active={activeTab === 'notifications'}
            on:click={() => activeTab = 'notifications'}
          >
            🔔 Notifications
          </button>
        </li>
        <li>
          <button 
            class="menu-item"
            class:active={activeTab === 'dashboard'}
            on:click={() => activeTab = 'dashboard'}
          >
            📊 Dashboard
          </button>
        </li>
        <li>
          <button 
            class="menu-item"
            class:active={activeTab === 'advanced'}
            on:click={() => activeTab = 'advanced'}
          >
            🔧 Advanced
          </button>
        </li>
        <li>
          <button 
            class="menu-item"
            class:active={activeTab === 'system'}
            on:click={() => activeTab = 'system'}
          >
            🖥️ System
          </button>
        </li>
        <li>
          <button 
            class="menu-item"
            class:active={activeTab === 'import-export'}
            on:click={() => activeTab = 'import-export'}
          >
            📁 Import/Export
          </button>
        </li>
      </ul>
    </div>

    <!-- 설정 내용 -->
    <div class="settings-content lg:col-span-3">
      {#if activeTab === 'general'}
        <div class="settings-section">
          <h2 class="text-xl font-semibold mb-4">🎨 General Settings</h2>
          
          <!-- 테마 설정 -->
          <div class="setting-group">
            <h3 class="text-lg font-medium mb-3">Appearance</h3>
            
            <div class="form-control">
              <label class="label" for="theme-selection">
                <span class="label-text">Theme</span>
              </label>
              <div class="join" id="theme-selection" role="radiogroup">
                {#each themeOptions as option}
                  <input 
                    class="join-item btn"
                    type="radio"
                    name="theme"
                    id="theme-{option.value}"
                    aria-label="{option.icon} {option.label}"
                    value={option.value}
                    checked={$config.theme === option.value}
                    on:change={() => updateThemeConfig(option.value)}
                  />
                {/each}
              </div>
            </div>

            <div class="form-control">
              <label class="label" for="language-select">
                <span class="label-text">Language</span>
              </label>
              <select 
                id="language-select"
                class="select select-bordered w-full max-w-xs"
                bind:value={$config.language}
                on:change={(e) => updateConfig({ language: e.currentTarget.value })}
              >
                {#each languageOptions as option}
                  <option value={option.value}>{option.icon} {option.label}</option>
                {/each}
              </select>
            </div>
          </div>

          <!-- 자동 새로고침 설정 -->
          <div class="setting-group">
            <h3 class="text-lg font-medium mb-3">Auto Refresh</h3>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Enable auto refresh</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-primary"
                  bind:checked={$config.autoRefresh.enabled}
                  on:change={(e) => updateConfig({ 
                    autoRefresh: { ...$config.autoRefresh, enabled: e.currentTarget.checked }
                  })}
                />
              </label>
            </div>

            {#if $config.autoRefresh.enabled}
              <div class="form-control">
                <label class="label" for="refresh-interval">
                  <span class="label-text">Refresh interval (seconds)</span>
                </label>
                <input 
                  id="refresh-interval"
                  type="range"
                  min="5"
                  max="60"
                  step="5"
                  class="range range-primary"
                  value={$config.autoRefresh.interval / 1000}
                  on:input={(e) => updateConfig({ 
                    autoRefresh: { ...$config.autoRefresh, interval: parseInt(e.currentTarget.value) * 1000 }
                  })}
                />
                <div class="w-full flex justify-between text-xs px-2">
                  <span>5s</span>
                  <span>30s</span>
                  <span>60s</span>
                </div>
                <div class="text-center text-sm mt-1">
                  Current: {$config.autoRefresh.interval / 1000}s
                </div>
              </div>
            {/if}
          </div>
        </div>

      {:else if activeTab === 'notifications'}
        <div class="settings-section">
          <h2 class="text-xl font-semibold mb-4">🔔 Notification Settings</h2>
          
          <div class="setting-group">
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Enable notifications</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-primary"
                  bind:checked={$config.notifications.enabled}
                  on:change={(e) => updateNotificationConfig({ enabled: e.currentTarget.checked })}
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Desktop notifications</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-secondary"
                  bind:checked={$config.notifications.desktop}
                  on:change={(e) => updateNotificationConfig({ desktop: e.currentTarget.checked })}
                  disabled={!$config.notifications.enabled}
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Sound notifications</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-accent"
                  bind:checked={$config.notifications.sounds}
                  on:change={(e) => updateNotificationConfig({ sounds: e.currentTarget.checked })}
                  disabled={!$config.notifications.enabled}
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Auto-hide notifications</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-info"
                  bind:checked={$config.notifications.autoHide}
                  on:change={(e) => updateNotificationConfig({ autoHide: e.currentTarget.checked })}
                  disabled={!$config.notifications.enabled}
                />
              </label>
            </div>

            {#if $config.notifications.autoHide}
              <div class="form-control">
                <label class="label" for="hide-delay">
                  <span class="label-text">Auto-hide delay (seconds)</span>
                </label>
                <input 
                  id="hide-delay"
                  type="range"
                  min="2"
                  max="10"
                  step="1"
                  class="range range-info"
                  value={$config.notifications.hideDelay / 1000}
                  on:input={(e) => updateNotificationConfig({ 
                    hideDelay: parseInt(e.currentTarget.value) * 1000 
                  })}
                />
                <div class="text-center text-sm mt-1">
                  {$config.notifications.hideDelay / 1000} seconds
                </div>
              </div>
            {/if}

            <div class="mt-4">
              <button 
                class="btn btn-outline btn-sm"
                on:click={handleTestNotification}
              >
                🧪 Test Notification
              </button>
            </div>
          </div>
        </div>

      {:else if activeTab === 'dashboard'}
        <div class="settings-section">
          <h2 class="text-xl font-semibold mb-4">📊 Dashboard Settings</h2>
          
          <div class="setting-group">
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Compact mode</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-primary"
                  bind:checked={$config.dashboard.compactMode}
                  on:change={(e) => updateDashboardConfig({ compactMode: e.currentTarget.checked })}
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Show performance metrics</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-secondary"
                  bind:checked={$config.dashboard.showMetrics}
                  on:change={(e) => updateDashboardConfig({ showMetrics: e.currentTarget.checked })}
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Show charts</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-accent"
                  bind:checked={$config.dashboard.showCharts}
                  on:change={(e) => updateDashboardConfig({ showCharts: e.currentTarget.checked })}
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label" for="default-view-selection">
                <span class="label-text">Default view</span>
              </label>
              <div class="join" id="default-view-selection" role="radiogroup">
                {#each defaultViewOptions as option}
                  <input 
                    class="join-item btn"
                    type="radio"
                    name="defaultView"
                    id="view-{option.value}"
                    aria-label="{option.icon} {option.label}"
                    value={option.value}
                    checked={$config.dashboard.defaultView === option.value}
                    on:change={() => updateDashboardConfig({ defaultView: option.value })}
                  />
                {/each}
              </div>
            </div>

            <div class="form-control">
              <label class="label" for="sessions-per-page">
                <span class="label-text">Sessions per page</span>
              </label>
              <input 
                id="sessions-per-page"
                type="range"
                min="10"
                max="50"
                step="5"
                class="range range-primary"
                bind:value={$config.dashboard.sessionsPerPage}
                on:input={(e) => updateDashboardConfig({ 
                  sessionsPerPage: parseInt(e.currentTarget.value) 
                })}
              />
              <div class="text-center text-sm mt-1">
                {$config.dashboard.sessionsPerPage} sessions
              </div>
            </div>
          </div>
        </div>

      {:else if activeTab === 'advanced'}
        <div class="settings-section">
          <h2 class="text-xl font-semibold mb-4">🔧 Advanced Settings</h2>
          
          <div class="setting-group">
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Debug mode</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-warning"
                  bind:checked={$config.advanced.debugMode}
                  on:change={toggleDebugMode}
                />
              </label>
              <label class="label">
                <span class="label-text-alt">Enable detailed logging and debug information</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label" for="log-level-select">
                <span class="label-text">Log level</span>
              </label>
              <select 
                id="log-level-select"
                class="select select-bordered w-full max-w-xs"
                bind:value={$config.advanced.logLevel}
                on:change={(e) => updateAdvancedConfig({ logLevel: e.currentTarget.value })}
              >
                {#each logLevelOptions as option}
                  <option value={option.value}>{option.label}</option>
                {/each}
              </select>
            </div>

            <div class="form-control">
              <label class="label" for="max-log-size">
                <span class="label-text">Max log size (MB)</span>
              </label>
              <input 
                id="max-log-size"
                type="number"
                min="1"
                max="100"
                class="input input-bordered w-full max-w-xs"
                value={Math.round($config.advanced.maxLogSize / 1048576)}
                on:input={(e) => updateAdvancedConfig({ 
                  maxLogSize: parseInt(e.currentTarget.value) * 1048576 
                })}
              />
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Enable telemetry</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-info"
                  bind:checked={$config.advanced.enableTelemetry}
                  on:change={(e) => updateAdvancedConfig({ enableTelemetry: e.currentTarget.checked })}
                />
              </label>
              <label class="label">
                <span class="label-text-alt">Help improve the app by sending usage data</span>
              </label>
            </div>

            <div class="mt-4">
              <button 
                class="btn btn-outline btn-sm"
                on:click={handleOpenLogs}
              >
                📋 Open Log Files
              </button>
            </div>
          </div>
        </div>

      {:else if activeTab === 'system'}
        <div class="settings-section">
          <h2 class="text-xl font-semibold mb-4">🖥️ System Settings</h2>
          
          <div class="setting-group">
            <h3 class="text-lg font-medium mb-3">Python Configuration</h3>
            
            <div class="form-control">
              <label class="label" for="python-executable">
                <span class="label-text">Python executable</span>
              </label>
              <input 
                id="python-executable"
                type="text"
                class="input input-bordered w-full"
                bind:value={$config.python.executable}
                on:input={(e) => updateConfig({ 
                  python: { ...$config.python, executable: e.currentTarget.value }
                })}
                placeholder="python3"
              />
            </div>

            <div class="form-control">
              <label class="label" for="python-venv">
                <span class="label-text">Virtual environment (optional)</span>
              </label>
              <input 
                id="python-venv"
                type="text"
                class="input input-bordered w-full"
                bind:value={$config.python.virtualEnv}
                on:input={(e) => updateConfig({ 
                  python: { ...$config.python, virtualEnv: e.currentTarget.value }
                })}
                placeholder="/path/to/venv"
              />
            </div>
          </div>

          <div class="setting-group">
            <h3 class="text-lg font-medium mb-3">Tmux Configuration</h3>
            
            <div class="form-control">
              <label class="label" for="tmux-executable">
                <span class="label-text">Tmux executable</span>
              </label>
              <input 
                id="tmux-executable"
                type="text"
                class="input input-bordered w-full"
                bind:value={$config.tmux.executable}
                on:input={(e) => updateConfig({ 
                  tmux: { ...$config.tmux, executable: e.currentTarget.value }
                })}
                placeholder="tmux"
              />
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Auto-attach to sessions</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-primary"
                  bind:checked={$config.tmux.autoAttach}
                  on:change={(e) => updateConfig({ 
                    tmux: { ...$config.tmux, autoAttach: e.currentTarget.checked }
                  })}
                />
              </label>
            </div>

            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">Enable mouse mode</span>
                <input 
                  type="checkbox" 
                  class="toggle toggle-secondary"
                  bind:checked={$config.tmux.mouseMode}
                  on:change={(e) => updateConfig({ 
                    tmux: { ...$config.tmux, mouseMode: e.currentTarget.checked }
                  })}
                />
              </label>
            </div>
          </div>

          <div class="setting-group">
            <h3 class="text-lg font-medium mb-3">Application Actions</h3>
            
            <div class="flex gap-3">
              <button 
                class="btn btn-warning btn-sm"
                on:click={handleRestart}
              >
                🔄 Restart App
              </button>
            </div>
          </div>
        </div>

      {:else if activeTab === 'import-export'}
        <div class="settings-section">
          <h2 class="text-xl font-semibold mb-4">📁 Import/Export Settings</h2>
          
          <div class="setting-group">
            <h3 class="text-lg font-medium mb-3">Configuration Backup</h3>
            
            <div class="flex gap-3 mb-4">
              <button 
                class="btn btn-primary btn-sm"
                on:click={handleExport}
              >
                📤 Export Configuration
              </button>
              
              <button 
                class="btn btn-secondary btn-sm"
                on:click={() => importFileInput.click()}
              >
                📥 Import Configuration
              </button>
            </div>

            <input 
              bind:this={importFileInput}
              type="file"
              accept=".json"
              style="display: none"
              on:change={handleImport}
            />

            <div class="alert alert-info">
              <div>
                <h4 class="font-bold">Backup Information</h4>
                <p class="text-sm">
                  Export your settings to back them up or transfer to another installation.
                  Import will overwrite your current settings.
                </p>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .settings-page {
    @apply max-w-7xl mx-auto;
  }
  
  .settings-section {
    @apply bg-base-100 rounded-lg border border-base-content/10 p-6;
  }
  
  .setting-group {
    @apply space-y-4 mb-6 pb-6 border-b border-base-content/10 last:border-b-0 last:mb-0 last:pb-0;
  }
  
  .menu-item {
    @apply w-full text-left;
  }
  
  .menu-item.active {
    @apply bg-primary text-primary-content;
  }
</style>