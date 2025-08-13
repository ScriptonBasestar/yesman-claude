import { writable, derived, type Writable } from 'svelte/store';

// Health status type definitions
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

// Initial health state
const initialHealth: HealthStatus = {
  overall: 'unknown',
  components: {},
  lastUpdated: new Date()
};

// Health store
export const health: Writable<HealthStatus> = writable(initialHealth);

// Health state derivations
export const healthState = derived(health, $health => $health.overall);

export const isHealthy = derived(health, $health => $health.overall === 'healthy');

export const isUnhealthy = derived(health, $health => 
  $health.overall === 'error' || $health.overall === 'warning'
);

// Health observable (reactive stream)
export const health$ = derived(health, $health => $health);

// Health status string
export const healthStatus = derived(health, $health => {
  switch ($health.overall) {
    case 'healthy': return '시스템 정상';
    case 'warning': return '주의 필요';
    case 'error': return '오류 발생';
    default: return '상태 확인 중';
  }
});

// Format last check time
export const formatLastCheck = derived(health, $health => {
  const now = new Date();
  const diff = now.getTime() - $health.lastUpdated.getTime();
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return '방금 전';
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
});

// Health update functions
export function updateHealthStatus(componentName: string, status: 'healthy' | 'warning' | 'error', message?: string) {
  health.update(current => {
    const updated = {
      ...current,
      components: {
        ...current.components,
        [componentName]: {
          status,
          message,
          lastCheck: new Date()
        }
      },
      lastUpdated: new Date()
    };

    // Update overall health based on components
    const componentStatuses = Object.values(updated.components).map(c => c.status);
    if (componentStatuses.some(s => s === 'error')) {
      updated.overall = 'error';
    } else if (componentStatuses.some(s => s === 'warning')) {
      updated.overall = 'warning';
    } else if (componentStatuses.length > 0 && componentStatuses.every(s => s === 'healthy')) {
      updated.overall = 'healthy';
    } else {
      updated.overall = 'unknown';
    }

    return updated;
  });
}

export function resetHealth() {
  health.set(initialHealth);
}

// Auto-refresh health status
let healthCheckInterval: NodeJS.Timeout | null = null;

export function startHealthMonitoring(intervalMs: number = 30000) {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
  }
  
  healthCheckInterval = setInterval(() => {
    // In a real implementation, this would call actual health check APIs
    // For now, we'll just update the timestamp
    health.update(current => ({
      ...current,
      lastUpdated: new Date()
    }));
  }, intervalMs);
}

export function stopHealthMonitoring() {
  if (healthCheckInterval) {
    clearInterval(healthCheckInterval);
    healthCheckInterval = null;
  }
}

// Initialize health monitoring on import
if (typeof window !== 'undefined') {
  startHealthMonitoring();
}