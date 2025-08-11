export interface PaneInfo {
	id: string;
	command: string;
	is_claude: boolean;
	is_controller: boolean;
	current_task: string | null;
	idle_time: number;
	last_activity: string | null; // ISO 8601 date string
	cpu_usage: number;
	memory_usage: number;
	pid: number | null;
	running_time: number;
	status: string;
	activity_score: number;
	last_output: string | null;
	output_lines: number;
}

export interface WindowInfo {
	name: string;
	index: string;
	panes: PaneInfo[];
}

export interface Session {
	project_name: string;
	session_name: string; // This will be used as the ID
	template: string;
	exists: boolean;
	status: 'running' | 'stopped';
	windows: WindowInfo[];
	controller_status: 'running' | 'not running' | 'unknown';
	description?: string;
	controller_error?: string | null;
	uptime?: string;
	last_activity_timestamp?: number;
	total_panes?: number;
}

export interface SessionFilters {
	search: string;
	status: string;
	controllerStatus: string;
	sortBy: 'session_name' | 'status' | 'uptime' | 'last_activity';
	sortOrder: 'asc' | 'desc';
	showOnlyErrors: boolean;
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

// User Experience Types
export interface TroubleshootingIssue {
	id: string;
	title: string;
	description: string;
	severity: 'low' | 'medium' | 'high' | 'critical';
	category: string;
	auto_fixable: boolean;
}

export interface TroubleshootingStep {
	id: string;
	title: string;
	description: string;
	command: string | null;
	safety_level: 'safe' | 'moderate' | 'high_risk';
	estimated_time: number;
}

export interface TroubleshootingResult {
	success: boolean;
	message: string;
	steps_executed: string[];
	execution_time: number;
}

export interface SetupStep {
	id: string;
	name: string;
	description: string;
	safety_level: 'safe' | 'moderate' | 'high_risk';
	estimated_time: number;
	dependencies: string[];
}

export interface SetupResult {
	success: boolean;
	message: string;
	details: string;
}

export interface DocumentationInfo {
	doc_type: string;
	title: string;
	path: string;
	last_updated: string;
	size_kb: number;
}

export interface SystemHealth {
	status: 'healthy' | 'degraded' | 'unhealthy';
	components: {
		[key: string]: {
			status: 'healthy' | 'degraded' | 'unhealthy';
			message?: string;
			last_check?: string;
		};
	};
	metrics?: {
		[key: string]: number | string;
	};
}
