// HALF Command Center — Rust Backend
//
// Tauri 2.0 desktop shell with Python sidecar IPC.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;

// ─── State ───────────────────────────────────────────────────────────────────

struct AppState {
    project_path: Mutex<PathBuf>,
    finality_gate_locked: Mutex<bool>,
}

// ─── Data Models ─────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
struct PipelineStatus {
    project: String,
    mode: String,
    active_phase: Option<String>,
    completed_phases: Vec<String>,
    pending_phases: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct FinalityGateStatus {
    locked: bool,
    mrp_ready: bool,
    deployment_approved: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct ErrorBudgetStatus {
    remaining: i64,
    total: i64,
}

#[derive(Debug, Serialize, Deserialize)]
struct SidecarResult {
    status: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

// ─── Tauri Commands ──────────────────────────────────────────────────────────

#[tauri::command]
fn get_pipeline_status(state: tauri::State<AppState>) -> Result<PipelineStatus, String> {
    let path = state.project_path.lock().map_err(|e| e.to_string())?;
    let config_path = path.join(".hale/config.yaml");

    let (project_name, mode) = if config_path.exists() {
        if let Ok(content) = std::fs::read_to_string(&config_path) {
            (parse_yaml_value(&content, "project"), parse_yaml_value(&content, "mode"))
        } else {
            ("unknown".into(), "full".into())
        }
    } else {
        ("unknown".into(), "full".into())
    };

    let artifacts_dir = path.join(".hale/artifacts");
    let mut completed = Vec::new();
    if artifacts_dir.exists() {
        if let Ok(entries) = std::fs::read_dir(&artifacts_dir) {
            for entry in entries.flatten() {
                if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                    if let Some(name) = entry.file_name().to_str() {
                        completed.push(name.to_string());
                    }
                }
            }
        }
    }

    Ok(PipelineStatus {
        project: project_name,
        mode,
        active_phase: completed.last().cloned(),
        completed_phases: completed,
        pending_phases: Vec::new(),
    })
}

#[tauri::command]
fn get_finality_gate_status(state: tauri::State<AppState>) -> Result<FinalityGateStatus, String> {
    let locked = state.finality_gate_locked.lock().map_err(|e| e.to_string())?;
    let path = state.project_path.lock().map_err(|e| e.to_string())?;
    let gate_path = path.join(".hale/finality-gate.json");
    let mrp_ready = gate_path.exists();
    Ok(FinalityGateStatus {
        locked: *locked,
        mrp_ready,
        deployment_approved: !*locked && mrp_ready,
    })
}

#[tauri::command]
fn get_error_budget(state: tauri::State<AppState>) -> Result<ErrorBudgetStatus, String> {
    let path = state.project_path.lock().map_err(|e| e.to_string())?;
    let budget_path = path.join(".hale/metrics/error-budget.json");
    if budget_path.exists() {
        if let Ok(content) = std::fs::read_to_string(&budget_path) {
            if let Ok(data) = serde_json::from_str::<serde_json::Value>(&content) {
                let remaining = data.get("remaining").and_then(|v| v.as_i64()).unwrap_or(100);
                let total = data.get("total").and_then(|v| v.as_i64()).unwrap_or(100);
                return Ok(ErrorBudgetStatus { remaining, total });
            }
        }
    }
    Ok(ErrorBudgetStatus { remaining: 100, total: 100 })
}

#[tauri::command]
fn approve_deployment(signature: String, state: tauri::State<AppState>) -> Result<String, String> {
    if signature.len() < 8 {
        return Err("Sign-off key must be at least 8 characters".into());
    }
    let mut locked = state.finality_gate_locked.lock().map_err(|e| e.to_string())?;
    *locked = false;
    let path = state.project_path.lock().map_err(|e| e.to_string())?;
    let gate_path = path.join(".hale/finality-gate.json");
    let approval = serde_json::json!({
        "status": "approved",
        "signature_hash": sha256_hex(&signature),
        "approved_at": chrono_now(),
    });
    std::fs::write(&gate_path, serde_json::to_string_pretty(&approval).unwrap())
        .map_err(|e| e.to_string())?;
    Ok("Deployment approved.".into())
}

#[tauri::command]
fn run_goal_command(command: String, state: tauri::State<AppState>) -> Result<String, String> {
    let path = state.project_path.lock().map_err(|e| e.to_string())?;
    // Try the goal CLI sidecar first
    let result = Command::new("python3")
        .args(["-m", "half.goal"])
        .arg(&command)
        .current_dir(&*path)
        .output()
        .map_err(|e| format!("Failed to execute command: {}", e));

    let output = result.or_else(|_| {
        Command::new("python3")
            .args(["-m", "half.half_sidecar"])
            .arg(&command)
            .current_dir(&*path)
            .output()
            .map_err(|e| format!("Failed to execute command: {}", e))
    })?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if output.status.success() {
        Ok(stdout)
    } else {
        Err(format!("Command failed: {}", stderr))
    }
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

fn parse_yaml_value(content: &str, key: &str) -> String {
    for line in content.lines() {
        let line = line.trim();
        if let Some(val) = line.strip_prefix(&format!("{}:", key)) {
            return val.trim().trim_matches('"').to_string();
        }
    }
    String::from("unknown")
}

fn sha256_hex(input: &str) -> String {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    let mut hasher = DefaultHasher::new();
    input.hash(&mut hasher);
    format!("{:x}", hasher.finish())
}

fn chrono_now() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let dur = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
    format!("{}", dur.as_secs())
}

// ─── App Entrypoint ──────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_notification::init())
        .manage(AppState {
            project_path: Mutex::new(
                std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
            ),
            finality_gate_locked: Mutex::new(true),
        })
        .invoke_handler(tauri::generate_handler![
            get_pipeline_status,
            get_finality_gate_status,
            get_error_budget,
            approve_deployment,
            run_goal_command,
        ])
        .run(tauri::generate_context!())
        .expect("error while running HALF Command Center");
}
