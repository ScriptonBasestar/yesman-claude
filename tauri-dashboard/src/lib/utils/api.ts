import { invoke } from '@tauri-apps/api/tauri';

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: number;
}

export interface HealthStatus {
  overall: 'healthy' | 'warning' | 'error' | 'unknown';
  components: {
    [key: string]: {
      status: 'healthy' | 'warning' | 'error';
      message?: string;
      lastCheck: Date;
    };
  };
  lastUpdated: Date;
}

export interface PerformanceMetrics {
  cpu: {
    percent: number;
    status: 'normal' | 'high';
  };
  memory: {
    percent: number;
    total_gb: number;
    available_gb: number;
    status: 'normal' | 'high';
  };
  disk: {
    percent: number;
    total_gb: number;
    free_gb: number;
    status: 'normal' | 'high';
  };
  network?: {
    connections: number;
    bandwidth_usage: number;
  };
}

// Tauri 환경 감지 (웹에선 false)
// @ts-ignore
const isTauri = typeof window !== 'undefined' && typeof window.__TAURI_IPC__ === 'function' && typeof window.__TAURI__ === 'object';

// API utility class
export class ApiClient {
  private static instance: ApiClient;

  static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  // 공통 fetch 래퍼 (웹 전용)
  private async fetchJson<T>(url: string, init?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(url, init);
      if (!res.ok) {
        const text = await res.text();
        return { success: false, error: text || `HTTP ${res.status}`, timestamp: Date.now() };
      }
      const data = (await res.json()) as T;
      return { success: true, data, timestamp: Date.now() };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        timestamp: Date.now(),
      };
    }
  }

  // Generic Tauri command invocation with error handling
  async invoke<T>(command: string, args?: Record<string, any>): Promise<ApiResponse<T>> {
    if (!isTauri) {
      // 웹 환경에서는 Tauri invoke를 호출할 수 없음
      return {
        success: false,
        error: 'Not running in Tauri environment',
        timestamp: Date.now(),
      };
    }
    try {
      const result = await invoke(command, args);
      return {
        success: true,
        data: result as T,
        timestamp: Date.now()
      };
    } catch (error) {
      console.error(`API error in command ${command}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        timestamp: Date.now()
      };
    }
  }

  // Health check endpoints
  async getHealthStatus(): Promise<ApiResponse<HealthStatus>> {
    if (isTauri) {
      // Tauri 환경에서는 기존 명령 사용 (정의되어 있다면)
      return this.invoke<HealthStatus>('get_health_status');
    }
    // 웹 환경: FastAPI 대시보드 헬스 엔드포인트로 폴백하고 HealthStatus 형태로 매핑
    const res = await this.fetchJson<any>('/api/dashboard/health');
    if (!res.success || !res.data) return { success: false, error: res.error || 'Failed to fetch health', timestamp: Date.now() };

    // 매핑 로직: overall_score와 categories.status를 HealthStatus로 변환
    const score: number = Number(res.data.overall_score ?? 0);
    const overall: HealthStatus['overall'] = score >= 80 ? 'healthy' : score >= 50 ? 'warning' : 'error';

    const components: HealthStatus['components'] = {};
    const categories = res.data.categories || {};
    const mapStatus = (s: string): 'healthy' | 'warning' | 'error' => {
      const v = String(s || '').toLowerCase();
      if (v === 'good' || v === 'excellent' || v === 'ok') return 'healthy';
      if (v === 'warning' || v === 'warn') return 'warning';
      if (v === 'error' || v === 'critical' || v === 'bad') return 'error';
      return 'healthy';
    };
    for (const key of Object.keys(categories)) {
      const st = mapStatus(categories[key]?.status);
      components[key] = {
        status: st,
        message: categories[key]?.message,
        lastCheck: new Date(),
      };
    }

    return {
      success: true,
      data: { overall, components, lastUpdated: new Date() },
      timestamp: Date.now(),
    };
  }

  // 세션 목록 (웹: REST, Tauri: 가능 시 invoke)
  async getSessions(): Promise<ApiResponse<any[]>> {
    if (isTauri) {
      // Tauri 측에 명령이 없을 수 있으므로 우선 REST 사용
      // return this.invoke<any[]>('get_sessions');
      return this.fetchJson<any[]>('/api/sessions');
    }
    return this.fetchJson<any[]>('/api/sessions');
  }

  // Performance monitoring
  async getPerformanceMetrics(): Promise<ApiResponse<PerformanceMetrics>> {
    return this.invoke<PerformanceMetrics>('get_performance_metrics');
  }

  async getSystemInfo(): Promise<ApiResponse<any>> {
    return this.invoke('get_system_info');
  }

  // Process management
  async startProcess(processName: string, args?: string[]): Promise<ApiResponse<any>> {
    return this.invoke('start_process', { processName, args });
  }

  async stopProcess(processId: string): Promise<ApiResponse<any>> {
    return this.invoke('stop_process', { processId });
  }

  async getProcessList(): Promise<ApiResponse<any[]>> {
    return this.invoke('get_process_list');
  }

  // Dashboard configuration
  async getDashboardConfig(): Promise<ApiResponse<any>> {
    return this.invoke('get_dashboard_config');
  }

  async updateDashboardConfig(config: Record<string, any>): Promise<ApiResponse<any>> {
    return this.invoke('update_dashboard_config', { config });
  }

  // Log management
  async getLogs(service?: string, limit?: number): Promise<ApiResponse<any[]>> {
    return this.invoke('get_logs', { service, limit });
  }

  async clearLogs(service?: string): Promise<ApiResponse<any>> {
    return this.invoke('clear_logs', { service });
  }

  // File operations
  async readFile(path: string): Promise<ApiResponse<string>> {
    return this.invoke<string>('read_file', { path });
  }

  async writeFile(path: string, content: string): Promise<ApiResponse<any>> {
    return this.invoke('write_file', { path, content });
  }

  async listFiles(directory: string): Promise<ApiResponse<string[]>> {
    return this.invoke<string[]>('list_files', { directory });
  }

  // Deployment management
  async getDeploymentStatus(): Promise<ApiResponse<any>> {
    return this.invoke('get_deployment_status');
  }

  async startDeployment(config: Record<string, any>): Promise<ApiResponse<any>> {
    return this.invoke('start_deployment', { config });
  }

  async rollbackDeployment(deploymentId: string): Promise<ApiResponse<any>> {
    return this.invoke('rollback_deployment', { deploymentId });
  }

  // Error handling utilities
  static handleApiError(response: ApiResponse): string {
    if (response.success) {
      return '';
    }
    return response.error || 'Unknown API error occurred';
  }

  static isApiSuccess<T>(response: ApiResponse<T>): response is ApiResponse<T> & { success: true; data: T } {
    return response.success && response.data !== undefined;
  }
}

// Singleton instance for easy access
export const api = ApiClient.getInstance();

// React hooks for API calls (if using React)
export function useApiCall<T>(command: string, args?: Record<string, any>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.invoke<T>(command, args);
      if (response.success) {
        setData(response.data!);
      } else {
        setError(response.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [command, args]);

  return { data, loading, error, execute };
}

// Helper functions for common operations
export async function fetchWithRetry<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<ApiResponse<T>> {
  let lastError: string = '';
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await apiCall();
      if (response.success) {
        return response;
      }
      lastError = response.error || 'Unknown error';
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    
    if (attempt < maxRetries) {
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }
  
  return {
    success: false,
    error: `Failed after ${maxRetries} attempts. Last error: ${lastError}`,
    timestamp: Date.now()
  };
}

export default api;