use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader, Read, Write};
use std::net::TcpStream;
use std::process::{Child as DebugChild, Command as DebugCommand, Stdio};
use std::sync::Mutex;
use std::time::Duration;
use tauri::{AppHandle, Manager, RunEvent, State};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

#[derive(Clone, Debug, Deserialize)]
struct Handshake {
    event: String,
    port: u16,
    token: String,
    startup_id: String,
    version: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeConfig {
    api_base: String,
    token: String,
    startup_id: String,
    sidecar_version: String,
}

enum SidecarChild {
    Debug(DebugChild),
    Release(CommandChild),
}

impl SidecarChild {
    fn kill(&mut self) {
        match self {
            Self::Debug(child) => {
                let _ = child.kill();
                let _ = child.wait();
            }
            Self::Release(child) => {
                let _ = child.kill();
            }
        }
    }
}

struct RuntimeState {
    config: RuntimeConfig,
    child: Mutex<Option<SidecarChild>>,
}

fn parse_handshake(line: &str) -> Option<Handshake> {
    let value: Handshake = serde_json::from_str(line).ok()?;
    (value.event == "ready" && !value.token.is_empty()).then_some(value)
}

fn runtime_from_handshake(handshake: Handshake) -> RuntimeConfig {
    RuntimeConfig {
        api_base: format!("http://127.0.0.1:{}/", handshake.port),
        token: handshake.token,
        startup_id: handshake.startup_id,
        sidecar_version: handshake.version,
    }
}

fn sidecar_args(app: &AppHandle) -> Result<Vec<String>, String> {
    let config_root = app
        .path()
        .app_config_dir()
        .map_err(|error| format!("无法确定应用配置目录：{error}"))?;
    let default_vault = app
        .path()
        .document_dir()
        .map_err(|error| format!("无法确定文档目录：{error}"))?
        .join("Skills Vault");
    Ok(vec![
        "--desktop-mode".into(),
        "--port".into(),
        "0".into(),
        "--desktop-config-root".into(),
        config_root.to_string_lossy().into_owned(),
        "--default-vault-root".into(),
        default_vault.to_string_lossy().into_owned(),
        "--allowed-origin".into(),
        "tauri://localhost".into(),
        "--allowed-origin".into(),
        "http://tauri.localhost".into(),
        "--allowed-origin".into(),
        "http://127.0.0.1:1420".into(),
        "--parent-pid".into(),
        std::process::id().to_string(),
    ])
}

#[cfg(debug_assertions)]
fn spawn_sidecar(app: &AppHandle) -> Result<(RuntimeConfig, SidecarChild), String> {
    let project_root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .ok_or("无法确定项目根目录")?;
    let mut args = vec![
        project_root.join("server/http_server.py").to_string_lossy().into_owned(),
        "--static-root".into(),
        project_root.join("app/dist").to_string_lossy().into_owned(),
    ];
    args.extend(sidecar_args(app)?);
    let mut child = DebugCommand::new("python3")
        .args(args)
        .current_dir(project_root)
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()
        .map_err(|error| format!("无法启动 Python 开发服务：{error}"))?;
    let stdout = child.stdout.take().ok_or("无法读取 Python 服务启动信息")?;
    let mut lines = BufReader::new(stdout).lines();
    let handshake = loop {
        let line = lines
            .next()
            .ok_or("Python 服务在完成启动前退出")?
            .map_err(|error| format!("读取 Python 服务启动信息失败：{error}"))?;
        if let Some(handshake) = parse_handshake(&line) {
            break handshake;
        }
    };
    std::thread::spawn(move || {
        for line in lines.map_while(Result::ok) {
            eprintln!("[sidecar] {line}");
        }
    });
    Ok((runtime_from_handshake(handshake), SidecarChild::Debug(child)))
}

#[cfg(not(debug_assertions))]
fn spawn_sidecar(app: &AppHandle) -> Result<(RuntimeConfig, SidecarChild), String> {
    let command = app
        .shell()
        .sidecar("skills-vault-sidecar")
        .map_err(|error| format!("无法准备 Skills Vault sidecar：{error}"))?
        .args(sidecar_args(app)?);
    let (mut events, child) = command
        .spawn()
        .map_err(|error| format!("无法启动 Skills Vault sidecar：{error}"))?;
    let handshake = tauri::async_runtime::block_on(async {
        loop {
            match events.recv().await {
                Some(CommandEvent::Stdout(bytes)) => {
                    let line = String::from_utf8_lossy(&bytes);
                    if let Some(handshake) = parse_handshake(line.trim()) {
                        break Ok(handshake);
                    }
                }
                Some(CommandEvent::Stderr(bytes)) => {
                    eprintln!("[sidecar] {}", String::from_utf8_lossy(&bytes));
                }
                Some(CommandEvent::Terminated(payload)) => {
                    break Err(format!("sidecar 在完成启动前退出：{:?}", payload.code));
                }
                None => break Err("sidecar 启动通道已关闭".into()),
                _ => {}
            }
        }
    })?;
    tauri::async_runtime::spawn(async move {
        while let Some(event) = events.recv().await {
            if let CommandEvent::Stderr(bytes) = event {
                eprintln!("[sidecar] {}", String::from_utf8_lossy(&bytes));
            }
        }
    });
    Ok((runtime_from_handshake(handshake), SidecarChild::Release(child)))
}

#[tauri::command]
fn runtime_config(state: State<'_, RuntimeState>) -> RuntimeConfig {
    state.config.clone()
}

fn request_shutdown(config: &RuntimeConfig) {
    let address = config.api_base.trim_start_matches("http://").trim_end_matches('/');
    if let Ok(mut stream) = TcpStream::connect_timeout(
        &address.parse().unwrap_or_else(|_| "127.0.0.1:0".parse().unwrap()),
        Duration::from_millis(500),
    ) {
        let request = format!(
            "POST /api/runtime/shutdown HTTP/1.1\r\nHost: {address}\r\nAuthorization: Bearer {}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n",
            config.token
        );
        let _ = stream.write_all(request.as_bytes());
        let _ = stream.set_read_timeout(Some(Duration::from_millis(500)));
        let mut response = [0_u8; 64];
        let _ = stream.read(&mut response);
    }
}

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let (config, child) = spawn_sidecar(app.handle())
                .map_err(|message| std::io::Error::new(std::io::ErrorKind::Other, message))?;
            app.manage(RuntimeState {
                config,
                child: Mutex::new(Some(child)),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![runtime_config])
        .build(tauri::generate_context!())
        .expect("Skills Vault desktop failed to start");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            if let Some(state) = app_handle.try_state::<RuntimeState>() {
                request_shutdown(&state.config);
                if let Ok(mut guard) = state.child.lock() {
                    if let Some(mut child) = guard.take() {
                        std::thread::sleep(Duration::from_millis(300));
                        child.kill();
                    }
                }
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_only_ready_handshakes() {
        assert!(parse_handshake(r#"{"event":"log","port":1,"token":"x","startup_id":"s","version":"2"}"#).is_none());
        let parsed = parse_handshake(r#"{"event":"ready","port":43123,"token":"secret","startup_id":"start","version":"2.1.0"}"#).unwrap();
        assert_eq!(runtime_from_handshake(parsed).api_base, "http://127.0.0.1:43123/");
    }
}
