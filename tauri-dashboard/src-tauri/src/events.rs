use tauri::Window;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct SessionUpdatePayload {
    pub session: String,
    pub status: String,
    pub controller_status: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LogUpdatePayload {
    pub session: String,
    pub log: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MetricUpdatePayload {
    pub session: String,
    pub response_time: f64,
    pub prompts_per_minute: f64,
    pub timestamp: DateTime<Utc>,
}

pub struct EventManager {
    window: Arc<RwLock<Option<Window>>>,
}

impl EventManager {
    pub fn new() -> Self {
        Self {
            window: Arc::new(RwLock::new(None)),
        }
    }
    
    pub async fn set_window(&self, window: Window) {
        *self.window.write().await = Some(window);
    }
    
    pub async fn emit_session_update(&self, session_name: &str, status: &str, controller_status: &str) {
        if let Some(window) = self.window.read().await.as_ref() {
            let payload = SessionUpdatePayload {
                session: session_name.to_string(),
                status: status.to_string(),
                controller_status: controller_status.to_string(),
            };
            
            let _ = window.emit("session-update", payload);
        }
    }
    
    pub async fn emit_log_update(&self, session_name: &str, log: &str) {
        if let Some(window) = self.window.read().await.as_ref() {
            let payload = LogUpdatePayload {
                session: session_name.to_string(),
                log: log.to_string(),
                timestamp: Utc::now(),
            };
            
            let _ = window.emit("log-update", payload);
        }
    }
    
    pub async fn emit_metric_update(&self, session_name: &str, response_time: f64, prompts_per_minute: f64) {
        if let Some(window) = self.window.read().await.as_ref() {
            let payload = MetricUpdatePayload {
                session: session_name.to_string(),
                response_time,
                prompts_per_minute,
                timestamp: Utc::now(),
            };
            
            let _ = window.emit("metric-update", payload);
        }
    }
    
    pub async fn emit_notification(&self, title: &str, message: &str, level: &str) {
        if let Some(window) = self.window.read().await.as_ref() {
            let payload = serde_json::json!({
                "title": title,
                "message": message,
                "level": level,
                "timestamp": Utc::now()
            });
            
            let _ = window.emit("notification", payload);
        }
    }
}

impl Default for EventManager {
    fn default() -> Self {
        Self::new()
    }
}