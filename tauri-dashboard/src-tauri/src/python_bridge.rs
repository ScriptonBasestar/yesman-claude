use std::process::Command;
use serde::{Deserialize, Serialize};
use tauri::command;
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SessionInfo {
    pub session_name: String,
    pub project_name: String,
    pub status: String,
    pub template: String,
    pub windows: Vec<WindowInfo>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WindowInfo {
    pub index: i32,
    pub name: String,
    pub panes: Vec<PaneInfo>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PaneInfo {
    pub command: String,
    pub is_claude: bool,
    pub is_controller: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AppConfig {
    pub confidence_threshold: f64,
    pub response_delay: f64,
    pub max_retries: i32,
    pub enable_auto_response: bool,
    pub log_level: String,
    pub auto_refresh: bool,
    pub refresh_interval: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MetricData {
    pub timestamp: DateTime<Utc>,
    pub response_time: f64,
    pub prompts_per_minute: f64,
    pub session_name: String,
}

// User Experience related structures
#[derive(Debug, Serialize, Deserialize)]
pub struct TroubleshootingIssue {
    pub id: String,
    pub title: String,
    pub description: String,
    pub severity: String,
    pub category: String,
    pub auto_fixable: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TroubleshootingStep {
    pub id: String,
    pub title: String,
    pub description: String,
    pub command: Option<String>,
    pub safety_level: String,
    pub estimated_time: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TroubleshootingResult {
    pub success: bool,
    pub message: String,
    pub steps_executed: Vec<String>,
    pub execution_time: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SetupStep {
    pub id: String,
    pub name: String,
    pub description: String,
    pub safety_level: String,
    pub estimated_time: i32,
    pub dependencies: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SetupResult {
    pub success: bool,
    pub message: String,
    pub details: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DocumentationInfo {
    pub doc_type: String,
    pub title: String,
    pub path: String,
    pub last_updated: DateTime<Utc>,
    pub size_kb: i32,
}

fn execute_python_script(script: &str) -> Result<String, String> {
    let output = Command::new("python")
        .args(["-c", script])
        .output()
        .map_err(|e| format!("Failed to execute command: {}", e))?;

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }

    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

#[command]
pub async fn get_all_sessions() -> Result<Vec<SessionInfo>, String> {
    let script = r#"
import sys
import os
sys.path.append('.')
sys.path.append('..')

try:
    from libs.core.session_manager import SessionManager
    sm = SessionManager()
    sessions = sm.get_all_sessions()

    import json
    result = []
    for s in sessions:
        windows = []
        if hasattr(s, 'windows') and s.windows:
            for w in s.windows:
                panes = []
                if hasattr(w, 'panes') and w.panes:
                    for p in w.panes:
                        panes.append({
                            'command': getattr(p, 'command', ''),
                            'is_claude': getattr(p, 'is_claude', False),
                            'is_controller': getattr(p, 'is_controller', False)
                        })
                windows.append({
                    'index': getattr(w, 'index', 0),
                    'name': getattr(w, 'name', ''),
                    'panes': panes
                })

        result.append({
            'session_name': getattr(s, 'session_name', ''),
            'project_name': getattr(s, 'project_name', ''),
            'status': getattr(s, 'status', 'unknown'),
            'template': getattr(s, 'template', ''),
            'windows': windows
        })

    print(json.dumps(result))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"#;

    let result = execute_python_script(script)?;

    // 에러 체크
    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse JSON: {}", e))
}

#[command]
pub async fn get_controller_status(session_name: String) -> Result<String, String> {
    let script = format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.core.claude_manager import ClaudeManager
    cm = ClaudeManager()
    controller = cm.get_controller('{}')
    if controller:
        if controller.is_running:
            print('Active')
        else:
            print('Ready')
    else:
        print('Not Available')
except Exception as e:
    print('Error')
"#, session_name);

    execute_python_script(&script)
}

#[command]
pub async fn start_controller(session_name: String) -> Result<bool, String> {
    let script = format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.core.claude_manager import ClaudeManager
    cm = ClaudeManager()
    controller = cm.get_controller('{}')
    if controller:
        result = controller.start()
        print(result)
    else:
        print(False)
except Exception as e:
    print(False)
"#, session_name);

    let result = execute_python_script(&script)?;
    Ok(result.trim() == "True")
}

#[command]
pub async fn stop_controller(session_name: String) -> Result<bool, String> {
    let script = format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.core.claude_manager import ClaudeManager
    cm = ClaudeManager()
    controller = cm.get_controller('{}')
    if controller:
        result = controller.stop()
        print(result)
    else:
        print(False)
except Exception as e:
    print(False)
"#, session_name);

    let result = execute_python_script(&script)?;
    Ok(result.trim() == "True")
}

#[command]
pub async fn restart_claude_pane(session_name: String) -> Result<bool, String> {
    let script = format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.core.claude_manager import ClaudeManager
    cm = ClaudeManager()
    controller = cm.get_controller('{}')
    if controller:
        result = controller.restart_claude_pane()
        print(result)
    else:
        print(False)
except Exception as e:
    print(False)
"#, session_name);

    let result = execute_python_script(&script)?;
    Ok(result.trim() == "True")
}

#[command]
pub async fn get_app_config() -> Result<AppConfig, String> {
    let script = r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.yesman_config import YesmanConfig
    config = YesmanConfig()

    # 기본 설정값들
    result = {
        'confidence_threshold': 0.8,
        'response_delay': 1.0,
        'max_retries': 3,
        'enable_auto_response': True,
        'log_level': 'INFO',
        'auto_refresh': True,
        'refresh_interval': 2
    }

    import json
    print(json.dumps(result))
except Exception as e:
    import json
    print(json.dumps({'error': str(e)}))
"#;

    let result = execute_python_script(script)?;

    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse config JSON: {}", e))
}

#[command]
pub async fn save_app_config(config: AppConfig) -> Result<bool, String> {
    // 설정 저장 로직 (현재는 더미)
    println!("Saving config: {:?}", config);
    Ok(true)
}

#[command]
pub async fn get_session_logs(session_name: String, limit: Option<i32>) -> Result<Vec<String>, String> {
    let limit = limit.unwrap_or(100);

    // 더미 로그 데이터 (실제로는 Python에서 로그 파일 읽기)
    let mut logs = Vec::new();
    for i in 0..limit {
        logs.push(format!("[{:02}:{:02}:{:02}] Log entry {} for session {}",
            (i / 3600) % 24, (i / 60) % 60, i % 60, i, session_name));
    }

    Ok(logs)
}

#[command]
pub async fn get_metrics_data(_time_range: String) -> Result<Vec<MetricData>, String> {
    // 더미 메트릭 데이터
    let mut metrics = Vec::new();
    let now = Utc::now();

    for i in 0..20 {
        metrics.push(MetricData {
            timestamp: now - chrono::Duration::minutes(i),
            response_time: 100.0 + (i as f64) * 10.0,
            prompts_per_minute: 5.0 + (i as f64) * 0.5,
            session_name: "example".to_string(),
        });
    }

    Ok(metrics)
}

#[command]
pub async fn setup_tmux_session(session_name: Option<String>) -> Result<bool, String> {
    let script = match session_name {
        Some(name) => format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.tmux_manager import TmuxManager
    manager = TmuxManager()
    result = manager.setup_project('{}')
    print(result)
except Exception as e:
    print(False)
"#, name),
        None => r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.tmux_manager import TmuxManager
    manager = TmuxManager()
    result = manager.setup_all_projects()
    print(result)
except Exception as e:
    print(False)
"#.to_string()
    };

    let result = execute_python_script(&script)?;
    Ok(result.trim() == "True")
}

#[command]
pub async fn teardown_tmux_session(session_name: Option<String>) -> Result<bool, String> {
    let script = match session_name {
        Some(name) => format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.tmux_manager import TmuxManager
    manager = TmuxManager()
    result = manager.teardown_project('{}')
    print(result)
except Exception as e:
    print(False)
"#, name),
        None => r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.tmux_manager import TmuxManager
    manager = TmuxManager()
    result = manager.teardown_all_projects()
    print(result)
except Exception as e:
    print(False)
"#.to_string()
    };

    let result = execute_python_script(&script)?;
    Ok(result.trim() == "True")
}

// User Experience Commands
#[command]
pub async fn run_troubleshooting_diagnosis() -> Result<Vec<TroubleshootingIssue>, String> {
    let script = r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.troubleshooting import IntelligentTroubleshootingEngine
    engine = IntelligentTroubleshootingEngine()
    issues = engine.diagnose_issues()
    
    import json
    result = []
    for issue in issues:
        result.append({
            'id': getattr(issue, 'id', ''),
            'title': getattr(issue, 'title', ''),
            'description': getattr(issue, 'description', ''),
            'severity': getattr(issue, 'severity', 'low'),
            'category': getattr(issue, 'category', 'general'),
            'auto_fixable': getattr(issue, 'auto_fixable', False)
        })
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"#;

    let result = execute_python_script(script)?;
    
    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse troubleshooting result: {}", e))
}

#[command]
pub async fn get_troubleshooting_guide(issue_id: String) -> Result<Vec<TroubleshootingStep>, String> {
    let script = format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.troubleshooting import IntelligentTroubleshootingEngine
    engine = IntelligentTroubleshootingEngine()
    guide = engine.get_troubleshooting_guide('{}')
    
    import json
    result = []
    if guide:
        for step in guide.steps:
            result.append({{
                'id': getattr(step, 'id', ''),
                'title': getattr(step, 'title', ''),
                'description': getattr(step, 'description', ''),
                'command': getattr(step, 'command', None),
                'safety_level': getattr(step, 'safety_level', 'safe'),
                'estimated_time': getattr(step, 'estimated_time', 30)
            }})
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{'error': str(e)}}))
"#, issue_id);

    let result = execute_python_script(&script)?;
    
    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse troubleshooting guide: {}", e))
}

#[command]
pub async fn execute_troubleshooting_fix(issue_id: String, auto_approve: bool) -> Result<TroubleshootingResult, String> {
    let script = format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.troubleshooting import IntelligentTroubleshootingEngine
    engine = IntelligentTroubleshootingEngine()
    result = engine.execute_fix('{}', auto_approve={})
    
    import json
    output = {{
        'success': getattr(result, 'success', False),
        'message': getattr(result, 'message', ''),
        'steps_executed': getattr(result, 'steps_executed', []),
        'execution_time': getattr(result, 'execution_time', 0.0)
    }}
    
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({{'error': str(e)}}))
"#, issue_id, auto_approve);

    let result = execute_python_script(&script)?;
    
    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse fix result: {}", e))
}

#[command]
pub async fn generate_documentation() -> Result<Vec<DocumentationInfo>, String> {
    let script = r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from scripts.documentation_generator import LiveDocumentationGenerator
    generator = LiveDocumentationGenerator()
    docs = generator.generate_all()
    
    import json
    from datetime import datetime
    result = []
    for doc in docs:
        result.append({
            'doc_type': getattr(doc, 'doc_type', 'general'),
            'title': getattr(doc, 'title', ''),
            'path': getattr(doc, 'path', ''),
            'last_updated': datetime.now().isoformat() + 'Z',
            'size_kb': getattr(doc, 'size_kb', 0)
        })
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"#;

    let result = execute_python_script(script)?;
    
    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse documentation result: {}", e))
}

#[command]
pub async fn get_setup_steps() -> Result<Vec<SetupStep>, String> {
    let script = r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.onboarding import IntelligentSetupAssistant
    assistant = IntelligentSetupAssistant()
    steps = assistant.get_available_steps()
    
    import json
    result = []
    for step in steps:
        result.append({
            'id': getattr(step, 'id', ''),
            'name': getattr(step, 'name', ''),
            'description': getattr(step, 'description', ''),
            'safety_level': getattr(step, 'safety_level', 'safe'),
            'estimated_time': getattr(step, 'estimated_time', 60),
            'dependencies': getattr(step, 'dependencies', [])
        })
    
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({'error': str(e)}))
"#;

    let result = execute_python_script(script)?;
    
    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse setup steps: {}", e))
}

#[command]
pub async fn run_setup_step(step_id: String, interactive: bool) -> Result<SetupResult, String> {
    let script = format!(r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.onboarding import IntelligentSetupAssistant
    assistant = IntelligentSetupAssistant()
    result = assistant.run_setup_step('{}', interactive={})
    
    import json
    output = {{
        'success': getattr(result, 'success', False),
        'message': getattr(result, 'message', ''),
        'details': getattr(result, 'details', '')
    }}
    
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({{'error': str(e)}}))
"#, step_id, interactive);

    let result = execute_python_script(&script)?;
    
    if result.contains("\"error\"") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse setup result: {}", e))
}

#[command]
pub async fn get_system_health() -> Result<serde_json::Value, String> {
    let script = r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.dashboard.monitoring_integration import MonitoringIntegration
    monitor = MonitoringIntegration()
    health = monitor.get_system_health()
    
    import json
    print(json.dumps(health))
except Exception as e:
    print(json.dumps({'error': str(e), 'status': 'unhealthy'}))
"#;

    let result = execute_python_script(script)?;
    
    if result.contains("\"error\"") && !result.contains("status") {
        return Err(format!("Python error: {}", result));
    }

    serde_json::from_str(&result)
        .map_err(|e| format!("Failed to parse health status: {}", e))
}

#[allow(dead_code)]
pub async fn start_all_controllers() -> Result<i32, String> {
    let sessions = get_all_sessions().await?;
    let mut success_count = 0;

    for session in sessions {
        if let Ok(true) = start_controller(session.session_name).await {
            success_count += 1;
        }
    }

    Ok(success_count)
}

#[allow(dead_code)]
pub async fn stop_all_controllers() -> Result<i32, String> {
    let sessions = get_all_sessions().await?;
    let mut success_count = 0;

    for session in sessions {
        if let Ok(true) = stop_controller(session.session_name).await {
            success_count += 1;
        }
    }

    Ok(success_count)
}
