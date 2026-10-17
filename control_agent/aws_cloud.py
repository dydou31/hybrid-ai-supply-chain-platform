import json
import os
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CLOUD_SCRIPT = PROJECT_DIR / "scripts" / "cloud-control.sh"
TERRAFORM_DIR = PROJECT_DIR / "terraform" / "aws"


STATE_FILE = PROJECT_DIR / "logs" / "cloud" / "operation.json"


def save_cloud_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2))
    temporary.replace(STATE_FILE)


def load_cloud_state():
    if not STATE_FILE.exists():
        return None

    return json.loads(STATE_FILE.read_text())


_lock = threading.Lock()
_process = None

_state = {
    "operation_id": None,
    "action": None,
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "returncode": None,
    "log_file": None,
}


def get_cloud_operation():
    with _lock:
        current = dict(_state)

    if current["status"] == "idle":
        saved = load_cloud_state()
        if saved:
            if saved.get("status") == "running":
                saved["status"] = "unknown"
                saved["message"] = (
                    "Control Agent restarted during a cloud operation. "
                    "Operation state must be verified."
                )
            return saved

    return current


def start_cloud_operation(action: str):
    global _process

    if action not in ("on", "off"):
        raise ValueError("Invalid cloud action")

    if not CLOUD_SCRIPT.is_file():
        raise RuntimeError("Cloud control script not found")

    with _lock:
        if _process is not None and _process.poll() is None:
            raise RuntimeError("Cloud operation already running")

        saved = load_cloud_state()
        if saved and saved.get("status") == "running":
            raise RuntimeError(
                "Previous cloud operation requires reconciliation "
                "before starting another operation"
            )

        # Prevent redundant or unsafe CLOUD ON/OFF operations.
        result = subprocess.run(
            [
                "aws", "ssm", "get-parameter",
                "--name", "/hybrid-ai/cloud/mode",
                "--region", "eu-west-3",
                "--profile", "hybrid-ai-terraform",
                "--query", "Parameter.Value",
                "--output", "text",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Cannot verify AWS cloud mode. Operation refused."
            )

        cloud_mode = result.stdout.strip().upper()

        if cloud_mode not in {"ON", "OFF", "TRANSITION"}:
            raise RuntimeError(
                "Unknown AWS cloud mode. Operation refused."
            )

        if cloud_mode == "TRANSITION":
            raise RuntimeError(
                "AWS cloud transition already in progress."
            )

        if cloud_mode == action.upper():
            raise RuntimeError(
                f"AWS cloud is already {cloud_mode}."
            )

        operation_id = str(uuid.uuid4())
        log_dir = PROJECT_DIR / "logs" / "cloud"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{operation_id}.log"

        env = os.environ.copy()
        env["AWS_PROFILE"] = "hybrid-ai-terraform"
        env["PYTHONUNBUFFERED"] = "1"
        env["HYBRID_AI_CLOUD_CONTROL_CENTER"] = "1"

        with log_file.open("w") as output:
            _process = subprocess.Popen(
                ["/bin/bash", str(CLOUD_SCRIPT), action],
                cwd=TERRAFORM_DIR,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        _state.update({
            "operation_id": operation_id,
            "action": action,
            "pid": _process.pid,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "returncode": None,
            "log_file": str(log_file),
        })

        save_cloud_state(_state)

    threading.Thread(
        target=_watch_process,
        args=(_process, operation_id),
        daemon=True,
    ).start()

    return get_cloud_operation()


def _watch_process(process, operation_id):
    process.wait()

    with _lock:
        if _state["operation_id"] != operation_id:
            return

        _state["returncode"] = process.returncode
        _state["status"] = (
            "success" if process.returncode == 0 else "failed"
        )
        _state["finished_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

        save_cloud_state(_state)
