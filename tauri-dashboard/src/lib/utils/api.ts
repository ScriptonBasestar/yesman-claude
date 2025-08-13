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

// API utility class
export class ApiClient {
  private static instance: ApiClient;

  static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  // Generic Tauri command invocation with error handling
  async invoke<T>(command: string, args?: Record<string, any>): Promise<ApiResponse<T>> {
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
    return this.invoke<HealthStatus>('get_health_status');
  }

  async runHealthCheck(): Promise<ApiResponse<any>> {
    return this.invoke('run_health_check');
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