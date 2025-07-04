/**
 * 세션 상태 관리 스토어 (Tauri 연동)
 */

import { writable, derived, get } from 'svelte/store';
import { pythonBridge, eventListeners, tauriUtils } from '$lib/utils/tauri';
import { showNotification } from './notifications';
import type { Session, SessionFilters } from '$lib/types/session';

// 세션 데이터 스토어
export const sessions = writable<Session[]>([]);
export const isLoading = writable<boolean>(false);
export const error = writable<string | null>(null);

// 필터 상태
export const sessionFilters = writable<SessionFilters>({
  search: '',
  status: '',
  controllerStatus: '',
  sortBy: 'name',
  sortOrder: 'asc',
  showOnlyErrors: false
});

// 자동 새로고침 설정
export const autoRefreshEnabled = writable<boolean>(true);
export const autoRefreshInterval = writable<number>(10000); // 10초

// 선택된 세션들
export const selectedSessions = writable<string[]>([]);

// 필터링된 세션 목록 (파생 스토어)
export const filteredSessions = derived(
  [sessions, sessionFilters],
  ([$sessions, $filters]) => {
    let filtered = [...$sessions];

    // 검색 필터
    if ($filters.search) {
      const searchLower = $filters.search.toLowerCase();
      filtered = filtered.filter(session =>
        session.session_name.toLowerCase().includes(searchLower) ||
        session.project_name?.toLowerCase().includes(searchLower) ||
        session.description?.toLowerCase().includes(searchLower)
      );
    }

    // 상태 필터
    if ($filters.status) {
      filtered = filtered.filter(session => session.status === $filters.status);
    }

    // 컨트롤러 상태 필터
    if ($filters.controllerStatus) {
      filtered = filtered.filter(session => session.controller_status === $filters.controllerStatus);
    }

    // 에러만 표시
    if ($filters.showOnlyErrors) {
      filtered = filtered.filter(session => 
        session.controller_status === 'error' || 
        session.controller_error !== null
      );
    }

    // 정렬
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch ($filters.sortBy) {
        case 'name':
          aValue = a.session_name;
          bValue = b.session_name;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'uptime':
          aValue = a.uptime || '';
          bValue = b.uptime || '';
          break;
        case 'last_activity':
          aValue = a.last_activity_timestamp || 0;
          bValue = b.last_activity_timestamp || 0;
          break;
        default:
          aValue = a.session_name;
          bValue = b.session_name;
      }

      if (typeof aValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return $filters.sortOrder === 'asc' ? comparison : -comparison;
      } else {
        const comparison = aValue - bValue;
        return $filters.sortOrder === 'asc' ? comparison : -comparison;
      }
    });

    return filtered;
  }
);

// 세션 통계 (파생 스토어)
export const sessionStats = derived(sessions, ($sessions) => ({
  total: $sessions.length,
  active: $sessions.filter(s => s.status === 'active').length,
  inactive: $sessions.filter(s => s.status === 'inactive').length,
  runningControllers: $sessions.filter(s => s.controller_status === 'running').length,
  stoppedControllers: $sessions.filter(s => s.controller_status === 'stopped').length,
  errorControllers: $sessions.filter(s => s.controller_status === 'error').length,
  totalWindows: $sessions.reduce((sum, s) => sum + (s.windows?.length || 0), 0),
  totalPanes: $sessions.reduce((sum, s) => sum + (s.total_panes || 0), 0)
}));

// 자동 새로고침 인터벌 ID
let refreshIntervalId: number | null = null;

/**
 * 세션 데이터 새로고침
 */
export async function refreshSessions(): Promise<void> {
  isLoading.set(true);
  error.set(null);

  try {
    const sessionData = await pythonBridge.getAllSessions();
    sessions.set(sessionData);
    
    // 성공 알림 (선택적)
    if (get(sessions).length === 0) {
      showNotification('No Sessions', 'No tmux sessions found. Run setup to create sessions.', 'warning');
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
    error.set(errorMessage);
    showNotification('Error', `Failed to refresh sessions: ${errorMessage}`, 'error');
    console.error('Failed to refresh sessions:', err);
  } finally {
    isLoading.set(false);
  }
}

/**
 * 자동 새로고침 시작
 */
export function startAutoRefresh(): void {
  stopAutoRefresh(); // 기존 인터벌 정리
  
  const interval = get(autoRefreshInterval);
  if (get(autoRefreshEnabled) && interval > 0) {
    refreshIntervalId = setInterval(refreshSessions, interval) as unknown as number;
    console.log('Auto-refresh started with interval:', interval);
  }
}

/**
 * 자동 새로고침 중지
 */
export function stopAutoRefresh(): void {
  if (refreshIntervalId !== null) {
    clearInterval(refreshIntervalId);
    refreshIntervalId = null;
    console.log('Auto-refresh stopped');
  }
}

/**
 * 자동 새로고침 설정 변경
 */
export function configureAutoRefresh(enabled: boolean, interval?: number): void {
  autoRefreshEnabled.set(enabled);
  if (interval !== undefined) {
    autoRefreshInterval.set(interval);
  }
  
  if (enabled) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
}

/**
 * 필터 업데이트
 */
export function updateFilters(newFilters: Partial<SessionFilters>): void {
  sessionFilters.update(current => ({ ...current, ...newFilters }));
}

/**
 * 필터 초기화
 */
export function resetFilters(): void {
  sessionFilters.set({
    search: '',
    status: '',
    controllerStatus: '',
    sortBy: 'name',
    sortOrder: 'asc',
    showOnlyErrors: false
  });
}

/**
 * 세션 선택 관리
 */
export function toggleSessionSelection(sessionName: string): void {
  selectedSessions.update(selected => {
    if (selected.includes(sessionName)) {
      return selected.filter(name => name !== sessionName);
    } else {
      return [...selected, sessionName];
    }
  });
}

export function selectAllSessions(): void {
  const allSessionNames = get(filteredSessions).map(s => s.session_name);
  selectedSessions.set(allSessionNames);
}

export function clearSessionSelection(): void {
  selectedSessions.set([]);
}

/**
 * 컨트롤러 액션들
 */
export async function startController(sessionName: string): Promise<void> {
  try {
    await pythonBridge.startController(sessionName);
    showNotification('Controller Started', `Controller started for ${sessionName}`, 'success');
    
    // 세션 상태 업데이트
    updateSessionControllerStatus(sessionName, 'running');
    
    // 데이터 새로고침
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('Error', `Failed to start controller: ${errorMessage}`, 'error');
    throw err;
  }
}

export async function stopController(sessionName: string): Promise<void> {
  try {
    await pythonBridge.stopController(sessionName);
    showNotification('Controller Stopped', `Controller stopped for ${sessionName}`, 'success');
    
    // 세션 상태 업데이트
    updateSessionControllerStatus(sessionName, 'stopped');
    
    // 데이터 새로고침
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('Error', `Failed to stop controller: ${errorMessage}`, 'error');
    throw err;
  }
}

export async function restartController(sessionName: string): Promise<void> {
  try {
    await stopController(sessionName);
    await new Promise(resolve => setTimeout(resolve, 2000)); // 2초 대기
    await startController(sessionName);
  } catch (err) {
    showNotification('Error', 'Failed to restart controller', 'error');
    throw err;
  }
}

/**
 * 세션 액션들
 */
export async function setupTmuxSession(sessionName: string): Promise<void> {
  try {
    await pythonBridge.setupTmuxSession(sessionName);
    showNotification('Session Created', `Tmux session ${sessionName} created`, 'success');
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('Error', `Failed to setup session: ${errorMessage}`, 'error');
    throw err;
  }
}

export async function setupAllSessions(): Promise<void> {
  try {
    await pythonBridge.setupAllSessions();
    showNotification('All Sessions Created', 'All tmux sessions have been created', 'success');
    setTimeout(refreshSessions, 2000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('Error', `Failed to setup all sessions: ${errorMessage}`, 'error');
    throw err;
  }
}

export async function teardownAllSessions(): Promise<void> {
  try {
    await pythonBridge.teardownAllSessions();
    showNotification('All Sessions Destroyed', 'All tmux sessions have been destroyed', 'success');
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('Error', `Failed to teardown all sessions: ${errorMessage}`, 'error');
    throw err;
  }
}

/**
 * 배치 작업들
 */
export async function startAllControllers(): Promise<void> {
  const stoppedSessions = get(sessions).filter(s => s.controller_status === 'stopped');
  
  if (stoppedSessions.length === 0) {
    showNotification('Info', 'No stopped controllers to start', 'info');
    return;
  }

  const results = await Promise.allSettled(
    stoppedSessions.map(session => startController(session.session_name))
  );

  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;

  if (failed === 0) {
    showNotification('Success', `Started ${successful} controllers`, 'success');
  } else {
    showNotification('Partial Success', `Started ${successful} controllers, ${failed} failed`, 'warning');
  }
}

export async function stopAllControllers(): Promise<void> {
  const runningSessions = get(sessions).filter(s => s.controller_status === 'running');
  
  if (runningSessions.length === 0) {
    showNotification('Info', 'No running controllers to stop', 'info');
    return;
  }

  const results = await Promise.allSettled(
    runningSessions.map(session => stopController(session.session_name))
  );

  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;

  if (failed === 0) {
    showNotification('Success', `Stopped ${successful} controllers`, 'success');
  } else {
    showNotification('Partial Success', `Stopped ${successful} controllers, ${failed} failed`, 'warning');
  }
}

/**
 * 내부 유틸리티 함수들
 */
function updateSessionControllerStatus(sessionName: string, status: string): void {
  sessions.update(currentSessions =>
    currentSessions.map(session =>
      session.session_name === sessionName
        ? { ...session, controller_status: status }
        : session
    )
  );
}

/**
 * 컨트롤러 상태 업데이트 (외부 사용용)
 */
export function updateControllerStatus(sessionName: string, status?: string): void {
  if (status) {
    updateSessionControllerStatus(sessionName, status);
  } else {
    // status가 없으면 해당 세션의 상태를 새로고침
    refreshSessions();
  }
}

/**
 * 이벤트 리스너 설정
 */
export function setupEventListeners(): void {
  // 브라우저 환경 체크
  if (typeof window === 'undefined') {
    return;
  }

  // 세션 상태 변경 이벤트
  eventListeners.onSessionStatusChanged((sessionName, status) => {
    sessions.update(currentSessions =>
      currentSessions.map(session =>
        session.session_name === sessionName
          ? { ...session, status }
          : session
      )
    );
  });

  // 컨트롤러 상태 변경 이벤트
  eventListeners.onControllerStatusChanged((sessionName, status) => {
    updateSessionControllerStatus(sessionName, status);
  });

  // 에러 이벤트
  eventListeners.onError((errorMessage) => {
    error.set(errorMessage);
    showNotification('System Error', errorMessage, 'error');
  });
}

/**
 * 로그 관련 함수들
 */
export async function viewSessionLogs(sessionName: string): Promise<void> {
  try {
    await tauriUtils.openLogFile(sessionName);
  } catch (err) {
    showNotification('Error', 'Failed to open log file', 'error');
    throw err;
  }
}

export async function getSessionLogs(sessionName: string): Promise<string[]> {
  try {
    return await pythonBridge.getSessionLogs(sessionName);
  } catch (err) {
    showNotification('Error', 'Failed to get session logs', 'error');
    throw err;
  }
}

// 스토어 초기화 시 이벤트 리스너 설정 (브라우저 환경에서만)
if (typeof window !== 'undefined') {
  setupEventListeners();
}