from fastapi import FastAPI, Request, Response, HTTPException, Depends
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.observability.tracing import setup_tracing
from datetime import datetime, timedelta, timezone
import os
import hashlib
import hmac
import secrets
import base64
import json
import uuid

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cloud_auth import CloudPasskey, CloudWebAuthnChallenge
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.routers.sync import router as sync_router

from app.routers.suppliers import router as suppliers_router
from app.routers.health import router as health_router
from app.routers.purchase_orders import router as purchase_orders_router
from app.routers.kpis import router as kpis_router
from app.ai.router import router as ai_router


setup_tracing()

app = FastAPI(
    title="Hybrid AI Supply Chain Platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str


class WebAuthnRegistrationVerifyRequest(BaseModel):
    request_id: str
    username: str
    password: str
    credential: dict


class WebAuthnAuthenticationVerifyRequest(BaseModel):
    request_id: str
    credential: dict


CLOUD_RP_ID = "dw3e18cneqohd.cloudfront.net"
CLOUD_ORIGIN = "https://dw3e18cneqohd.cloudfront.net"
CLOUD_RP_NAME = "Hybrid AI Supply Chain Platform"
WEBAUTHN_CHALLENGE_TTL_MINUTES = 5


CLOUD_SESSION_COOKIE = "hybrid_ai_session"
CLOUD_SESSION_MAX_AGE_SECONDS = 8 * 60 * 60


def _cloud_session_secret() -> str:
    secret = os.getenv("CLOUD_SESSION_SECRET")
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Cloud session authentication is not configured",
        )
    return secret


def _create_cloud_session_token() -> str:
    expires_at = (
        int(datetime.now(timezone.utc).timestamp())
        + CLOUD_SESSION_MAX_AGE_SECONDS
    )

    payload = str(expires_at)

    signature = hmac.new(
        _cloud_session_secret().encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload}.{signature}"


def _verify_cloud_session_token(token: str | None) -> None:
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    try:
        expires_text, supplied_signature = token.split(".", 1)
        expires_at = int(expires_text)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )

    expected_signature = hmac.new(
        _cloud_session_secret().encode("utf-8"),
        expires_text.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    if not secrets.compare_digest(
        supplied_signature,
        expected_signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )

    if expires_at <= int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(
            status_code=401,
            detail="Session expired",
        )


def require_cloud_session(request: Request) -> None:
    _verify_cloud_session_token(
        request.cookies.get(CLOUD_SESSION_COOKIE)
    )


def _set_cloud_session_cookie(response: Response) -> None:
    response.set_cookie(
        key=CLOUD_SESSION_COOKIE,
        value=_create_cloud_session_token(),
        max_age=CLOUD_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _verify_cloud_credentials(username: str, password: str) -> None:
    expected_username = os.getenv("CLOUD_AUTH_USERNAME")
    expected_password = os.getenv("CLOUD_AUTH_PASSWORD")

    if not expected_username or not expected_password:
        raise HTTPException(
            status_code=503,
            detail="Cloud authentication is not configured",
        )

    if not (
        secrets.compare_digest(username, expected_username)
        and secrets.compare_digest(password, expected_password)
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )


def _utcnow():
    return datetime.now(timezone.utc)


def _load_challenge(
    db: Session,
    request_id: str,
    purpose: str,
):
    row = (
        db.query(CloudWebAuthnChallenge)
        .filter(CloudWebAuthnChallenge.id == request_id)
        .first()
    )

    if row is None or row.purpose != purpose:
        raise HTTPException(
            status_code=400,
            detail="Invalid WebAuthn challenge",
        )

    expires_at = row.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= _utcnow():
        db.delete(row)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="WebAuthn challenge expired",
        )

    return row


@app.post("/auth/login")
def login(payload: LoginRequest, response: Response):
    _verify_cloud_credentials(
        payload.username,
        payload.password,
    )
    _set_cloud_session_cookie(response)
    return {"authenticated": True}


@app.get("/auth/webauthn/status")
def cloud_webauthn_status(
    db: Session = Depends(get_db),
):
    return {
        "configured": db.query(CloudPasskey).first() is not None
    }


@app.post("/auth/webauthn/register/options")
def cloud_webauthn_register_options(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    _verify_cloud_credentials(
        payload.username,
        payload.password,
    )

    existing = db.query(CloudPasskey).first()
    exclude_credentials = []

    if existing:
        exclude_credentials.append(
            PublicKeyCredentialDescriptor(
                id=_b64url_decode(existing.credential_id)
            )
        )

    options = generate_registration_options(
        rp_id=CLOUD_RP_ID,
        rp_name=CLOUD_RP_NAME,
        user_id=payload.username.encode("utf-8"),
        user_name=payload.username,
        user_display_name="Hybrid AI Administrator",
        timeout=60000,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=exclude_credentials,
    )

    request_id = str(uuid.uuid4())
    now = _utcnow()

    db.add(
        CloudWebAuthnChallenge(
            id=request_id,
            challenge=_b64url_encode(options.challenge),
            purpose="registration",
            username=payload.username,
            created_at=now,
            expires_at=now + timedelta(
                minutes=WEBAUTHN_CHALLENGE_TTL_MINUTES
            ),
        )
    )
    db.commit()

    return {
        "request_id": request_id,
        "publicKey": json.loads(options_to_json(options)),
    }


@app.post("/auth/webauthn/register/verify")
def cloud_webauthn_register_verify(
    payload: WebAuthnRegistrationVerifyRequest,
    db: Session = Depends(get_db),
):
    _verify_cloud_credentials(
        payload.username,
        payload.password,
    )

    challenge = _load_challenge(
        db,
        payload.request_id,
        "registration",
    )

    if challenge.username != payload.username:
        raise HTTPException(
            status_code=401,
            detail="WebAuthn registration user mismatch",
        )

    try:
        verification = verify_registration_response(
            credential=payload.credential,
            expected_challenge=_b64url_decode(
                challenge.challenge
            ),
            expected_rp_id=CLOUD_RP_ID,
            expected_origin=CLOUD_ORIGIN,
            require_user_verification=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Passkey registration verification failed: {exc}",
        )

    passkey = db.query(CloudPasskey).first()

    if passkey is None:
        passkey = CloudPasskey(
            username=payload.username
        )
        db.add(passkey)

    passkey.username = payload.username
    passkey.credential_id = _b64url_encode(
        verification.credential_id
    )
    passkey.credential_public_key = _b64url_encode(
        verification.credential_public_key
    )
    passkey.sign_count = verification.sign_count

    db.delete(challenge)
    db.commit()

    return {
        "success": True,
        "configured": True,
    }


@app.post("/auth/webauthn/authenticate/options")
def cloud_webauthn_authenticate_options(
    db: Session = Depends(get_db),
):
    passkey = db.query(CloudPasskey).first()

    if passkey is None:
        raise HTTPException(
            status_code=404,
            detail="Cloud Touch ID is not configured",
        )

    options = generate_authentication_options(
        rp_id=CLOUD_RP_ID,
        allow_credentials=[
            PublicKeyCredentialDescriptor(
                id=_b64url_decode(
                    passkey.credential_id
                )
            )
        ],
        timeout=60000,
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    request_id = str(uuid.uuid4())
    now = _utcnow()

    db.add(
        CloudWebAuthnChallenge(
            id=request_id,
            challenge=_b64url_encode(options.challenge),
            purpose="authentication",
            username=passkey.username,
            created_at=now,
            expires_at=now + timedelta(
                minutes=WEBAUTHN_CHALLENGE_TTL_MINUTES
            ),
        )
    )
    db.commit()

    return {
        "request_id": request_id,
        "publicKey": json.loads(options_to_json(options)),
    }


@app.post("/auth/webauthn/authenticate/verify")
def cloud_webauthn_authenticate_verify(
    payload: WebAuthnAuthenticationVerifyRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    challenge = _load_challenge(
        db,
        payload.request_id,
        "authentication",
    )

    passkey = db.query(CloudPasskey).first()

    if passkey is None:
        raise HTTPException(
            status_code=404,
            detail="Cloud Touch ID is not configured",
        )

    try:
        verification = verify_authentication_response(
            credential=payload.credential,
            expected_challenge=_b64url_decode(
                challenge.challenge
            ),
            expected_rp_id=CLOUD_RP_ID,
            expected_origin=CLOUD_ORIGIN,
            credential_public_key=_b64url_decode(
                passkey.credential_public_key
            ),
            credential_current_sign_count=passkey.sign_count,
            require_user_verification=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Touch ID verification failed: {exc}",
        )

    passkey.sign_count = verification.new_sign_count
    db.delete(challenge)
    db.commit()

    _set_cloud_session_cookie(response)
    return {"authenticated": True}


@app.post("/auth/logout")
def cloud_logout(response: Response):
    response.delete_cookie(
        key=CLOUD_SESSION_COOKIE,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return {"authenticated": False}


@app.get("/")
def root():
    return {
        "application": "Hybrid AI Supply Chain Platform",
        "version": "0.1.0"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

Instrumentator().instrument(app).expose(app, endpoint="/metrics")
FastAPIInstrumentor.instrument_app(app)

# On ajoute les routers
app.include_router(health_router)

# En CLOUD, les APIs métier nécessitent une session authentifiée.
# En LOCAL, le comportement de développement reste inchangé.
cloud_api_dependencies = (
    [Depends(require_cloud_session)]
    if os.getenv("CLOUD_AUTH_USERNAME")
    else []
)

app.include_router(
    suppliers_router,
    dependencies=cloud_api_dependencies,
)
app.include_router(
    purchase_orders_router,
    dependencies=cloud_api_dependencies,
)
app.include_router(
    kpis_router,
    dependencies=cloud_api_dependencies,
)
app.include_router(
    ai_router,
    dependencies=cloud_api_dependencies,
)

# Le endpoint de synchronisation possède déjà sa propre
# authentification X-Sync-Key : on conserve ce mécanisme séparé.
app.include_router(sync_router)