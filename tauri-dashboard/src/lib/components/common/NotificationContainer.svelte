<script lang="ts">
  import { notifications, dismissNotification, clearAllNotifications } from '$lib/stores/notifications';
  import { fade, fly } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';

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
</script>

<!-- 토스트 알림 컨테이너 (우측 상단) -->
<div class="toast-container fixed top-4 right-4 z-50 space-y-2">
  {#each $notifications.slice(0, 5) as notification (notification.id)}
    <div
      class="alert {getNotificationStyle(notification.type).class} shadow-lg max-w-sm"
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

        <button
          class="btn btn-ghost btn-xs"
          on:click={() => handleDismiss(notification.id)}
        >
          ✕
        </button>
      </div>
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
            class="btn btn-ghost btn-sm"
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
            class="notification-item p-3 rounded-lg border border-base-content/10"
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

              <button
                class="btn btn-ghost btn-xs"
                on:click={() => handleDismiss(notification.id)}
              >
                ✕
              </button>
            </div>
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
</style>
