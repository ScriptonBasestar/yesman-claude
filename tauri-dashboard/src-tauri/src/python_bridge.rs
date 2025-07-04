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
    from libs.streamlit_dashboard.session_actions import setup_tmux_sessions
    result = setup_tmux_sessions('{}')
    print(result)
except Exception as e:
    print(False)
"#, name),
        None => r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.streamlit_dashboard.session_actions import setup_tmux_sessions
    result = setup_tmux_sessions()
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
    from libs.streamlit_dashboard.session_actions import teardown_tmux_sessions
    result = teardown_tmux_sessions('{}')
    print(result)
except Exception as e:
    print(False)
"#, name),
        None => r#"
import sys
sys.path.append('.')
sys.path.append('..')

try:
    from libs.streamlit_dashboard.session_actions import teardown_tmux_sessions
    result = teardown_tmux_sessions()
    print(result)
except Exception as e:
    print(False)
"#.to_string()
    };
    
    let result = execute_python_script(&script)?;
    Ok(result.trim() == "True")
}

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