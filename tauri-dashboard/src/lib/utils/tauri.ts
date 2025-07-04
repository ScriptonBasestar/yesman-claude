/**
 * Tauri API 통합 유틸리티
 * Python 브리지와 Tauri 이벤트 시스템을 연결
 */

import { invoke } from '@tauri-apps/api/tauri';
import { listen, emit } from '@tauri-apps/api/event';
import type { Session, SessionFilters } from '$lib/types/session';
import type { Notification } from '$lib/stores/notifications';

// Python 브리지 함수들
export const pythonBridge = {
  /**
   * 모든 세션 정보 가져오기
   */
  async getAllSessions(): Promise<Session[]> {
    try {
      const result = await invoke('get_all_sessions');
      return JSON.parse(result as string);
    } catch (error) {
      console.error('Failed to get sessions:', error);
      throw new Error(`Failed to get sessions: ${error}`);
    }
  },

  /**
   * Claude 컨트롤러 시작
   */
  async startController(sessionName: string): Promise<void> {
    try {
      await invoke('start_controller', { sessionName });
      await emit('controller-started', { sessionName });
    } catch (error) {
      console.error('Failed to start controller:', error);
      throw new Error(`Failed to start controller: ${error}`);
    }
  },

  /**
   * Claude 컨트롤러 중지
   */
  async stopController(sessionName: string): Promise<void> {
    try {
      await invoke('stop_controller', { sessionName });
      await emit('controller-stopped', { sessionName });
    } catch (error) {
      console.error('Failed to stop controller:', error);
      throw new Error(`Failed to stop controller: ${error}`);
    }
  },

  /**
   * Tmux 세션 설정
   */
  async setupTmuxSession(sessionName: string): Promise<void> {
    try {
      await invoke('setup_tmux_session', { sessionName });
      await emit('session-created', { sessionName });
    } catch (error) {
      console.error('Failed to setup session:', error);
      throw new Error(`Failed to setup session: ${error}`);
    }
  },

  /**
   * 모든 세션 설정
   */
  async setupAllSessions(): Promise<void> {
    try {
      await invoke('setup_all_sessions');
      await emit('all-sessions-created');
    } catch (error) {
      console.error('Failed to setup all sessions:', error);
      throw new Error(`Failed to setup all sessions: ${error}`);
    }
  },

  /**
   * 모든 세션 정리
   */
  async teardownAllSessions(): Promise<void> {
    try {
      await invoke('teardown_all_sessions');
      await emit('all-sessions-destroyed');
    } catch (error) {
      console.error('Failed to teardown all sessions:', error);
      throw new Error(`Failed to teardown all sessions: ${error}`);
    }
  },

  /**
   * 세션 로그 가져오기
   */
  async getSessionLogs(sessionName: string): Promise<string[]> {
    try {
      const result = await invoke('get_session_logs', { sessionName });
      return JSON.parse(result as string);
    } catch (error) {
      console.error('Failed to get session logs:', error);
      throw new Error(`Failed to get session logs: ${error}`);
    }
  },

  /**
   * 시스템 메트릭 가져오기
   */
  async getSystemMetrics(): Promise<any> {
    try {
      const result = await invoke('get_system_metrics');
      return JSON.parse(result as string);
    } catch (error) {
      console.error('Failed to get system metrics:', error);
      return {
        memoryUsage: 0,
        cpuUsage: 0,
        responseTime: 0,
        uptime: '0h 0m'
      };
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