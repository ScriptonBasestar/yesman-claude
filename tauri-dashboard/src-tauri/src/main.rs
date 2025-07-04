#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod python_bridge;
mod events;
mod cache;
mod notifications;

use tauri::{CustomMenuItem, SystemTray, SystemTrayMenu, SystemTrayEvent, Manager};
use python_bridge::*;
use events::EventManager;
use notifications::*;

fn create_system_tray() -> SystemTray {
    let show = CustomMenuItem::new("show".to_string(), "Show Dashboard");
    let start_all = CustomMenuItem::new("start_all".to_string(), "Start All Sessions");
    let stop_all = CustomMenuItem::new("stop_all".to_string(), "Stop All Sessions");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_native_item(tauri::SystemTrayMenuItem::Separator)
        .add_item(start_all)
        .add_item(stop_all)
        .add_native_item(tauri::SystemTrayMenuItem::Separator)
        .add_item(quit);
    
    SystemTray::new().with_menu(tray_menu)
}

fn handle_system_tray_event(app: &tauri::AppHandle, event: SystemTrayEvent) {
    match event {
        SystemTrayEvent::MenuItemClick { id, .. } => {
            match id.as_str() {
                "show" => {
                    let window = app.get_window("main").unwrap();
                    window.show().unwrap();
                    window.set_focus().unwrap();
                }
                "start_all" => {
                    // 모든 컨트롤러 시작
                    tauri::async_runtime::spawn(async move {
                        let _ = start_all_controllers().await;
                    });
                }
                "stop_all" => {
                    // 모든 컨트롤러 중지
                    tauri::async_runtime::spawn(async move {
                        let _ = stop_all_controllers().await;
                    });
                }
                "quit" => {
                    std::process::exit(0);
                }
                _ => {}
            }
        }
        _ => {}
    }
}

fn main() {
    tauri::Builder::default()
        .system_tray(create_system_tray())
        .on_system_tray_event(handle_system_tray_event)
        .manage(EventManager::new())
        .invoke_handler(tauri::generate_handler![
            get_all_sessions,
            get_controller_status,
            start_controller,
            stop_controller,
            restart_claude_pane,
            get_app_config,
            save_app_config,
            get_session_logs,
            get_metrics_data,
            setup_tmux_session,
            teardown_tmux_session,
            show_notification
        ])
        .setup(|app| {
            // 이벤트 매니저에 윈도우 등록
            let window = app.get_window("main").unwrap();
            let event_manager = app.state::<EventManager>();
            
            tauri::async_runtime::spawn(async move {
                event_manager.set_window(window).await;
            });
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}