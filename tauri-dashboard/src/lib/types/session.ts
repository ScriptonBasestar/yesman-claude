export interface SessionInfo {
  session_name: string;
  project_name: string;
  status: string;
  template: string;
  windows: WindowInfo[];
}

export interface WindowInfo {
  index: number;
  name: string;
  panes: PaneInfo[];
}

export interface PaneInfo {
  command: string;
  is_claude: boolean;
  is_controller: boolean;
}

export interface AppConfig {
  confidence_threshold: number;
  response_delay: number;
  max_retries: number;
  enable_auto_response: boolean;
  log_level: string;
  auto_refresh: boolean;
  refresh_interval: number;
}

export interface MetricData {
  timestamp: string;
  response_time: number;
  prompts_per_minute: number;
  session_name: string;
}

export interface DashboardStats {
  total_sessions: number;
  running_sessions: number;
  active_controllers: number;
  last_update: string;
}

export interface NotificationData {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
}

export type ControllerStatus = 'Active' | 'Ready' | 'Not Available' | 'Error';
export type SessionStatus = 'running' | 'stopped' | 'unknown';