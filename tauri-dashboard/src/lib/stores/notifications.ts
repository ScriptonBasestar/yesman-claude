/**
 * 알림 상태 관리 스토어 (Tauri 연동)
 */

import { writable, get } from 'svelte/store';
import { tauriUtils } from '$lib/utils/tauri';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  timestamp: number;
  read: boolean;
  persistent?: boolean;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  label: string;
  action: string;
  style?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
}

// 알림 스토어
export const notifications = writable<Notification[]>([]);
export const unreadCount = writable<number>(0);

// 알림 설정
export const notificationSettings = writable({
  enabled: true,
  showDesktopNotifications: true,
  autoHideDelay: 5000, // 5초 후 자동 숨김
  maxNotifications: 50, // 최대 알림 개수
  persistErrors: true, // 에러 알림은 수동으로만 삭제
  enableSounds: false
});

/**
 * 새 알림 생성
 */
export function showNotification(
  type: 'success' | 'error' | 'warning' | 'info',
  title: string,
  message?: string,
  persistent?: boolean,
  actions?: NotificationAction[]
): string {
  const notification: Notification = {
    id: generateNotificationId(),
    type,
    title,
    message,
    timestamp: Date.now(),
    read: false,
    persistent,
    actions
  };

  // 스토어에 추가
  notifications.update(current => {
    const updated = [notification, ...current];

    // 최대 개수 제한
    const maxNotifications = get(notificationSettings).maxNotifications;
    if (updated.length > maxNotifications) {
      return updated.slice(0, maxNotifications);
    }

    return updated;
  });

  // 읽지 않은 알림 수 업데이트
  updateUnreadCount();

  // 데스크톱 알림 표시
  const settings = get(notificationSettings);
  if (settings.enabled && settings.showDesktopNotifications) {
    sendDesktopNotification(notification);
  }

  // 자동 숨김 설정 (에러는 지속 설정에 따라)
  if (!persistent && !(type === 'error' && settings.persistErrors)) {
    setTimeout(() => {
      markAsRead(notification.id);
    }, settings.autoHideDelay);
  }

  return notification.id;
}

/**
 * 편의 함수들
 */
export function notifySuccess(title: string, message?: string, actions?: NotificationAction[]): string {
  return showNotification('success', title, message, false, actions);
}

export function notifyError(title: string, message?: string, persistent: boolean = true, actions?: NotificationAction[]): string {
  return showNotification('error', title, message, persistent, actions);
}

export function notifyWarning(title: string, message?: string, persistent: boolean = false, actions?: NotificationAction[]): string {
  return showNotification('warning', title, message, persistent, actions);
}

export function notifyInfo(title: string, message?: string, persistent: boolean = false, actions?: NotificationAction[]): string {
  return showNotification('info', title, message, persistent, actions);
}

/**
 * 알림 관리 함수들
 */
export function dismissNotification(id: string): void {
  notifications.update(current => current.filter(n => n.id !== id));
  updateUnreadCount();
}

export function markAsRead(id: string): void {
  notifications.update(current =>
    current.map(n => n.id === id ? { ...n, read: true } : n)
  );
  updateUnreadCount();
}

export function markAllAsRead(): void {
  notifications.update(current =>
    current.map(n => ({ ...n, read: true }))
  );
  updateUnreadCount();
}

export function clearAllNotifications(): void {
  notifications.set([]);
  unreadCount.set(0);
}

export function clearReadNotifications(): void {
  notifications.update(current => current.filter(n => !n.read));
  updateUnreadCount();
}

/**
 * 알림 액션 처리
 */
export function executeNotificationAction(notificationId: string, actionId: string): void {
  const allNotifications = get(notifications);
  const notification = allNotifications.find(n => n.id === notificationId);

  if (!notification) return;

  const action = notification.actions?.find(a => a.action === actionId);
  if (!action) return;

  // 액션별 처리
  switch (actionId) {
    case 'retry':
      // 재시도 로직 - 커스텀 이벤트 발송
      window.dispatchEvent(new CustomEvent('notification-retry', {
        detail: { notificationId, originalNotification: notification }
      }));
      break;

    case 'view_logs':
      // 로그 보기
      tauriUtils.openLogFile();
      break;

    case 'open_settings':
      // 설정 열기
      window.dispatchEvent(new CustomEvent('open-settings'));
      break;

    case 'dismiss':
      dismissNotification(notificationId);
      break;

    default:
      // 커스텀 액션 - 이벤트 발송
      window.dispatchEvent(new CustomEvent('notification-action', {
        detail: { notificationId, actionId, notification }
      }));
  }

  // 액션 실행 후 알림을 읽음으로 표시
  markAsRead(notificationId);
}

/**
 * 알림 설정 관리
 */
export function updateNotificationSettings(newSettings: Partial<typeof notificationSettings>): void {
  notificationSettings.update(current => ({ ...current, ...newSettings }));
}

export function toggleDesktopNotifications(): void {
  notificationSettings.update(current => ({
    ...current,
    showDesktopNotifications: !current.showDesktopNotifications
  }));
}

export function toggleNotificationSounds(): void {
  notificationSettings.update(current => ({
    ...current,
    enableSounds: !current.enableSounds
  }));
}

/**
 * 내부 유틸리티 함수들
 */
function generateNotificationId(): string {
  return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function updateUnreadCount(): void {
  const current = get(notifications);
  const unread = current.filter(n => !n.read).length;
  unreadCount.set(unread);
}

async function sendDesktopNotification(notification: Notification): Promise<void> {
  try {
    await tauriUtils.sendNotification(
      notification.title,
      notification.message || '',
      notification.type
    );
  } catch (error) {
    console.warn('Failed to send desktop notification:', error);
  }
}

/**
 * 알림 템플릿들
 */
export const notificationTemplates = {
  sessionCreated(sessionName: string): Notification {
    return {
      id: generateNotificationId(),
      type: 'success',
      title: 'Session Created',
      message: `Tmux session "${sessionName}" has been created successfully`,
      timestamp: Date.now(),
      read: false,
      actions: [
        { label: 'View Session', action: 'view_session', style: 'primary' },
        { label: 'Dismiss', action: 'dismiss', style: 'secondary' }
      ]
    };
  },

  controllerStarted(sessionName: string): Notification {
    return {
      id: generateNotificationId(),
      type: 'success',
      title: 'Controller Started',
      message: `Claude controller for "${sessionName}" is now running`,
      timestamp: Date.now(),
      read: false,
      actions: [
        { label: 'View Details', action: 'view_details', style: 'primary' },
        { label: 'View Logs', action: 'view_logs', style: 'secondary' }
      ]
    };
  },

  controllerError(sessionName: string, error: string): Notification {
    return {
      id: generateNotificationId(),
      type: 'error',
      title: 'Controller Error',
      message: `Error in "${sessionName}": ${error}`,
      timestamp: Date.now(),
      read: false,
      persistent: true,
      actions: [
        { label: 'Restart Controller', action: 'restart_controller', style: 'warning' },
        { label: 'View Logs', action: 'view_logs', style: 'secondary' },
        { label: 'Dismiss', action: 'dismiss', style: 'error' }
      ]
    };
  },

  systemWarning(message: string): Notification {
    return {
      id: generateNotificationId(),
      type: 'warning',
      title: 'System Warning',
      message,
      timestamp: Date.now(),
      read: false,
      persistent: false,
      actions: [
        { label: 'Check Settings', action: 'open_settings', style: 'warning' },
        { label: 'Dismiss', action: 'dismiss', style: 'secondary' }
      ]
    };
  },

  connectionLost(): Notification {
    return {
      id: generateNotificationId(),
      type: 'error',
      title: 'Connection Lost',
      message: 'Lost connection to Python backend. Attempting to reconnect...',
      timestamp: Date.now(),
      read: false,
      persistent: true,
      actions: [
        { label: 'Retry Connection', action: 'retry_connection', style: 'error' },
        { label: 'Check Logs', action: 'view_logs', style: 'secondary' }
      ]
    };
  },

  batchOperationComplete(operation: string, successful: number, failed: number): Notification {
    const type = failed === 0 ? 'success' : successful === 0 ? 'error' : 'warning';
    const title = failed === 0 ? 'Operation Complete' : 'Operation Partial';
    const message = failed === 0
      ? `${operation} completed successfully for ${successful} item${successful > 1 ? 's' : ''}`
      : `${operation} completed: ${successful} successful, ${failed} failed`;

    return {
      id: generateNotificationId(),
      type,
      title,
      message,
      timestamp: Date.now(),
      read: false,
      persistent: failed > 0,
      actions: failed > 0 ? [
        { label: 'View Details', action: 'view_batch_details', style: 'primary' },
        { label: 'Retry Failed', action: 'retry_failed', style: 'warning' }
      ] : undefined
    };
  }
};

/**
 * 시스템 이벤트와 알림 연결
 */
export function setupNotificationSystem(): void {
  // 브라우저 환경 체크
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  // 백엔드 연결 상태 모니터링
  let connectionCheckInterval: number;

  function startConnectionMonitoring() {
    connectionCheckInterval = setInterval(async () => {
      try {
        // 간단한 핑 테스트
        await tauriUtils.sendNotification('test', 'test', 'info');
      } catch (error) {
        showNotification('error', 'Connection Lost', 'Lost connection to Python backend', true, [
          { label: 'Retry', action: 'retry_connection', style: 'error' }
        ]);
        clearInterval(connectionCheckInterval);
      }
    }, 30000); // 30초마다 체크
  }

  // 연결 모니터링 시작
  startConnectionMonitoring();

  // 커스텀 이벤트 리스너 설정
  window.addEventListener('notification-retry', (event) => {
    const { notificationId, originalNotification } = (event as CustomEvent).detail;
    // 재시도 로직 구현
    console.log('Retrying notification action:', notificationId, originalNotification);
  });

  // 페이지 가시성 변경 시 알림 읽음 처리
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      // 페이지가 다시 보이면 일정 시간 후 모든 알림을 읽음으로 표시
      setTimeout(() => {
        const settings = get(notificationSettings);
        if (settings.enabled) {
          markAllAsRead();
        }
      }, 2000);
    }
  });
}

/**
 * 알림 내보내기/가져오기
 */
export function exportNotifications(): string {
  const allNotifications = get(notifications);
  return JSON.stringify({
    notifications: allNotifications,
    exportedAt: new Date().toISOString(),
    version: '1.0'
  }, null, 2);
}

export function importNotifications(jsonData: string): boolean {
  try {
    const data = JSON.parse(jsonData);
    if (data.notifications && Array.isArray(data.notifications)) {
      notifications.set(data.notifications);
      updateUnreadCount();
      return true;
    }
    return false;
  } catch (error) {
    console.error('Failed to import notifications:', error);
    return false;
  }
}

// 알림 시스템 초기화 (브라우저 환경에서만)
if (typeof window !== 'undefined') {
  setupNotificationSystem();
}
