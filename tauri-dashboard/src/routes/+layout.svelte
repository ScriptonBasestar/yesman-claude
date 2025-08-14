<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { listen } from '@tauri-apps/api/event';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import Header from '$lib/components/layout/Header.svelte';
  import NotificationContainer from '$lib/components/common/NotificationContainer.svelte';
  import { loadConfig } from '$lib/stores/config';
  import { refreshSessions, startAutoRefresh, stopAutoRefresh, getAvailableProjects } from '$lib/stores/sessions';
  import { showNotification, notifySuccess, notifyError, notifyWarning } from '$lib/stores/notifications';
  import { health } from '$lib/stores/health';

  let isMinimized = false;
  let currentRoute: string | null = null;

  // 연결 가능 상태 판단 헬퍼
  function isServiceReachable(status: 'healthy' | 'warning' | 'error' | 'unknown'): boolean {
    return status === 'healthy' || status === 'warning';
  }

  onMount(() => {
    let unlistenSessionUpdate: (() => void) | undefined;
    let unlistenLogUpdate: (() => void) | undefined;
    let unlistenNotification: (() => void) | undefined;
    let unsubscribeHealthStore: (() => void) | undefined;

    // 최근 상태를 추적하여 재연결 알림/초기화 제어
    let lastStatus: 'healthy' | 'warning' | 'error' | 'unknown' = 'unknown';
    let initializedAfterHealthy = false; // healthy/ warning 전환 후 초기화 수행 여부

    // 초기화 실행 함수 (중복 방지)
    const runInitialization = async (isFirst: boolean) => {
      if (initializedAfterHealthy) return;
      try {
        await loadConfig();
        await refreshSessions(isFirst);
        void getAvailableProjects(); // 프로젝트 목록도 미리 로드
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Unknown error';
        notifyError('Initialization Failed', `Failed to load initial data: ${msg}`);
      }
      startAutoRefresh();
      initializedAfterHealthy = true;
    };

    // 헬스 모니터링 시작: 연결 가능 상태일 때 초기 로딩/자동 새로고침 시작
    health.startChecking({
      interval: 30000,
      onStatusChange: (status) => {
        if (status === 'error') {
          stopAutoRefresh();
          notifyWarning('API Disconnected', 'Unable to connect to backend server. Please check if the API server is running.');
        } else if (isServiceReachable(status)) {
          const isReconnected = lastStatus === 'unknown' || lastStatus === 'error';
          if (isReconnected) {
            notifySuccess('API Connected', 'Successfully connected to backend server.');
          }
          void runInitialization(!initializedAfterHealthy);
        }
        lastStatus = status;
      }
    });

    // 즉시 1회 헬스 체크 후 연결 가능하면 초기화 실행 (타이밍 이슈 대비)
    (async () => {
      await health.check();
      if (!initializedAfterHealthy) {
        let currentOverall: 'healthy' | 'warning' | 'error' | 'unknown' = 'unknown';
        const tmpUnsub = health.subscribe(($h) => { currentOverall = $h.overall; });
        tmpUnsub();
        if (isServiceReachable(currentOverall)) {
          void runInitialization(true);
        }
      }
    })();

    // 헬스 상태 구독: 콜백 타이밍을 놓쳐도 연결 가능해지면 초기화
    unsubscribeHealthStore = health.subscribe(($h) => {
      if (isServiceReachable($h.overall) && !initializedAfterHealthy) {
        void runInitialization(true);
      }
    });

    // 실시간 이벤트 리스너 설정 (Tauri 환경에서만)
    (async () => {
      try {
        unlistenSessionUpdate = await listen('session-update', (event) => {
          const { session, status, controller_status } = event.payload as any;
          void session; void status; void controller_status;
          refreshSessions();
        });

        unlistenLogUpdate = await listen('log-update', (event) => {
          const { session, log, timestamp } = event.payload as any;
          void session; void log; void timestamp;
        });

        unlistenNotification = await listen('notification', (event) => {
          const { title, message, level } = event.payload as any;
          showNotification(level, title, message, false);
        });
      } catch (error) {
        // 웹 환경에서는 이벤트 리스너가 동작하지 않을 수 있음
      }
    })();

    // cleanup 반환
    return () => {
      health.stopChecking();
      stopAutoRefresh();
      if (unsubscribeHealthStore) unsubscribeHealthStore();
      if (unlistenSessionUpdate) unlistenSessionUpdate();
      if (unlistenLogUpdate) unlistenLogUpdate();
      if (unlistenNotification) unlistenNotification();
    };
  });

  // 페이지 변경 감지
  $: currentRoute = $page.route.id;

  async function handleQuickAction(event: CustomEvent) {
    const { action } = event.detail;

    switch (action) {
      case 'refresh':
        refreshSessions();
        notifySuccess('Refreshed', 'Session data refreshed');
        break;
      case 'setup':
        try {
          const { setupAllSessions } = await import('$lib/stores/sessions');
          await setupAllSessions();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Setup Failed', `Failed to setup sessions: ${errorMessage}`);
        }
        break;
      case 'teardown':
        try {
          const { teardownAllSessions } = await import('$lib/stores/sessions');
          await teardownAllSessions();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Teardown Failed', `Failed to teardown sessions: ${errorMessage}`);
        }
        break;
      case 'start_all':
        try {
          const { startAllControllers } = await import('$lib/stores/sessions');
          await startAllControllers();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Start Failed', `Failed to start all controllers: ${errorMessage}`);
        }
        break;
      case 'stop_all':
        try {
          const { stopAllControllers } = await import('$lib/stores/sessions');
          await stopAllControllers();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          notifyError('Stop Failed', `Failed to stop all controllers: ${errorMessage}`);
        }
        break;
    }
  }
</script>

<div class="app-layout h-screen flex">
  <!-- 사이드바 -->
  <div class="sidebar-container" class:minimized={isMinimized}>
    <Sidebar {currentRoute} bind:isMinimized on:quickAction={handleQuickAction} />
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
