import base64
import json
import os
import secrets
import subprocess
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pwdlib import PasswordHash

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_DIR / ".env")


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Hybrid AI Control Agent",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Content-Type",
        "X-Admin-Password",
    ],
)


# ============================================================
# CONFIGURATION
# ============================================================

ALLOWED_SERVICES = {
    "api",
    "db",
    "redis",
    "prometheus",
    "tempo",
    "grafana",
}

ALLOWED_ACTIONS = {
    "start",
    "stop",
}

ADMIN_PASSWORD_HASH = os.getenv(
    "CONTROL_ADMIN_PASSWORD_HASH",
    "",
).replace("$$", "$")

password_hash = PasswordHash.recommended()


# ============================================================
# WEBAUTHN / TOUCH ID CONFIGURATION
# ============================================================

RP_ID = "localhost"
RP_NAME = "Hybrid AI Control Center"

EXPECTED_ORIGIN = "http://localhost:5173"

WEBAUTHN_USER_ID = b"hybrid-ai-control-admin"
WEBAUTHN_USER_NAME = "admin"

PASSKEY_FILE = (
    Path(__file__).resolve().parent
    / ".webauthn_credential.json"
)

CHALLENGE_TTL_SECONDS = 300


# Registration challenges:
#
# request_id -> {
#     challenge,
#     created_at
# }
registration_challenges: dict[str, dict] = {}


# Authentication challenges:
#
# request_id -> {
#     challenge,
#     created_at,
#     service,
#     action
# }
authentication_challenges: dict[str, dict] = {}


# ============================================================
# BASE64URL HELPERS
# ============================================================

def bytes_to_base64url(value: bytes) -> str:
    return (
        base64.urlsafe_b64encode(value)
        .rstrip(b"=")
        .decode("ascii")
    )


def base64url_to_bytes(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)

    return base64.urlsafe_b64decode(
        value + padding
    )


# ============================================================
# ADMIN PASSWORD
# ============================================================

def verify_admin_password(
    password: str | None,
):
    if not ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=503,
            detail=(
                "Control Agent authentication "
                "is not configured"
            ),
        )

    if not password:
        raise HTTPException(
            status_code=401,
            detail=(
                "Administrator authentication required"
            ),
        )

    try:
        valid = password_hash.verify(
            password,
            ADMIN_PASSWORD_HASH,
        )

    except Exception:
        valid = False

    if not valid:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid administrator credentials"
            ),
        )


# ============================================================
# PASSKEY STORAGE
# ============================================================

def load_passkey():
    if not PASSKEY_FILE.exists():
        return None

    try:
        return json.loads(
            PASSKEY_FILE.read_text(
                encoding="utf-8",
            )
        )

    except Exception:
        return None


def save_passkey(
    credential_id: bytes,
    credential_public_key: bytes,
    sign_count: int,
):
    data = {
        "credential_id": bytes_to_base64url(
            credential_id
        ),
        "credential_public_key": bytes_to_base64url(
            credential_public_key
        ),
        "sign_count": sign_count,
    }

    PASSKEY_FILE.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )


# ============================================================
# CHALLENGE MANAGEMENT
# ============================================================

def cleanup_challenges():
    now = time.time()

    for store in (
        registration_challenges,
        authentication_challenges,
    ):
        expired = [
            request_id
            for request_id, item in store.items()
            if (
                now - item["created_at"]
                > CHALLENGE_TTL_SECONDS
            )
        ]

        for request_id in expired:
            store.pop(
                request_id,
                None,
            )


def new_request_id():
    return secrets.token_urlsafe(32)


def get_valid_challenge(
    store: dict[str, dict],
    request_id: str,
):
    cleanup_challenges()

    item = store.pop(
        request_id,
        None,
    )

    if not item:
        raise HTTPException(
            status_code=400,
            detail=(
                "WebAuthn challenge is invalid "
                "or has expired"
            ),
        )

    return item


# ============================================================
# SERVICE VALIDATION
# ============================================================

def validate_service_action(
    service: str,
    action: str,
):
    # Special authenticated action:
    # local business-data promotion to AWS.
    if service == "aws-sync" and action == "sync_aws":
        return

    if service not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Service '{service}' is not allowed"
            ),
        )

    if action not in ALLOWED_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Action '{action}' is not allowed"
            ),
        )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "control-agent",
        "authentication": (
            "enabled"
            if ADMIN_PASSWORD_HASH
            else "not-configured"
        ),
        "passkey": (
            "configured"
            if load_passkey()
            else "not-configured"
        ),
    }


# ============================================================
# WEBAUTHN STATUS
# ============================================================

@app.get("/webauthn/status")
def webauthn_status():
    return {
        "configured": (
            load_passkey() is not None
        ),
        "rp_id": RP_ID,
    }


# ============================================================
# WEBAUTHN REGISTRATION OPTIONS
# ============================================================

@app.post("/webauthn/register/options")
def webauthn_register_options(
    x_admin_password: str | None = Header(
        default=None
    ),
):
    verify_admin_password(
        x_admin_password
    )

    cleanup_challenges()

    existing_passkey = load_passkey()

    exclude_credentials = []

    if existing_passkey:
        exclude_credentials.append(
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(
                    existing_passkey[
                        "credential_id"
                    ]
                )
            )
        )

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=WEBAUTHN_USER_ID,
        user_name=WEBAUTHN_USER_NAME,
        user_display_name=(
            "Hybrid AI Administrator"
        ),
        timeout=60000,
        authenticator_selection=(
            AuthenticatorSelectionCriteria(
                authenticator_attachment=(
                    AuthenticatorAttachment.PLATFORM
                ),
                resident_key=(
                    ResidentKeyRequirement.PREFERRED
                ),
                user_verification=(
                    UserVerificationRequirement.REQUIRED
                ),
            )
        ),
        exclude_credentials=exclude_credentials,
    )

    request_id = new_request_id()

    registration_challenges[
        request_id
    ] = {
        "challenge": options.challenge,
        "created_at": time.time(),
    }

    return {
        "request_id": request_id,
        "publicKey": json.loads(
            options_to_json(options)
        ),
    }


# ============================================================
# WEBAUTHN REGISTRATION VERIFY
# ============================================================

@app.post("/webauthn/register/verify")
def webauthn_register_verify(
    payload: dict,
    x_admin_password: str | None = Header(
        default=None
    ),
):
    verify_admin_password(
        x_admin_password
    )

    request_id = payload.get(
        "request_id"
    )

    credential = payload.get(
        "credential"
    )

    if not request_id or not credential:
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing WebAuthn registration data"
            ),
        )

    challenge_data = get_valid_challenge(
        registration_challenges,
        request_id,
    )

    try:
        verification = (
            verify_registration_response(
                credential=credential,
                expected_challenge=(
                    challenge_data[
                        "challenge"
                    ]
                ),
                expected_rp_id=RP_ID,
                expected_origin=EXPECTED_ORIGIN,
                require_user_verification=True,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=(
                "Passkey registration verification "
                f"failed: {exc}"
            ),
        )

    save_passkey(
        credential_id=(
            verification.credential_id
        ),
        credential_public_key=(
            verification.credential_public_key
        ),
        sign_count=(
            verification.sign_count
        ),
    )

    return {
        "success": True,
        "configured": True,
        "message": (
            "Touch ID / Passkey configured"
        ),
    }


# ============================================================
# WEBAUTHN AUTHENTICATION OPTIONS
# ============================================================

@app.post("/webauthn/authenticate/options")
def webauthn_authenticate_options(
    payload: dict,
):
    service = payload.get(
        "service"
    )

    action = payload.get(
        "action"
    )

    validate_service_action(
        service,
        action,
    )

    cleanup_challenges()

    passkey = load_passkey()

    if not passkey:
        raise HTTPException(
            status_code=404,
            detail=(
                "Touch ID / Passkey "
                "is not configured"
            ),
        )

    credential_id = (
        base64url_to_bytes(
            passkey[
                "credential_id"
            ]
        )
    )

    options = (
        generate_authentication_options(
            rp_id=RP_ID,
            timeout=60000,
            allow_credentials=[
                PublicKeyCredentialDescriptor(
                    id=credential_id
                )
            ],
            user_verification=(
                UserVerificationRequirement.REQUIRED
            ),
        )
    )

    request_id = new_request_id()

    authentication_challenges[
        request_id
    ] = {
        "challenge": options.challenge,
        "created_at": time.time(),
        "service": service,
        "action": action,
    }

    return {
        "request_id": request_id,
        "publicKey": json.loads(
            options_to_json(options)
        ),
    }


# ============================================================
# WEBAUTHN AUTHENTICATION VERIFY + ACTION
# ============================================================

@app.post("/webauthn/authenticate/verify")
def webauthn_authenticate_verify(
    payload: dict,
):
    request_id = payload.get(
        "request_id"
    )

    credential = payload.get(
        "credential"
    )

    if not request_id or not credential:
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing WebAuthn "
                "authentication data"
            ),
        )

    challenge_data = get_valid_challenge(
        authentication_challenges,
        request_id,
    )

    passkey = load_passkey()

    if not passkey:
        raise HTTPException(
            status_code=404,
            detail=(
                "Touch ID / Passkey "
                "is not configured"
            ),
        )

    credential_id = (
        base64url_to_bytes(
            passkey[
                "credential_id"
            ]
        )
    )

    credential_public_key = (
        base64url_to_bytes(
            passkey[
                "credential_public_key"
            ]
        )
    )

    submitted_credential_id = (
        credential.get("id")
    )

    if (
        submitted_credential_id
        != passkey["credential_id"]
    ):
        raise HTTPException(
            status_code=401,
            detail=(
                "Unknown WebAuthn credential"
            ),
        )

    try:
        verification = (
            verify_authentication_response(
                credential=credential,
                expected_challenge=(
                    challenge_data[
                        "challenge"
                    ]
                ),
                expected_rp_id=RP_ID,
                expected_origin=EXPECTED_ORIGIN,
                credential_public_key=(
                    credential_public_key
                ),
                credential_current_sign_count=(
                    passkey.get(
                        "sign_count",
                        0,
                    )
                ),
                require_user_verification=True,
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=(
                "Touch ID / Passkey "
                f"verification failed: {exc}"
            ),
        )

    save_passkey(
        credential_id=credential_id,
        credential_public_key=(
            credential_public_key
        ),
        sign_count=(
            verification.new_sign_count
        ),
    )

    service = challenge_data[
        "service"
    ]

    action = challenge_data[
        "action"
    ]

    if action == "sync_aws":
        return run_aws_sync()

    return run_compose_action(
        action,
        service,
    )


# ============================================================
# PGVECTOR STATUS
# ============================================================

def pgvector_status():
    """
    Check pgvector directly inside PostgreSQL,
    independently of FastAPI.
    """

    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "db",
                "psql",
                "-U",
                os.getenv(
                    "POSTGRES_USER",
                    "postgres",
                ),
                "-d",
                os.getenv(
                    "POSTGRES_DB",
                    "hybrid_ai_db",
                ),
                "-tAc",
                (
                    "SELECT EXISTS "
                    "(SELECT 1 FROM pg_extension "
                    "WHERE extname = 'vector');"
                ),
            ],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )

        running = (
            result.stdout.strip().lower()
            == "t"
        )

        return {
            "state": (
                "running"
                if running
                else "unavailable"
            ),
            "health": (
                "healthy"
                if running
                else ""
            ),
            "status": (
                "pgvector extension active"
                if running
                else (
                    "pgvector extension unavailable"
                )
            ),
            "running": running,
        }

    except Exception:
        return {
            "state": "unavailable",
            "health": "",
            "status": (
                "pgvector check failed"
            ),
            "running": False,
        }


# ============================================================
# OLLAMA STATUS
# ============================================================

def ollama_status():
    """
    Check Ollama and llama3.2:3b directly,
    independently of FastAPI.
    """

    try:
        request = urllib.request.Request(
            (
                "http://127.0.0.1:"
                "11434/api/tags"
            ),
            headers={
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=3,
        ) as response:
            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        models = {
            model.get("name")
            for model in data.get(
                "models",
                [],
            )
            if model.get("name")
        }

        running = (
            "llama3.2:3b"
            in models
        )

        return {
            "state": (
                "running"
                if running
                else "unavailable"
            ),
            "health": (
                "healthy"
                if running
                else ""
            ),
            "status": (
                (
                    "Ollama + llama3.2:3b "
                    "available"
                )
                if running
                else (
                    "Ollama available but "
                    "llama3.2:3b missing"
                )
            ),
            "running": running,
        }

    except Exception:
        return {
            "state": "unavailable",
            "health": "",
            "status": (
                "Ollama unavailable"
            ),
            "running": False,
        }


# ============================================================
# DOCKER SERVICE STATUS
# ============================================================

@app.get("/services/status")
def services_status():
    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "ps",
                "--all",
                "--format",
                "json",
            ],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail=(
                "Docker Compose status timed out"
            ),
        )

    except subprocess.CalledProcessError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Docker Compose status unavailable"
            ),
        )

    docker_services = {}

    for line in result.stdout.splitlines():
        if not line.strip():
            continue

        item = json.loads(line)

        service = item.get(
            "Service"
        )

        if service in ALLOWED_SERVICES:
            state = item.get(
                "State",
                "unknown",
            )

            docker_services[
                service
            ] = {
                "state": state,
                "health": item.get(
                    "Health",
                    "",
                ),
                "status": item.get(
                    "Status",
                    "",
                ),
                "running": (
                    state == "running"
                ),
            }

    services = {}

    for service in ALLOWED_SERVICES:
        services[
            service
        ] = docker_services.get(
            service,
            {
                "state": "not-created",
                "health": "",
                "status": "Not created",
                "running": False,
            },
        )

    services[
        "pgvector"
    ] = pgvector_status()

    services[
        "ollama"
    ] = ollama_status()

    return {
        "services": services,
    }


# ============================================================
# DOCKER ACTION
# ============================================================

def run_compose_action(
    action: str,
    service: str,
):
    validate_service_action(
        service,
        action,
    )

    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                action,
                service,
            ],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )

        return {
            "success": True,
            "service": service,
            "action": action,
            "output": (
                result.stdout.strip()
            ),
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail=(
                "Docker Compose command "
                "timed out"
            ),
        )

    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                exc.stderr.strip()
                or (
                    "Docker Compose "
                    "command failed"
                )
            ),
        )

# ============================================================
# AWS DATA SYNC
# ============================================================

def run_aws_sync():
    try:
        result = subprocess.run(
            [
                str(PROJECT_DIR / ".venv" / "bin" / "python"),
                str(
                    PROJECT_DIR
                    / "scripts"
                    / "sync_local_to_aws.py"
                ),
            ],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )

        return {
            "success": True,
            "target": "aws",
            "output": result.stdout.strip(),
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="AWS sync timed out",
        )

    except subprocess.CalledProcessError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                exc.stderr.strip()
                or exc.stdout.strip()
                or "AWS sync failed"
            ),
        )


@app.post("/sync/aws")
def sync_to_aws(
    x_admin_password: str | None = Header(
        default=None
    ),
):
    verify_admin_password(
        x_admin_password
    )

    return run_aws_sync()

# ============================================================
# PASSWORD FALLBACK
# ============================================================

@app.post(
    "/services/{service}/stop"
)
def stop_service(
    service: str,
    x_admin_password: str | None = Header(
        default=None
    ),
):
    verify_admin_password(
        x_admin_password
    )

    return run_compose_action(
        "stop",
        service,
    )


@app.post(
    "/services/{service}/start"
)
def start_service(
    service: str,
    x_admin_password: str | None = Header(
        default=None
    ),
):
    verify_admin_password(
        x_admin_password
    )

    return run_compose_action(
        "start",
        service,
    )
