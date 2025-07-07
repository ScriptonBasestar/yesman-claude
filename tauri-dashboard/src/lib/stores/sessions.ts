/**
 * 세션 상태 관리 스토어 (FastAPI 연동)
 */

import { writable, derived, get } from 'svelte/store';
import { pythonBridge } from '$lib/utils/tauri';
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
  sortBy: 'session_name', // Fix: 'name' -> 'session_name'
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
        !!session.controller_error // Fix: check controller_error existence
      );
    }

    // 정렬
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch ($filters.sortBy) {
        case 'session_name': // Fix: 'name' -> 'session_name'
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
  active: $sessions.filter(s => s.status === 'running').length, // Fix: 'active' -> 'running'
  inactive: $sessions.filter(s => s.status === 'stopped').length, // Fix: 'inactive' -> 'stopped'
  runningControllers: $sessions.filter(s => s.controller_status === 'running').length,
  stoppedControllers: $sessions.filter(s => s.controller_status === 'not running').length, // Fix: 'stopped' -> 'not running'
  errorControllers: $sessions.filter(s => !!s.controller_error).length, // Fix: check controller_error existence
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
    // 1. API 함수 이름 변경
    const sessionData = await pythonBridge.get_sessions();
    
    // 데이터 가공 (필요 시)
    const processedData = sessionData.map((s: Session) => ({
      ...s,
      // 2. 누락된 필드 임시 처리
      total_panes: s.windows?.reduce((acc, w) => acc + w.panes.length, 0) || 0,
      description: s.template, // template을 임시로 description으로 사용
    }));

    sessions.set(processedData);
    
    if (get(sessions).length === 0) {
      // Fix: Correct argument order for showNotification
      showNotification('warning', 'No Sessions', 'No tmux sessions found.');
    }
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
    error.set(errorMessage);
    // Fix: Correct argument order
    showNotification('error', 'Error', `Failed to refresh sessions: ${errorMessage}`);
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
    sortBy: 'session_name', // Fix: 'name' -> 'session_name'
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
    // 3. API 함수 변경 및 파라미터 유지 (session_name이 ID로 사용됨)
    await pythonBridge.start_claude(sessionName);
    // Fix: Correct argument order
    showNotification('success', 'Controller Started', `Controller started for ${sessionName}`);
    
    updateSessionControllerStatus(sessionName, 'running');
    setTimeout(refreshSessions, 1000); // 상태 반영을 위해 새로고침
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    // Fix: Correct argument order
    showNotification('error', 'Error', `Failed to start controller: ${errorMessage}`);
    throw err;
  }
}

export async function stopController(sessionName: string): Promise<void> {
  try {
    // 4. API 함수 변경
    await pythonBridge.stop_claude(sessionName);
    // Fix: Correct argument order
    showNotification('success', 'Controller Stopped', `Controller stopped for ${sessionName}`);
    // Fix: Use a valid status type
    updateSessionControllerStatus(sessionName, 'not running');
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    // Fix: Correct argument order
    showNotification('error', 'Error', `Failed to stop controller: ${errorMessage}`);
    throw err;
  }
}

export async function restartController(sessionName: string): Promise<void> {
  try {
    showNotification('info', 'Restarting', `Restarting controller for ${sessionName}...`);
    await pythonBridge.stop_claude(sessionName);
    // 상태 업데이트를 위해 잠시 대기
    await new Promise(resolve => setTimeout(resolve, 2000));
    await pythonBridge.start_claude(sessionName);
    showNotification('success', 'Controller Restarted', `Controller for ${sessionName} has been restarted.`);
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to restart controller: ${errorMessage}`);
    throw err;
  }
}

// 5. setup* 함수들은 UI 수정이 필요하므로 주석 처리
/*
export async function setupTmuxSession(sessionName: string): Promise<void> {
  // TODO: UI에서 session config를 받아 create_session을 호출하도록 변경 필요
  try {
    // await pythonBridge.create_session({ session_name: sessionName, ... });
    showNotification('success', 'Session Created', `Session ${sessionName} created.`);
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to create session: ${errorMessage}`);
    throw err;
  }
}
*/

// 6. setupAllSessions 함수는 제거

export async function teardownAllSessions(): Promise<void> {
  const sessionsToTeardown = get(sessions);
  if (sessionsToTeardown.length === 0) {
    showNotification('info', 'Info', 'No sessions to teardown.');
    return;
  }

  showNotification('info', 'Teardown', `Tearing down ${sessionsToTeardown.length} sessions...`);
  try {
    // 7. 새로운 로직으로 구현
    await Promise.all(sessionsToTeardown.map(s => pythonBridge.delete_session(s.session_name)));
    showNotification('success', 'Success', 'All sessions have been torn down.');
    clearSessionSelection();
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to teardown all sessions: ${errorMessage}`);
    throw err;
  }
}

// 8. start/stopAllControllers 구현
export async function startAllControllers(): Promise<void> {
  const selected = get(selectedSessions);
  const sessionsToStart = selected.length > 0 ? get(sessions).filter(s => selected.includes(s.session_name)) : get(sessions);

  if (sessionsToStart.length === 0) {
    showNotification('info', 'Info', 'No sessions selected to start controllers.');
    return;
  }

  showNotification('info', 'Starting All', `Starting controllers for ${sessionsToStart.length} sessions...`);
  try {
    await Promise.all(sessionsToStart.map(s => pythonBridge.start_claude(s.session_name)));
    showNotification('success', 'Success', 'All selected controllers started.');
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to start all controllers: ${errorMessage}`);
    throw err;
  }
}

export async function stopAllControllers(): Promise<void> {
    const selected = get(selectedSessions);
    const sessionsToStop = selected.length > 0 ? get(sessions).filter(s => selected.includes(s.session_name)) : get(sessions);
  
    if (sessionsToStop.length === 0) {
      showNotification('info', 'Info', 'No sessions selected to stop controllers.');
      return;
    }
  
    showNotification('info', 'Stopping All', `Stopping controllers for ${sessionsToStop.length} sessions...`);
    try {
      await Promise.all(sessionsToStop.map(s => pythonBridge.stop_claude(s.session_name)));
      showNotification('success', 'Success', 'All selected controllers stopped.');
      setTimeout(refreshSessions, 1000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      showNotification('error', 'Error', `Failed to stop all controllers: ${errorMessage}`);
      throw err;
    }
}

/**
 * 내부적으로 세션의 컨트롤러 상태를 업데이트합니다.
 * @param sessionName - 세션 이름
 * @param status - 새로운 컨트롤러 상태
 */
function updateSessionControllerStatus(sessionName: string, status: 'running' | 'not running' | 'unknown'): void {
  sessions.update(current => 
    current.map(s => 
      s.session_name === sessionName 
        ? { ...s, controller_status: status } 
        : s
    )
  );
}

/**
 * 컨트롤러 상태 업데이트 (외부 사용용)
 */
export function updateControllerStatus(sessionName: string, status?: string): void {
  if (status) {
    updateSessionControllerStatus(sessionName, status as 'running' | 'not running' | 'unknown');
  } else {
    // status가 없으면 해당 세션의 상태를 새로고침
    refreshSessions();
  }
}

// 9. 이벤트 리스너는 현재 아키텍처에서 불필요하므로 주석 처리
/*
export function setupEventListeners(): void {
    // ...
}
*/

// 10. 로그 관련 함수 수정
export async function viewSessionLogs(sessionName: string): Promise<void> {
    try {
        const logs = await pythonBridge.get_logs(sessionName, false, 200);
        // TODO: 받은 로그를 보여주는 UI 로직 필요 (예: 모달)
        console.log(`Logs for ${sessionName}:`, logs);
        showNotification('info', 'Logs Fetched', `Check console for logs of ${sessionName}.`);
    } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        showNotification('error', 'Error', `Failed to get logs: ${errorMessage}`);
    }
}

export async function getSessionLogs(sessionName: string): Promise<string[]> {
  try {
    return await pythonBridge.get_logs(sessionName, false, 500);
  } catch (err) {
    console.error(`Failed to get logs for ${sessionName}:`, err);
    return [];
  }
}

// 스토어 초기화 시 이벤트 리스너 설정 (브라우저 환경에서만)
if (typeof window !== 'undefined') {
  // setupEventListeners(); // 이벤트 리스너는 현재 아키텍처에서 불필요하므로 주석 처리
}