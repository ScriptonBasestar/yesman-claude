use tauri::{api::notification::Notification, AppHandle};

#[tauri::command]
pub async fn show_notification(
    app: AppHandle,
    title: String,
    body: String,
    icon: Option<String>
) -> Result<(), String> {
    Notification::new(&app.config().tauri.bundle.identifier)
        .title(&title)
        .body(&body)
        .icon(&icon.unwrap_or_else(|| "icon.png".to_string()))
        .show()
        .map_err(|e| e.to_string())
}

pub fn notify_controller_status_change(
    app: &AppHandle,
    session_name: &str,
    status: &str
) -> Result<(), String> {
    let title = "Controller Status Changed".to_string();
    let body = format!("{}: {}", session_name, status);
    
    Notification::new(&app.config().tauri.bundle.identifier)
        .title(&title)
        .body(&body)
        .show()
        .map_err(|e| e.to_string())
}

pub fn notify_session_event(
    app: &AppHandle,
    session_name: &str,
    event: &str,
    message: &str
) -> Result<(), String> {
    let title = format!("Session Event: {}", event);
    let body = format!("{}: {}", session_name, message);
    
    Notification::new(&app.config().tauri.bundle.identifier)
        .title(&title)
        .body(&body)
        .show()
        .map_err(|e| e.to_string())
}