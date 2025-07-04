<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { listen } from '@tauri-apps/api/event';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import Header from '$lib/components/layout/Header.svelte';
  import NotificationContainer from '$lib/components/common/NotificationContainer.svelte';
  import { loadConfig } from '$lib/stores/config';
  import { refreshSessions, startAutoRefresh, stopAutoRefresh } from '$lib/stores/sessions';
  import { showNotification } from '$lib/stores/notifications';

  let isMinimized = false;

  onMount(async () => {
    // 초기 데이터 로드
    await loadConfig();
    await refreshSessions();
    
    // 자동 새로고침 시작
    startAutoRefresh();
    
    // 실시간 이벤트 리스너 설정
    const unlistenSessionUpdate = await listen('session-update', (event) => {
      const { session, status, controller_status } = event.payload as any;
      // 세션 상태 업데이트 처리
      refreshSessions();
    });
    
    const unlistenLogUpdate = await listen('log-update', (event) => {
      const { session, log, timestamp } = event.payload as any;
      // 로그 업데이트 처리 (필요시)
      console.log(`[${session}] ${log}`);
    });
    
    const unlistenNotification = await listen('notification', (event) => {
      const { title, message, level } = event.payload as any;
      showNotification(level, title, message, false); // 시스템 알림은 이미 표시됨
    });
    
    // 컴포넌트 언마운트 시 정리
    return () => {
      stopAutoRefresh();
      unlistenSessionUpdate();
      unlistenLogUpdate();
      unlistenNotification();
    };
  });
  
  // 페이지 변경 감지
  $: currentRoute = $page.route.id;
</script>

<div class="app-layout h-screen flex">
  <!-- 사이드바 -->
  <div class="sidebar-container" class:minimized={isMinimized}>
    <Sidebar {currentRoute} bind:isMinimized />
  </div>
  
  <!-- 메인 컨텐츠 영역 -->
  <div class="main-content flex-1 flex flex-col min-w-0">
    <!-- 헤더 -->
    <Header />
    
    <!-- 페이지 컨텐츠 -->
    <main class="flex-1 overflow-auto">
      <slot />
    </main>
  </div>
  
  <!-- 알림 컨테이너 -->
  <NotificationContainer />
</div>

<style>
  .sidebar-container {
    @apply w-64 transition-all duration-300;
  }
  
  .sidebar-container.minimized {
    @apply w-16;
  }
  
  .main-content {
    min-width: 0; /* flex item이 축소될 수 있도록 */
  }
</style>