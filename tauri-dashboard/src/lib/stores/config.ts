/**
 * 설정 상태 관리 스토어 (Tauri 연동)
 */

import { writable, get } from 'svelte/store';
import { tauriUtils } from '$lib/utils/tauri';

export interface AppConfig {
  theme: 'light' | 'dark' | 'auto';
  language: 'en' | 'ko';
  autoRefresh: {
    enabled: boolean;
    interval: number; // milliseconds
  };
  notifications: {
    enabled: boolean;
    desktop: boolean;
    sounds: boolean;
    autoHide: boolean;
    hideDelay: number;
  };
  dashboard: {
    compactMode: boolean;
    showMetrics: boolean;
    showCharts: boolean;
    defaultView: 'grid' | 'list';
    sessionsPerPage: number;
  };
  advanced: {
    debugMode: boolean;
    logLevel: 'error' | 'warn' | 'info' | 'debug';
    maxLogSize: number;
    enableTelemetry: boolean;
  };
  python: {
    executable: string;
    virtualEnv?: string;
    additionalPaths: string[];
  };
  tmux: {
    executable: string;
    defaultSession: string;
    autoAttach: boolean;
    mouseMode: boolean;
  };
}

// 기본 설정
const defaultConfig: AppConfig = {
  theme: 'auto',
  language: 'en',
  autoRefresh: {
    enabled: true,
    interval: 10000
  },
  notifications: {
    enabled: true,
    desktop: true,
    sounds: false,
    autoHide: true,
    hideDelay: 5000
  },
  dashboard: {
    compactMode: false,
    showMetrics: true,
    showCharts: true,
    defaultView: 'grid',
    sessionsPerPage: 20
  },
  advanced: {
    debugMode: false,
    logLevel: 'info',
    maxLogSize: 10485760, // 10MB
    enableTelemetry: false
  },
  python: {
    executable: 'python3',
    additionalPaths: []
  },
  tmux: {
    executable: 'tmux',
    defaultSession: 'yesman',
    autoAttach: false,
    mouseMode: true
  }
};

// 설정 스토어
export const config = writable<AppConfig>(defaultConfig);
export const isConfigLoading = writable<boolean>(false);
export const configError = writable<string | null>(null);

// 설정 변경 플래그
export const hasUnsavedChanges = writable<boolean>(false);

/**
 * 설정 로드
 */
export async function loadConfig(): Promise<void> {
  // 브라우저 환경 체크
  if (typeof window === 'undefined') {
    return;
  }

  isConfigLoading.set(true);
  configError.set(null);

  try {
    // Tauri에서 설정 파일 로드
    const savedConfig = await tauriUtils.loadConfig();

    if (savedConfig) {
      // 기본 설정과 병합 (새로운 설정 키가 추가될 수 있음)
      const mergedConfig = mergeConfigs(defaultConfig, savedConfig);
      config.set(mergedConfig);
    }

    hasUnsavedChanges.set(false);
  } catch (error) {
    console.error('Failed to load config:', error);
    configError.set(error instanceof Error ? error.message : 'Failed to load configuration');

    // 실패 시 기본 설정 사용
    config.set(defaultConfig);
  } finally {
    isConfigLoading.set(false);
  }
}

/**
 * 설정 저장
 */
export async function saveConfig(): Promise<void> {
  isConfigLoading.set(true);
  configError.set(null);

  try {
    const currentConfig = get(config);
    await tauriUtils.saveConfig(currentConfig);
    hasUnsavedChanges.set(false);
  } catch (error) {
    console.error('Failed to save config:', error);
    configError.set(error instanceof Error ? error.message : 'Failed to save configuration');
    throw error;
  } finally {
    isConfigLoading.set(false);
  }
}

/**
 * 설정 업데이트
 */
export function updateConfig(updates: Partial<AppConfig>): void {
  config.update(current => {
    const updated = mergeConfigs(current, updates);
    hasUnsavedChanges.set(true);
    return updated;
  });
}

/**
 * 특정 섹션 업데이트
 */
export function updateThemeConfig(theme: AppConfig['theme']): void {
  updateConfig({ theme });
  applyTheme(theme);
}

export function updateNotificationConfig(notifications: Partial<AppConfig['notifications']>): void {
  config.update(current => ({
    ...current,
    notifications: { ...current.notifications, ...notifications }
  }));
  hasUnsavedChanges.set(true);
}

export function updateDashboardConfig(dashboard: Partial<AppConfig['dashboard']>): void {
  config.update(current => ({
    ...current,
    dashboard: { ...current.dashboard, ...dashboard }
  }));
  hasUnsavedChanges.set(true);
}

export function updateAdvancedConfig(advanced: Partial<AppConfig['advanced']>): void {
  config.update(current => ({
    ...current,
    advanced: { ...current.advanced, ...advanced }
  }));
  hasUnsavedChanges.set(true);
}

/**
 * 설정 리셋
 */
export async function resetConfig(): Promise<void> {
  config.set(defaultConfig);
  hasUnsavedChanges.set(true);
  await saveConfig();
}

export async function resetSection(section: keyof AppConfig): Promise<void> {
  const currentConfig = get(config);
  const resetConfig = {
    ...currentConfig,
    [section]: defaultConfig[section]
  };

  config.set(resetConfig);
  hasUnsavedChanges.set(true);
}

/**
 * 설정 내보내기/가져오기
 */
export function exportConfig(): string {
  const currentConfig = get(config);
  return JSON.stringify({
    config: currentConfig,
    exportedAt: new Date().toISOString(),
    version: '1.0'
  }, null, 2);
}

export async function importConfig(jsonData: string): Promise<boolean> {
  try {
    const data = JSON.parse(jsonData);

    if (data.config && typeof data.config === 'object') {
      const importedConfig = mergeConfigs(defaultConfig, data.config);
      config.set(importedConfig);
      hasUnsavedChanges.set(true);
      await saveConfig();
      return true;
    }

    return false;
  } catch (error) {
    console.error('Failed to import config:', error);
    return false;
  }
}

/**
 * 테마 적용
 */
export function applyTheme(theme: AppConfig['theme']): void {
  const html = document.documentElement;

  if (theme === 'auto') {
    // 시스템 테마 따르기
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
  } else {
    html.setAttribute('data-theme', theme);
  }
}

/**
 * 언어 변경
 */
export function changeLanguage(language: AppConfig['language']): void {
  updateConfig({ language });

  // 언어 변경 이벤트 발송
  window.dispatchEvent(new CustomEvent('language-changed', {
    detail: { language }
  }));
}

/**
 * 설정 유효성 검사
 */
export function validateConfig(configToValidate: Partial<AppConfig>): string[] {
  const errors: string[] = [];

  // 자동 새로고침 간격 검사
  if (configToValidate.autoRefresh?.interval !== undefined) {
    if (configToValidate.autoRefresh.interval < 1000) {
      errors.push('Auto-refresh interval must be at least 1 second');
    }
    if (configToValidate.autoRefresh.interval > 300000) {
      errors.push('Auto-refresh interval must not exceed 5 minutes');
    }
  }

  // 알림 숨김 지연 시간 검사
  if (configToValidate.notifications?.hideDelay !== undefined) {
    if (configToValidate.notifications.hideDelay < 1000) {
      errors.push('Notification hide delay must be at least 1 second');
    }
  }

  // 페이지당 세션 수 검사
  if (configToValidate.dashboard?.sessionsPerPage !== undefined) {
    if (configToValidate.dashboard.sessionsPerPage < 5) {
      errors.push('Sessions per page must be at least 5');
    }
    if (configToValidate.dashboard.sessionsPerPage > 100) {
      errors.push('Sessions per page must not exceed 100');
    }
  }

  // 최대 로그 크기 검사
  if (configToValidate.advanced?.maxLogSize !== undefined) {
    if (configToValidate.advanced.maxLogSize < 1048576) { // 1MB
      errors.push('Max log size must be at least 1MB');
    }
  }

  return errors;
}

/**
 * 설정 변경 감지 및 자동 저장
 */
export function setupAutoSave(enabled: boolean = true, delay: number = 30000): void {
  // 브라우저 환경 체크
  if (typeof window === 'undefined') {
    return;
  }

  if (!enabled) return;

  let saveTimeout: number;

  hasUnsavedChanges.subscribe(hasChanges => {
    if (hasChanges) {
      // 변경사항이 있으면 일정 시간 후 자동 저장
      clearTimeout(saveTimeout);
      saveTimeout = setTimeout(async () => {
        try {
          await saveConfig();
          console.log('Configuration auto-saved');
        } catch (error) {
          console.error('Auto-save failed:', error);
        }
      }, delay);
    }
  });
}

/**
 * 키보드 단축키 설정
 */
export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  action: string;
  description: string;
}

export const keyboardShortcuts: KeyboardShortcut[] = [
  { key: 'r', ctrlKey: true, action: 'refresh', description: 'Refresh sessions' },
  { key: 's', ctrlKey: true, action: 'save', description: 'Save configuration' },
  { key: 'n', ctrlKey: true, action: 'new_session', description: 'Create new session' },
  { key: 'f', ctrlKey: true, action: 'search', description: 'Focus search' },
  { key: '/', action: 'search', description: 'Focus search' },
  { key: 'Escape', action: 'clear_selection', description: 'Clear selection' },
  { key: 'a', ctrlKey: true, action: 'select_all', description: 'Select all sessions' },
  { key: 'Delete', action: 'delete_selected', description: 'Delete selected sessions' }
];

/**
 * 내부 유틸리티 함수들
 */
function mergeConfigs(base: AppConfig, override: Partial<AppConfig>): AppConfig {
  const merged = { ...base };

  for (const [key, value] of Object.entries(override)) {
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      // 객체 타입은 재귀적으로 병합
      merged[key as keyof AppConfig] = {
        ...merged[key as keyof AppConfig],
        ...value
      } as any;
    } else {
      // 원시 타입이나 배열은 그대로 덮어씀
      merged[key as keyof AppConfig] = value as any;
    }
  }

  return merged;
}

/**
 * 시스템 테마 변경 감지
 */
export function setupThemeDetection(): void {
  // 브라우저 환경 체크
  if (typeof window === 'undefined') {
    return;
  }

  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

  const handleThemeChange = () => {
    const currentConfig = get(config);
    if (currentConfig.theme === 'auto') {
      applyTheme('auto');
    }
  };

  // 초기 테마 적용
  handleThemeChange();

  // 시스템 테마 변경 감지
  mediaQuery.addEventListener('change', handleThemeChange);
}

/**
 * 개발자 모드 토글
 */
export function toggleDebugMode(): void {
  config.update(current => ({
    ...current,
    advanced: {
      ...current.advanced,
      debugMode: !current.advanced.debugMode
    }
  }));
  hasUnsavedChanges.set(true);

  // 디버그 모드 이벤트 발송
  const isDebug = get(config).advanced.debugMode;
  window.dispatchEvent(new CustomEvent('debug-mode-changed', {
    detail: { enabled: isDebug }
  }));
}

// 초기화 시 설정 로드 및 테마 감지 설정 (브라우저 환경에서만)
if (typeof window !== 'undefined') {
  loadConfig();
  setupThemeDetection();
  setupAutoSave();
}
