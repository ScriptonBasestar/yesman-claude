/**
 * Tauri API 통합 유틸리티
 * Python 브리지와 Tauri 이벤트 시스템을 연결
 */

import { invoke } from '@tauri-apps/api/tauri';
import { open } from '@tauri-apps/api/dialog';
import { sendNotification } from '@tauri-apps/api/notification';
import { listen } from '@tauri-apps/api/event';

// Tauri 환경인지 확인하기 위한 변수입니다.
// 웹 브라우저 환경에서는 window.__TAURI__가 undefined입니다.
// @ts-ignore
const isTauri = typeof window !== 'undefined' && window.__TAURI__ !== undefined;

const API_BASE_URL = 'http://localhost:8080/api';

/**
 * FastAPI 서버에 API 요청을 보내는 헬퍼 함수
 * @param endpoint API 엔드포인트 경로 (e.g., '/sessions')
 * @param options fetch 함수의 옵션 객체
 * @returns API 응답을 JSON 형태로 파싱한 결과
 */
async function fetchApi(endpoint: string, options: RequestInit = {}) {
	try {
		const response = await fetch(`${API_BASE_URL}${endpoint}`, {
			...options,
			headers: {
				'Content-Type': 'application/json',
				...options.headers
			}
		});
		if (!response.ok) {
			const errorData = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(`API Error: ${errorData.detail || 'Unknown error'}`);
		}
		if (response.status === 204) {
			return null;
		}
		return await response.json();
	} catch (e) {
		console.error(`Failed to fetch API endpoint ${endpoint}:`, e);
		throw e;
	}
}

export const pythonBridge = {
	// Session Management - 올바른 API 엔드포인트로 수정
	get_sessions: () => fetchApi('/dashboard/sessions'),
	get_session_details: (sessionId: string) => fetchApi(`/sessions/${sessionId}`),
	create_session: (config: any) =>
		fetchApi(`/sessions/${config.project_name}/setup`, {
			method: 'POST',
			body: JSON.stringify(config)
		}),
	delete_session: (sessionId: string) => fetchApi(`/sessions/${sessionId}`, { method: 'DELETE' }),

	// Controller Management - 올바른 API 엔드포인트로 수정
	start_claude: (sessionId: string) =>
		fetchApi(`/sessions/${sessionId}/controller/start`, {
			method: 'POST'
		}),
	stop_claude: (sessionId: string) =>
		fetchApi(`/sessions/${sessionId}/controller/stop`, {
			method: 'POST'
		}),
	get_claude_status: (sessionId: string) =>
		fetchApi(`/sessions/${sessionId}/controller/status`),

	restart_claude: (sessionId: string) =>
		fetchApi(`/sessions/${sessionId}/controller/restart`, {
			method: 'POST'
		}),

	// Config Management
	get_app_config: () => fetchApi('/config'),
	save_app_config: (config: any) =>
		fetchApi('/config', {
			method: 'POST',
			body: JSON.stringify(config)
		}),

	// Logs - 올바른 API 엔드포인트로 수정
	get_logs: (sessionId: string, follow = false, lines = 50) =>
		fetchApi(`/sessions/${sessionId}/logs?follow=${follow}&lines=${lines}`),

	// Tauri-specific functions
	send_notification: async (message: string) => {
		if (isTauri) {
			return sendNotification({ title: 'Yesman', body: message });
		}
		console.log(`Notification (web): ${message}`);
		return Promise.resolve();
	},

	select_directory: async () => {
		if (isTauri) {
			const result = await open({ directory: true });
			return Array.isArray(result) ? result[0] : result;
		}
		alert('폴더 선택 기능은 데스크톱 앱에서만 사용할 수 있습니다.');
		return Promise.resolve(null);
	},

	// Deprecated functions
	get_session_info: () => {
		console.warn('get_session_info is deprecated. Use get_sessions instead.');
		return fetchApi('/sessions');
	},
	get_project_name: async () => {
		console.warn('get_project_name is deprecated. Use get_app_config instead.');
		try {
			const config = await fetchApi('/config');
			return config?.project_name || 'Unknown Project';
		} catch (error) {
			return 'Unknown Project';
		}
	}
};

// 이벤트 리스너 설정
export const eventListeners = {
  /**
   * 세션 상태 변경 이벤트 리스너
   */
  onSessionStatusChanged(callback: (sessionName: string, status: string) => void) {
    return listen('session-status-changed', (event) => {
      const { sessionName, status } = event.payload as any;
      callback(sessionName, status);
    });
  },

  /**
   * 컨트롤러 상태 변경 이벤트 리스너  
   */
  onControllerStatusChanged(callback: (sessionName: string, status: string) => void) {
    return listen('controller-status-changed', (event) => {
      const { sessionName, status } = event.payload as any;
      callback(sessionName, status);
    });
  },

  /**
   * 알림 이벤트 리스너
   */
  onNotification(callback: (notification: Notification) => void) {
    return listen('notification', (event) => {
      const notification = event.payload as Notification;
      callback(notification);
    });
  },

  /**
   * 에러 이벤트 리스너
   */
  onError(callback: (error: string) => void) {
    return listen('error', (event) => {
      const { message } = event.payload as any;
      callback(message);
    });
  },

  /**
   * 메트릭 업데이트 이벤트 리스너
   */
  onMetricsUpdate(callback: (metrics: any) => void) {
    return listen('metrics-update', (event) => {
      const metrics = event.payload as any;
      callback(metrics);
    });
  }
};

// 유틸리티 함수들
export const tauriUtils = {
  /**
   * 알림 발송
   */
  async sendNotification(title: string, body: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') {
    try {
      await invoke('send_notification', { title, body, type });
    } catch (error) {
      console.error('Failed to send notification:', error);
    }
  },

  /**
   * 애플리케이션 최소화
   */
  async minimizeWindow() {
    try {
      await invoke('minimize_window');
    } catch (error) {
      console.error('Failed to minimize window:', error);
    }
  },

  /**
   * 애플리케이션 최대화
   */
  async maximizeWindow() {
    try {
      await invoke('maximize_window');
    } catch (error) {
      console.error('Failed to maximize window:', error);
    }
  },

  /**
   * 시스템 트레이 표시/숨김
   */
  async toggleSystemTray() {
    try {
      await invoke('toggle_system_tray');
    } catch (error) {
      console.error('Failed to toggle system tray:', error);
    }
  },

  /**
   * 로그 파일 열기
   */
  async openLogFile(sessionName?: string) {
    try {
      await invoke('open_log_file', { sessionName });
    } catch (error) {
      console.error('Failed to open log file:', error);
    }
  },

  /**
   * 설정 파일 열기
   */
  async openConfigFile() {
    try {
      await invoke('open_config_file');
    } catch (error) {
      console.error('Failed to open config file:', error);
    }
  },

  /**
   * 설정 로드
   */
  async loadConfig() {
    try {
      if (isTauri) {
        return await invoke('load_config');
      } else {
        // 웹 환경에서는 localStorage에서 로드
        const saved = localStorage.getItem('yesman-config');
        return saved ? JSON.parse(saved) : null;
      }
    } catch (error) {
      console.error('Failed to load config:', error);
      return null;
    }
  },

  /**
   * 설정 저장
   */
  async saveConfig(config: any) {
    try {
      if (isTauri) {
        await invoke('save_config', { config });
      } else {
        // 웹 환경에서는 localStorage에 저장
        localStorage.setItem('yesman-config', JSON.stringify(config));
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      throw error;
    }
  }
};

// 에러 처리 유틸리티
export class TauriError extends Error {
  constructor(
    message: string,
    public code?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'TauriError';
  }
}

/**
 * Tauri 명령 실행 래퍼 (에러 처리 포함)
 */
export async function safeTauriInvoke<T>(
  command: string,
  args?: Record<string, any>
): Promise<T> {
  try {
    const result = await invoke(command, args);
    return result as T;
  } catch (error) {
    console.error(`Tauri command '${command}' failed:`, error);
    throw new TauriError(
      `Failed to execute command '${command}': ${error}`,
      'TAURI_COMMAND_FAILED',
      { command, args, originalError: error }
    );
  }
}

/**
 * 배치 명령 실행 (여러 명령을 순차적으로 실행)
 */
export async function executeBatchCommands(
  commands: Array<{ command: string; args?: Record<string, any> }>
): Promise<any[]> {
  const results = [];
  
  for (const { command, args } of commands) {
    try {
      const result = await safeTauriInvoke(command, args);
      results.push({ success: true, result });
    } catch (error) {
      results.push({ success: false, error: error.message });
    }
  }
  
  return results;
}

// 자동 재시도 로직
export async function retryTauriCommand<T>(
  command: string,
  args?: Record<string, any>,
  maxRetries: number = 3,
  delayMs: number = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await safeTauriInvoke<T>(command, args);
    } catch (error) {
      lastError = error as Error;
      
      if (attempt < maxRetries) {
        console.warn(`Command '${command}' failed (attempt ${attempt}/${maxRetries}), retrying in ${delayMs}ms...`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
        delayMs *= 2; // 지수 백오프
      }
    }
  }
  
  throw lastError!;
}