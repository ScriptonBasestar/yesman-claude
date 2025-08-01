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
const isTauri = typeof window !== 'undefined' &&
  window.__TAURI__ !== undefined &&
  window.__TAURI_IPC__ !== undefined;

// Import centralized API client
import { api } from './api';

export const pythonBridge = {
	// Session Management - Use centralized API client
	get_sessions: async () => {
		const response = await api.getSessions();
		return { sessions: response.data || [] };
	},
	get_session_details: (sessionId: string) => api.getSession(sessionId),
	create_session: (config: any) => api.createSession(config),
	delete_session: (sessionId: string) => api.deleteSession(sessionId),

	// Controller Management - Use centralized API client
	start_claude: (sessionId: string) => api.post(`/controllers/${sessionId}/start`, {}),
	stop_claude: (sessionId: string) => api.post(`/controllers/${sessionId}/stop`, {}),
	get_claude_status: (sessionId: string) => api.get(`/controllers/${sessionId}/status`),
	restart_claude: (sessionId: string) => api.post(`/controllers/${sessionId}/restart`, {}),

	// Config Management
	get_app_config: () => api.get('/config'),
	save_app_config: (config: any) => api.post('/config', config),

	// Logs
	get_logs: (sessionId: string, follow = false, lines = 50) => 
		api.getLogs(lines),

	// Tauri-specific functions
	send_notification: async (message: string) => {
		if (isTauri) {
			try {
				return await sendNotification({ title: 'Yesman', body: message });
			} catch (error) {
				console.warn('Failed to send Tauri notification, falling back to console:', error);
				console.log(`Notification (fallback): ${message}`);
			}
		} else {
			console.log(`Notification (web): ${message}`);
		}
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
		return api.dashboard.sessions();
	},
	get_project_name: async () => {
		console.warn('get_project_name is deprecated. Use get_app_config instead.');
		try {
			const config = await api.config.get();
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
    if (!isTauri) {
      console.warn('Event listeners are only available in Tauri environment');
      return () => {}; // 웹 환경에서는 빈 함수 반환
    }
    return listen('session-status-changed', (event) => {
      const { sessionName, status } = event.payload as any;
      callback(sessionName, status);
    });
  },

  /**
   * 컨트롤러 상태 변경 이벤트 리스너
   */
  onControllerStatusChanged(callback: (sessionName: string, status: string) => void) {
    if (!isTauri) {
      console.warn('Event listeners are only available in Tauri environment');
      return () => {};
    }
    return listen('controller-status-changed', (event) => {
      const { sessionName, status } = event.payload as any;
      callback(sessionName, status);
    });
  },

  /**
   * 알림 이벤트 리스너
   */
  onNotification(callback: (notification: Notification) => void) {
    if (!isTauri) {
      console.warn('Event listeners are only available in Tauri environment');
      return () => {};
    }
    return listen('notification', (event) => {
      const notification = event.payload as Notification;
      callback(notification);
    });
  },

  /**
   * 에러 이벤트 리스너
   */
  onError(callback: (error: string) => void) {
    if (!isTauri) {
      console.warn('Event listeners are only available in Tauri environment');
      return () => {};
    }
    return listen('error', (event) => {
      const { message } = event.payload as any;
      callback(message);
    });
  },

  /**
   * 메트릭 업데이트 이벤트 리스너
   */
  onMetricsUpdate(callback: (metrics: any) => void) {
    if (!isTauri) {
      console.warn('Event listeners are only available in Tauri environment');
      return () => {};
    }
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
    if (!isTauri) {
      console.log(`[Web Notification] ${title}: ${body} (${type})`);
      return;
    }
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
    if (!isTauri) {
      console.warn('Window controls are only available in Tauri environment');
      return;
    }
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
    if (!isTauri) {
      console.warn('Window controls are only available in Tauri environment');
      return;
    }
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
    if (!isTauri) {
      console.warn('System tray is only available in Tauri environment');
      return;
    }
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
    if (!isTauri) {
      console.warn('File operations are only available in Tauri environment');
      return;
    }
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
    if (!isTauri) {
      console.warn('File operations are only available in Tauri environment');
      return;
    }
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
  if (!isTauri) {
    console.warn(`Tauri command '${command}' is only available in Tauri environment`);
    throw new TauriError(
      `Command '${command}' is not available in web environment`,
      'NOT_TAURI_ENVIRONMENT',
      { command, args }
    );
  }
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
  if (!isTauri) {
    console.warn('Batch commands are only available in Tauri environment');
    return commands.map(() => ({ success: false, error: 'Not available in web environment' }));
  }

  const results = [];

  for (const { command, args } of commands) {
    try {
      const result = await safeTauriInvoke(command, args);
      results.push({ success: true, result });
    } catch (error) {
      results.push({ success: false, error: error instanceof Error ? error.message : String(error) });
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
  if (!isTauri) {
    throw new TauriError(
      `Retry command '${command}' is not available in web environment`,
      'NOT_TAURI_ENVIRONMENT',
      { command, args }
    );
  }

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
