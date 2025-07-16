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
export const isBackgroundLoading = writable<boolean>(false); // 백그라운드 로딩 상태
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
export const autoRefreshInterval = writable<number>(30000); // 30초로 증가

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
export async function refreshSessions(isInitial: boolean = false): Promise<void> {
  // 초기 로딩인지 백그라운드 로딩인지 구분
  if (isInitial) {
    isLoading.set(true);
  } else {
    isBackgroundLoading.set(true);
  }
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

    // 스마트 업데이트: 기존 데이터와 비교하여 변경된 경우만 업데이트
    const currentSessions = get(sessions);
    const hasChanged = isInitial || !currentSessions || currentSessions.length !== processedData.length ||
      currentSessions.some((current, index) => {
        const newSession = processedData[index];
        return !newSession ||
               current.session_name !== newSession.session_name ||
               current.status !== newSession.status ||
               current.controller_status !== newSession.controller_status ||
               current.windows?.length !== newSession.windows?.length;
      });

    if (hasChanged) {
      sessions.set(processedData);
    }

    if (isInitial && processedData.length === 0) {
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
    if (isInitial) {
      isLoading.set(false);
    } else {
      isBackgroundLoading.set(false);
    }
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

/**
 * 프로젝트 기반으로 tmux 세션을 생성합니다.
 */
export async function createTmuxSession(projectName: string): Promise<void> {
  try {
    showNotification('info', 'Creating Session', `Creating session for project: ${projectName}`);
    await pythonBridge.create_session({ project_name: projectName });
    showNotification('success', 'Session Created', `Session for ${projectName} created successfully`);
    setTimeout(refreshSessions, 1500);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to create session: ${errorMessage}`);
    throw err;
  }
}

/**
 * 사용 가능한 프로젝트 목록을 가져옵니다.
 */
export async function getAvailableProjects(): Promise<string[]> {
  try {
    const response = await fetch('/api/config/projects');
    if (!response.ok) {
      throw new Error('Failed to fetch projects');
    }
    return await response.json();
  } catch (err) {
    console.error('Failed to get available projects:', err);
    return [];
  }
}

// 6. setupAllSessions 함수 구현
export async function setupAllSessions(): Promise<void> {
  try {
    showNotification('info', 'Setup Sessions', 'Setting up all sessions from configuration...');

    // Use the dedicated setup-all endpoint
    const response = await fetch('/api/sessions/setup-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (response.status === 404) {
      showNotification('warning', 'No Projects', 'No projects found in projects.yaml configuration.');
      return;
    } else if (response.status === 207) {
      // Multi-status: 일부 성공, 일부 실패
      const errorText = await response.text();
      showNotification('warning', 'Partial Success', errorText);
    } else if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to setup sessions: ${errorText}`);
    } else {
      showNotification('success', 'Setup Complete', 'All sessions have been created successfully.');
    }

    // 세션 목록 새로고침
    setTimeout(refreshSessions, 1500);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Setup Error', `Failed to setup sessions: ${errorMessage}`);
    throw err;
  }
}

export async function teardownAllSessions(): Promise<void> {
  const sessionsToTeardown = get(sessions);
  if (sessionsToTeardown.length === 0) {
    showNotification('info', 'Info', 'No sessions to teardown.');
    return;
  }

  showNotification('info', 'Teardown', `Tearing down ${sessionsToTeardown.length} sessions...`);
  try {
    // Use the dedicated teardown-all endpoint
    const response = await fetch('/api/sessions/teardown-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to teardown sessions: ${errorText}`);
    }

    showNotification('success', 'Success', 'All sessions have been torn down.');
    clearSessionSelection();
    setTimeout(refreshSessions, 1500);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to teardown all sessions: ${errorMessage}`);
    throw err;
  }
}

// 8. start/stopAllControllers 구현 - 새로운 bulk API 사용
export async function startAllControllers(): Promise<void> {
  try {
    showNotification('info', 'Starting All', 'Starting all controllers...');
    
    const response = await fetch('/api/controllers/start-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to start controllers: ${errorText}`);
    }

    const result = await response.json();
    
    if (result.errors && result.errors.length > 0) {
      showNotification('warning', 'Partial Success', 
        `Started ${result.started}/${result.total_sessions} controllers. Errors: ${result.errors.join('; ')}`);
    } else {
      showNotification('success', 'Success', result.message);
    }
    
    setTimeout(refreshSessions, 1000);
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    showNotification('error', 'Error', `Failed to start all controllers: ${errorMessage}`);
    throw err;
  }
}

export async function stopAllControllers(): Promise<void> {
  try {
    showNotification('info', 'Stopping All', 'Stopping all controllers...');
    
    const response = await fetch('/api/controllers/stop-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to stop controllers: ${errorText}`);
    }

    const result = await response.json();
    
    if (result.errors && result.errors.length > 0) {
      showNotification('warning', 'Partial Success', 
        `Stopped ${result.stopped}/${result.total_sessions} controllers. Errors: ${result.errors.join('; ')}`);
    } else {
      showNotification('success', 'Success', result.message);
    }
    
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
