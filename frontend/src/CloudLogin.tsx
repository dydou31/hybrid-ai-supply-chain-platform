import { useState } from "react";
import type { FormEvent } from "react";
import { API_URL } from "./config";

type CloudLoginProps = {
  onAuthenticated: () => void;
};

function fromBase64Url(value: string): ArrayBuffer {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding)
    .replace(/-/g, "+")
    .replace(/_/g, "/");

  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);

  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  return bytes.buffer;
}

function toBase64Url(value: ArrayBuffer | null): string | null {
  if (value === null) return null;

  const bytes = new Uint8Array(value);
  let binary = "";

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function serializeAuthenticationCredential(
  credential: PublicKeyCredential,
) {
  const response =
    credential.response as AuthenticatorAssertionResponse;

  return {
    id: credential.id,
    rawId: toBase64Url(credential.rawId),
    type: credential.type,
    response: {
      authenticatorData: toBase64Url(response.authenticatorData),
      clientDataJSON: toBase64Url(response.clientDataJSON),
      signature: toBase64Url(response.signature),
      userHandle: toBase64Url(response.userHandle),
    },
  };
}

function serializeRegistrationCredential(
  credential: PublicKeyCredential,
) {
  const response =
    credential.response as AuthenticatorAttestationResponse;

  return {
    id: credential.id,
    rawId: toBase64Url(credential.rawId),
    type: credential.type,
    response: {
      attestationObject: toBase64Url(response.attestationObject),
      clientDataJSON: toBase64Url(response.clientDataJSON),
    },
  };
}

export default function CloudLogin({
  onAuthenticated,
}: CloudLoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [touchLoading, setTouchLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  function webAuthnAvailable() {
    return (
      "PublicKeyCredential" in window &&
      navigator.credentials !== undefined
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error("Invalid username or password");
      }

      sessionStorage.setItem(
        "hybrid-ai-cloud-auth",
        "true",
      );

      onAuthenticated();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Authentication failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleTouchId() {
    setError("");
    setMessage("");

    if (!webAuthnAvailable()) {
      setError(
        "Touch ID / Passkeys are not supported in this browser",
      );
      return;
    }

    setTouchLoading(true);

    try {
      const optionsResponse = await fetch(
        `${API_URL}/auth/webauthn/authenticate/options`,
        { method: "POST" },
      );

      if (optionsResponse.status === 404) {
        throw new Error(
          "Touch ID is not configured yet. Configure it once below.",
        );
      }

      if (!optionsResponse.ok) {
        throw new Error(
          "Unable to start Touch ID authentication",
        );
      }

      const data = await optionsResponse.json();
      const publicKey = data.publicKey;

      publicKey.challenge = fromBase64Url(
        publicKey.challenge,
      );

      if (publicKey.allowCredentials) {
        publicKey.allowCredentials =
          publicKey.allowCredentials.map(
            (credential: {
              id: string;
              type: PublicKeyCredentialType;
              transports?: AuthenticatorTransport[];
            }) => ({
              ...credential,
              id: fromBase64Url(credential.id),
            }),
          );
      }

      const credential =
        (await navigator.credentials.get({
          publicKey,
        })) as PublicKeyCredential | null;

      if (!credential) {
        throw new Error("Touch ID authentication cancelled");
      }

      const verifyResponse = await fetch(
        `${API_URL}/auth/webauthn/authenticate/verify`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            request_id: data.request_id,
            credential:
              serializeAuthenticationCredential(
                credential,
              ),
          }),
        },
      );

      if (!verifyResponse.ok) {
        const body = await verifyResponse
          .json()
          .catch(() => null);

        throw new Error(
          body?.detail || "Touch ID verification failed",
        );
      }

      sessionStorage.setItem(
        "hybrid-ai-cloud-auth",
        "true",
      );

      onAuthenticated();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Touch ID authentication failed",
      );
    } finally {
      setTouchLoading(false);
    }
  }

  async function handleConfigureTouchId() {
    setError("");
    setMessage("");

    if (!username || !password) {
      setError(
        "Enter your username and password first to configure Touch ID.",
      );
      return;
    }

    if (!webAuthnAvailable()) {
      setError(
        "Touch ID / Passkeys are not supported in this browser",
      );
      return;
    }

    setTouchLoading(true);

    try {
      const optionsResponse = await fetch(
        `${API_URL}/auth/webauthn/register/options`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username,
            password,
          }),
        },
      );

      if (!optionsResponse.ok) {
        const body = await optionsResponse
          .json()
          .catch(() => null);

        throw new Error(
          body?.detail ||
            "Unable to configure Touch ID",
        );
      }

      const data = await optionsResponse.json();
      const publicKey = data.publicKey;

      publicKey.challenge = fromBase64Url(
        publicKey.challenge,
      );

      publicKey.user.id = fromBase64Url(
        publicKey.user.id,
      );

      if (publicKey.excludeCredentials) {
        publicKey.excludeCredentials =
          publicKey.excludeCredentials.map(
            (credential: {
              id: string;
              type: PublicKeyCredentialType;
              transports?: AuthenticatorTransport[];
            }) => ({
              ...credential,
              id: fromBase64Url(credential.id),
            }),
          );
      }

      const credential =
        (await navigator.credentials.create({
          publicKey,
        })) as PublicKeyCredential | null;

      if (!credential) {
        throw new Error(
          "Touch ID configuration cancelled",
        );
      }

      const verifyResponse = await fetch(
        `${API_URL}/auth/webauthn/register/verify`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            request_id: data.request_id,
            username,
            password,
            credential:
              serializeRegistrationCredential(
                credential,
              ),
          }),
        },
      );

      if (!verifyResponse.ok) {
        const body = await verifyResponse
          .json()
          .catch(() => null);

        throw new Error(
          body?.detail ||
            "Touch ID configuration failed",
        );
      }

      setMessage("Touch ID configured for CLOUD");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Touch ID configuration failed",
      );
    } finally {
      setTouchLoading(false);
    }
  }

  return (
    <main className="cloud-login-page">
      <div className="cloud-login-glow cloud-login-glow-one" />
      <div className="cloud-login-glow cloud-login-glow-two" />

      <section className="cloud-login-card">
        <div className="cloud-login-brand">
          <div className="cloud-login-logo">⚡</div>

          <div>
            <div className="cloud-login-brand-name">
              HYBRID AI
            </div>

            <div className="cloud-login-brand-subtitle">
              SUPPLY CHAIN PLATFORM
            </div>
          </div>
        </div>

        <div className="cloud-login-badge">
          CLOUD
        </div>

        <div className="cloud-login-heading">
          <h1>CLOUD ACCESS</h1>
          <p>Secure access to your AI workspace</p>
        </div>

        <form
          className="cloud-login-form"
          onSubmit={handleSubmit}
        >
          <label>
            <span>Username</span>

            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) =>
                setUsername(event.target.value)
              }
              placeholder="Enter your username"
              required
            />
          </label>

          <label>
            <span>Password</span>

            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
              required
            />
          </label>

          {error && (
            <div className="cloud-login-error">
              {error}
            </div>
          )}

          {message && (
            <div className="cloud-login-success">
              {message}
            </div>
          )}

          <button
            className="cloud-login-primary"
            type="submit"
            disabled={loading || touchLoading}
          >
            {loading
              ? "AUTHENTICATING..."
              : "SIGN IN"}
          </button>
        </form>

        <div className="cloud-login-separator">
          <span />
          <small>OR</small>
          <span />
        </div>

        <button
          className="cloud-login-touchid"
          type="button"
          onClick={handleTouchId}
          disabled={loading || touchLoading}
        >
          <span className="cloud-login-fingerprint">
            ◎
          </span>

          {touchLoading
            ? "WAITING FOR TOUCH ID..."
            : "CONTINUE WITH TOUCH ID"}
        </button>

        <button
          className="cloud-login-touchid-setup"
          type="button"
          onClick={handleConfigureTouchId}
          disabled={loading || touchLoading}
        >
          Configure Touch ID
        </button>

        <div className="cloud-login-security">
          <span>◆</span>
          Secured Cloud Access
        </div>

        <footer className="cloud-login-footer">
          Created by <strong>Dylan TAÏBI</strong>
        </footer>
      </section>
    </main>
  );
}
