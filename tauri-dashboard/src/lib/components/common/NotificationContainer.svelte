<script lang="ts">
  import { notifications, dismissNotification, clearAllNotifications, notificationSettings } from '$lib/stores/notifications';
  import { fade, fly } from 'svelte/transition';
  import { createEventDispatcher, onMount } from 'svelte';

  const dispatch = createEventDispatcher();

  // 알림 타입별 아이콘 및 스타일
  const notificationStyles = {
    success: {
      icon: '✅',
      class: 'alert-success',
      bgClass: 'bg-success',
      textClass: 'text-success-content'
    },
    error: {
      icon: '❌',
      class: 'alert-error',
      bgClass: 'bg-error',
      textClass: 'text-error-content'
    },
    warning: {
      icon: '⚠️',
      class: 'alert-warning',
      bgClass: 'bg-warning',
      textClass: 'text-warning-content'
    },
    info: {
      icon: 'ℹ️',
      class: 'alert-info',
      bgClass: 'bg-info',
      textClass: 'text-info-content'
    }
  };

  function getNotificationStyle(type: string) {
    return notificationStyles[type as keyof typeof notificationStyles] || notificationStyles.info;
  }

  function formatTime(timestamp: number) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  function handleDismiss(id: string) {
    dismissNotification(id);
  }

  function handleClearAll() {
    clearAllNotifications();
  }

  // 알림이 있는지 확인
  $: hasNotifications = $notifications.length > 0;
  $: unreadCount = $notifications.filter(n => !n.read).length;

  // 알림 자동 숨김 타이머 관리
  let timers = new Map<string, number>();

  // 새 알림이 추가될 때마다 타이머 설정
  $: {
    $notifications.forEach(notification => {
      if (!timers.has(notification.id) && 
          !notification.persistent && 
          !(notification.type === 'error' && $notificationSettings.persistErrors)) {
        const delay = notification.type === 'error' 
          ? $notificationSettings.errorHideDelay 
          : $notificationSettings.autoHideDelay;
        const timer = window.setTimeout(() => {
          dismissNotification(notification.id);
          timers.delete(notification.id);
        }, delay);
        
        timers.set(notification.id, timer);
      }
    });
  }

  // 컴포넌트 언마운트 시 타이머 정리
  onMount(() => {
    return () => {
      timers.forEach(timer => clearTimeout(timer));
      timers.clear();
    };
  });
</script>

<!-- 토스트 알림 컨테이너 (우측 상단) -->
<div class="toast-container fixed top-4 right-4 z-50 space-y-2">
  {#each $notifications.slice(0, 5) as notification (notification.id)}
    <div
      class="alert {getNotificationStyle(notification.type).class} shadow-lg max-w-sm relative pr-12 overflow-hidden"
      in:fly={{ x: 300, duration: 300 }}
      out:fade={{ duration: 200 }}
    >
      <div class="flex items-start gap-3">
        <span class="text-lg flex-shrink-0">
          {getNotificationStyle(notification.type).icon}
        </span>

        <div class="flex-1 min-w-0">
          <div class="font-semibold text-sm">
            {notification.title}
          </div>
          {#if notification.message}
            <div class="text-xs opacity-90 mt-1">
              {notification.message}
            </div>
          {/if}
          <div class="text-xs opacity-75 mt-1">
            {formatTime(notification.timestamp)}
          </div>
        </div>
      </div>

      <button
        class="toast-close-btn"
        on:click={() => handleDismiss(notification.id)}
      >
        ✕
      </button>

      <!-- Auto-dismiss progress bar -->
      {#if !notification.persistent && !(notification.type === 'error' && $notificationSettings.persistErrors)}
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-base-content/20">
          <div 
            class="h-full bg-base-content/40 transition-all duration-300"
            style="animation: shrink {notification.type === 'error' ? $notificationSettings.errorHideDelay : $notificationSettings.autoHideDelay}ms linear forwards"
          />
        </div>
      {/if}
    </div>
  {/each}

  <!-- 너무 많은 알림이 있을 때 더보기 표시 -->
  {#if $notifications.length > 5}
    <div class="alert alert-info shadow-lg max-w-sm">
      <div class="flex items-center gap-3">
        <span class="text-lg">📋</span>
        <div class="flex-1">
          <div class="font-semibold text-sm">
            {$notifications.length - 5} more notifications
          </div>
          <div class="text-xs opacity-90">
            Click to view all
          </div>
        </div>
        <button
          class="btn btn-primary btn-xs"
          on:click={() => dispatch('showAll')}
        >
          View All
        </button>
      </div>
    </div>
  {/if}
</div>

<!-- 전체 알림 패널 (옵션) -->
<div class="notification-panel-overlay fixed inset-0 z-40 hidden">
  <div class="absolute inset-0 bg-black/20" role="button" tabindex="0" on:click={() => dispatch('closePanel')} on:keydown={(e) => e.key === 'Enter' && dispatch('closePanel')}></div>

  <div class="notification-panel absolute top-4 right-4 bottom-4 w-96 bg-base-100 rounded-lg shadow-xl border border-base-content/10">
    <div class="panel-header p-4 border-b border-base-content/10">
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">Notifications</h3>
        <div class="flex gap-2">
          {#if hasNotifications}
            <button
              class="btn btn-ghost btn-sm"
              on:click={handleClearAll}
            >
              Clear All
            </button>
          {/if}
          <button
            class="toast-close-btn"
            on:click={() => dispatch('closePanel')}
          >
            ✕
          </button>
        </div>
      </div>

      {#if unreadCount > 0}
        <div class="text-sm text-base-content/70 mt-1">
          {unreadCount} unread notifications
        </div>
      {/if}
    </div>

    <div class="panel-content overflow-y-auto max-h-full p-4 space-y-3">
      {#if hasNotifications}
        {#each $notifications as notification (notification.id)}
          <div
            class="notification-item p-3 rounded-lg border border-base-content/10 relative pr-12"
            class:bg-base-200={!notification.read}
            class:bg-base-100={notification.read}
          >
            <div class="flex items-start gap-3">
              <span class="text-lg flex-shrink-0 {getNotificationStyle(notification.type).textClass}">
                {getNotificationStyle(notification.type).icon}
              </span>

              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm">
                  {notification.title}
                </div>
                {#if notification.message}
                  <div class="text-sm text-base-content/70 mt-1">
                    {notification.message}
                  </div>
                {/if}
                <div class="text-xs text-base-content/50 mt-2">
                  {formatTime(notification.timestamp)}
                </div>
              </div>
            </div>

            <button
              class="toast-close-btn"
              on:click={() => handleDismiss(notification.id)}
            >
              ✕
            </button>
          </div>
        {/each}
      {:else}
        <div class="text-center py-8">
          <div class="text-4xl mb-2">🔔</div>
          <div class="text-base-content/70">No notifications</div>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .toast-container {
    @apply pointer-events-none;
  }

  .toast-container > * {
    @apply pointer-events-auto;
  }

  .notification-panel {
    @apply flex flex-col;
  }

  .panel-content {
    @apply flex-1;
  }

  .notification-item {
    @apply transition-colors;
  }

  .toast-close-btn {
    @apply absolute top-2 right-2 btn btn-ghost btn-xs btn-circle;
  }

  @keyframes shrink {
    from {
      width: 100%;
    }
    to {
      width: 0%;
    }
  }
</style>
