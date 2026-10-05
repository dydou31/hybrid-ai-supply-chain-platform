import { useEffect, useState } from "react";
import {
  SiDocker,
  SiFastapi,
  SiGrafana,
  SiHelm,
  SiKubernetes,
  SiPostgresql,
  SiPrometheus,
  SiReact,
  SiRedis,
  SiTerraform,
} from "react-icons/si";
import { FaAws, FaRobot, FaGithub, FaProjectDiagram } from "react-icons/fa";
import { VscPulse } from "react-icons/vsc";
import { API_URL, IS_AWS } from "./config";

type ServiceHealth = {
  status: string;
  postgres?: string;
  pgvector?: string;
  ollama?: string;
  model?: string;
  model_ready?: boolean;
};

type PlatformHealth = {
  status: string;
  services: Record<string, ServiceHealth>;
};

type DockerServiceStatus = {
  state: string;
  health: string;
  status: string;
  running: boolean;
};

type DockerServicesStatus = {
  services: Record<string, DockerServiceStatus>;
};

type NodeStatus = "live" | "down" | "starting" | "stopping" | "architecture";

type ServiceAction = "start" | "stop";

type PasskeyStatus = {
  configured: boolean;
  rp_id: string;
};

const CONTROL_AGENT_URL = "http://127.0.0.1:8100";

function base64urlToUint8Array(value: string) {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  const binary = window.atob(base64);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

function arrayBufferToBase64url(value: ArrayBuffer) {
  const bytes = new Uint8Array(value);
  let binary = "";

  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });

  return window
    .btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function prepareRegistrationOptions(
  publicKey: any,
): PublicKeyCredentialCreationOptions {
  return {
    ...publicKey,
    challenge: base64urlToUint8Array(publicKey.challenge),
    user: { ...publicKey.user, id: base64urlToUint8Array(publicKey.user.id) },
    excludeCredentials: (publicKey.excludeCredentials ?? []).map(
      (credential: any) => ({
        ...credential,
        id: base64urlToUint8Array(credential.id),
      }),
    ),
  };
}

function prepareAuthenticationOptions(
  publicKey: any,
): PublicKeyCredentialRequestOptions {
  return {
    ...publicKey,
    challenge: base64urlToUint8Array(publicKey.challenge),
    allowCredentials: (publicKey.allowCredentials ?? []).map(
      (credential: any) => ({
        ...credential,
        id: base64urlToUint8Array(credential.id),
      }),
    ),
  };
}

function registrationCredentialToJSON(credential: PublicKeyCredential) {
  const response = credential.response as AuthenticatorAttestationResponse;
  return {
    id: credential.id,
    rawId: arrayBufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: arrayBufferToBase64url(response.clientDataJSON),
      attestationObject: arrayBufferToBase64url(response.attestationObject),
      transports:
        typeof response.getTransports === "function"
          ? response.getTransports()
          : [],
    },
    clientExtensionResults: credential.getClientExtensionResults(),
    authenticatorAttachment: credential.authenticatorAttachment,
  };
}

function authenticationCredentialToJSON(credential: PublicKeyCredential) {
  const response = credential.response as AuthenticatorAssertionResponse;
  return {
    id: credential.id,
    rawId: arrayBufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      clientDataJSON: arrayBufferToBase64url(response.clientDataJSON),
      authenticatorData: arrayBufferToBase64url(response.authenticatorData),
      signature: arrayBufferToBase64url(response.signature),
      userHandle: response.userHandle
        ? arrayBufferToBase64url(response.userHandle)
        : null,
    },
    clientExtensionResults: credential.getClientExtensionResults(),
    authenticatorAttachment: credential.authenticatorAttachment,
  };
}

type ControllableService =
  "api" | "db" | "redis" | "prometheus" | "tempo" | "grafana";

type ArchitectureNode = {
  id: string;
  name: string;
  subtitle: string;
  group: "application" | "data" | "ai" | "delivery" | "observability";
  healthKey?: string;
  icon: React.ReactNode;
  description: string;
};

type ArchitectureNodeProps = {
  id: string;
  nodes: ArchitectureNode[];
  platform: PlatformHealth | null;
  dockerServices: DockerServicesStatus | null;
  selected: string;
  onSelect: (id: string) => void;
};

function ArchitectureNodeCard({
  id,
  nodes,
  platform,
  dockerServices,
  selected,
  onSelect,
}: ArchitectureNodeProps) {
  const node = nodes.find((item) => item.id === id);

  if (!node) return null;

  let status: NodeStatus;

  const dockerServiceByNode: Partial<Record<string, string>> = {
    fastapi: "api",
    postgres: "db",
    pgvector: "pgvector",
    redis: "redis",
    ollama: "ollama",
    prometheus: "prometheus",
    tempo: "tempo",
    grafana: "grafana",
  };

  const dockerService = dockerServiceByNode[node.id];
  const dockerState = dockerService
    ? dockerServices?.services?.[dockerService]
    : undefined;

  if (dockerState) {
    status = dockerState.running ? "live" : "down";
  } else if (!node.healthKey) {
    status = "architecture";
  } else if (!platform) {
    status = "down";
  } else {
    status =
      platform.services[node.healthKey]?.status === "healthy" ? "live" : "down";
  }

  return (
    <button
      type="button"
      className={`architecture-node architecture-${status} ${
        selected === id ? "architecture-selected" : ""
      }`}
      onClick={() => onSelect(id)}
    >
      <span className="architecture-node-icon">{node.icon}</span>

      <span className="architecture-node-copy">
        <strong>{node.name}</strong>
        <small>{node.subtitle}</small>
      </span>

      <span className={`architecture-node-status ${status}`}>
        <span className="status-dot" />

        {status === "live"
          ? "Live"
          : status === "down"
            ? "Unavailable"
            : "Architecture"}
      </span>
    </button>
  );
}

function Platform() {
  const [platform, setPlatform] = useState<PlatformHealth | null>(null);
  const [dockerServices, setDockerServices] =
    useState<DockerServicesStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState("fastapi");

  const [serviceTransitions, setServiceTransitions] = useState<
    Partial<Record<ControllableService, "starting" | "stopping">>
  >({});

  const [pendingAction, setPendingAction] = useState<{
    service: ControllableService;
    action: ServiceAction;
  } | null>(null);

  const [adminPassword, setAdminPassword] = useState("");
  const [actionError, setActionError] = useState("");
  const [passkeyStatus, setPasskeyStatus] = useState<PasskeyStatus | null>(
    null,
  );
  const [passkeyBusy, setPasskeyBusy] = useState(false);

  const loadPasskeyStatus = async () => {
    try {
      const response = await fetch(`${CONTROL_AGENT_URL}/webauthn/status`);
      if (!response.ok) throw new Error("Passkey status request failed");
      const data: PasskeyStatus = await response.json();
      setPasskeyStatus(data);
    } catch {
      setPasskeyStatus(null);
    }
  };

  const loadHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health/platform`);

      if (!response.ok) {
        throw new Error("Platform health request failed");
      }

      const data: PlatformHealth = await response.json();
      setPlatform(data);
    } catch {
      setPlatform(null);
    } finally {
      setLoading(false);
    }
  };

  const loadDockerStatus = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8100/services/status");

      if (!response.ok) {
        throw new Error("Docker service status request failed");
      }

      const data: DockerServicesStatus = await response.json();
      setDockerServices(data);
    } catch {
      setDockerServices(null);
    }
  };

  useEffect(() => {
    loadHealth();

    const healthInterval = window.setInterval(loadHealth, 10000);

    if (IS_AWS) {
      return () => {
        window.clearInterval(healthInterval);
      };
    }

    loadDockerStatus();
    loadPasskeyStatus();

    const dockerInterval = window.setInterval(loadDockerStatus, 1000);

    return () => {
      window.clearInterval(healthInterval);
      window.clearInterval(dockerInterval);
    };
  }, []);

  const executeServiceAction = async () => {
    if (!pendingAction || !adminPassword) return;

    const { service, action } = pendingAction;

    const transition = action === "start" ? "starting" : "stopping";

    setActionError("");

    setServiceTransitions((current) => ({
      ...current,
      [service]: transition,
    }));

    try {
      const response = await fetch(
        `http://127.0.0.1:8100/services/${service}/${action}`,
        {
          method: "POST",
          headers: {
            "X-Admin-Password": adminPassword,
          },
        },
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Invalid administrator password");
        }

        throw new Error("Service operation failed");
      }

      setPendingAction(null);
      setAdminPassword("");

      await new Promise((resolve) => window.setTimeout(resolve, 1000));

      await loadHealth();
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : "Service operation failed",
      );
    } finally {
      setServiceTransitions((current) => {
        const next = { ...current };

        delete next[service];

        return next;
      });
    }
  };

  const setupPasskey = async () => {
    if (!adminPassword || passkeyBusy) return;
    if (!window.PublicKeyCredential || !navigator.credentials) {
      setActionError("WebAuthn is not supported by this browser");
      return;
    }
    setPasskeyBusy(true);
    setActionError("");
    try {
      const optionsResponse = await fetch(
        `${CONTROL_AGENT_URL}/webauthn/register/options`,
        {
          method: "POST",
          headers: { "X-Admin-Password": adminPassword },
        },
      );
      if (!optionsResponse.ok) {
        if (optionsResponse.status === 401)
          throw new Error("Invalid administrator password");
        const errorData = await optionsResponse.json().catch(() => null);
        throw new Error(errorData?.detail ?? "Unable to start Touch ID setup");
      }
      const optionsData = await optionsResponse.json();
      const credential = (await navigator.credentials.create({
        publicKey: prepareRegistrationOptions(optionsData.publicKey),
      })) as PublicKeyCredential | null;
      if (!credential) throw new Error("Touch ID setup was cancelled");
      const verifyResponse = await fetch(
        `${CONTROL_AGENT_URL}/webauthn/register/verify`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Admin-Password": adminPassword,
          },
          body: JSON.stringify({
            request_id: optionsData.request_id,
            credential: registrationCredentialToJSON(credential),
          }),
        },
      );
      if (!verifyResponse.ok) {
        const errorData = await verifyResponse.json().catch(() => null);
        throw new Error(errorData?.detail ?? "Touch ID setup failed");
      }
      await loadPasskeyStatus();
      setAdminPassword("");
      setActionError("");
    } catch (error) {
      if (error instanceof DOMException && error.name === "NotAllowedError") {
        setActionError("Touch ID / Passkey setup was cancelled");
      } else {
        setActionError(
          error instanceof Error ? error.message : "Touch ID setup failed",
        );
      }
    } finally {
      setPasskeyBusy(false);
    }
  };

  const executePasskeyAction = async () => {
    if (!pendingAction || passkeyBusy) return;
    if (!window.PublicKeyCredential || !navigator.credentials) {
      setActionError("WebAuthn is not supported by this browser");
      return;
    }
    const { service, action } = pendingAction;
    const transition = action === "start" ? "starting" : "stopping";
    setPasskeyBusy(true);
    setActionError("");
    try {
      const optionsResponse = await fetch(
        `${CONTROL_AGENT_URL}/webauthn/authenticate/options`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ service, action }),
        },
      );
      if (!optionsResponse.ok) {
        const errorData = await optionsResponse.json().catch(() => null);
        throw new Error(
          errorData?.detail ?? "Unable to start Touch ID authentication",
        );
      }
      const optionsData = await optionsResponse.json();
      const credential = (await navigator.credentials.get({
        publicKey: prepareAuthenticationOptions(optionsData.publicKey),
      })) as PublicKeyCredential | null;
      if (!credential) throw new Error("Touch ID authentication was cancelled");
      setServiceTransitions((current) => ({
        ...current,
        [service]: transition,
      }));
      const verifyResponse = await fetch(
        `${CONTROL_AGENT_URL}/webauthn/authenticate/verify`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: optionsData.request_id,
            credential: authenticationCredentialToJSON(credential),
          }),
        },
      );
      if (!verifyResponse.ok) {
        const errorData = await verifyResponse.json().catch(() => null);
        throw new Error(errorData?.detail ?? "Touch ID authentication failed");
      }
      setPendingAction(null);
      setAdminPassword("");
      await new Promise((resolve) => window.setTimeout(resolve, 1000));
      await Promise.all([loadHealth(), loadDockerStatus()]);
    } catch (error) {
      if (error instanceof DOMException && error.name === "NotAllowedError") {
        setActionError("Touch ID / Passkey authentication was cancelled");
      } else {
        setActionError(
          error instanceof Error
            ? error.message
            : "Touch ID authentication failed",
        );
      }
    } finally {
      setServiceTransitions((current) => {
        const next = { ...current };
        delete next[service];
        return next;
      });
      setPasskeyBusy(false);
    }
  };

  const localNodes: ArchitectureNode[] = [
    {
      id: "react",
      name: "React",
      subtitle: "TypeScript + Vite",
      group: "application",
      icon: <SiReact />,
      description:
        "Interactive frontend for dashboards, suppliers, AI and platform operations.",
    },
    {
      id: "fastapi",
      name: "FastAPI",
      subtitle: "REST API",
      group: "application",
      icon: <SiFastapi />,
      description:
        "Core backend exposing business, AI and platform health APIs.",
    },
    {
      id: "postgres",
      name: "PostgreSQL",
      subtitle: "Operational data",
      group: "data",
      healthKey: "postgres",
      icon: <SiPostgresql />,
      description:
        "Primary relational database for suppliers, purchase orders and application data.",
    },
    {
      id: "pgvector",
      name: "pgvector",
      subtitle: "Vector storage",
      group: "ai",
      healthKey: "postgres",
      icon: <FaProjectDiagram />,
      description:
        "PostgreSQL vector extension used for semantic knowledge retrieval.",
    },
    {
      id: "redis",
      name: "Redis",
      subtitle: "Cache",
      group: "data",
      healthKey: "redis",
      icon: <SiRedis />,
      description: "Low-latency cache and fast data access layer.",
    },
    {
      id: "hybrid-ai",
      name: "Hybrid AI",
      subtitle: "Structured + RAG",
      group: "ai",
      icon: <FaProjectDiagram />,
      description:
        "Combines structured supply-chain retrieval with semantic RAG context.",
    },
    {
      id: "ollama",
      name: "Ollama / Llama",
      subtitle: "Local inference",
      group: "ai",
      healthKey: "ollama",
      icon: <FaRobot />,
      description:
        "Local LLM inference layer running the Llama model used by the AI Assistant.",
    },
    {
      id: "github",
      name: "GitHub Actions",
      subtitle: "CI/CD",
      group: "delivery",
      icon: <FaGithub />,
      description: "Continuous integration pipeline validating the project.",
    },
    {
      id: "docker",
      name: "Docker",
      subtitle: "Containers",
      group: "delivery",
      icon: <SiDocker />,
      description:
        "Containerization of the application and supporting services.",
    },
    {
      id: "kubernetes",
      name: "Kubernetes",
      subtitle: "Orchestration",
      group: "delivery",
      icon: <SiKubernetes />,
      description:
        "Container orchestration layer demonstrated locally with Kubernetes.",
    },
    {
      id: "helm",
      name: "Helm",
      subtitle: "K8s packaging",
      group: "delivery",
      icon: <SiHelm />,
      description: "Reusable Kubernetes deployment configuration.",
    },
    {
      id: "terraform",
      name: "Terraform",
      subtitle: "Infrastructure as Code",
      group: "delivery",
      icon: <SiTerraform />,
      description: "Declarative infrastructure provisioning.",
    },
    {
      id: "aws",
      name: "AWS",
      subtitle: "ECR + ECS/Fargate",
      group: "delivery",
      icon: <FaAws />,
      description: "Cloud deployment demonstration using ECR and ECS Fargate.",
    },
    {
      id: "otel",
      name: "OpenTelemetry",
      subtitle: "Instrumentation",
      group: "observability",
      icon: <VscPulse />,
      description: "Application telemetry instrumentation and trace export.",
    },
    {
      id: "prometheus",
      name: "Prometheus",
      subtitle: "Metrics",
      group: "observability",
      healthKey: "prometheus",
      icon: <SiPrometheus />,
      description: "Metrics collection for platform observability.",
    },
    {
      id: "tempo",
      name: "Tempo",
      subtitle: "Tracing",
      group: "observability",
      healthKey: "tempo",
      icon: <VscPulse />,
      description:
        "Distributed tracing backend receiving OpenTelemetry traces.",
    },
    {
      id: "grafana",
      name: "Grafana",
      subtitle: "Visualization",
      group: "observability",
      healthKey: "grafana",
      icon: <SiGrafana />,
      description: "Dashboards for metrics and observability data.",
    },
  ];

  const awsNodes: ArchitectureNode[] = [
    {
      id: "cloudfront",
      name: "CloudFront",
      subtitle: "HTTPS + CDN",
      group: "application",
      icon: <FaAws />,
      description:
        "Public HTTPS entry point serving the React frontend and routing API traffic to the AWS backend.",
    },
    {
      id: "alb",
      name: "Application Load Balancer",
      subtitle: "Traffic distribution",
      group: "application",
      icon: <FaAws />,
      description:
        "Distributes API traffic across healthy ECS Fargate tasks.",
    },
    {
      id: "fastapi",
      name: "ECS / Fargate",
      subtitle: "FastAPI ×2",
      group: "application",
      icon: <SiFastapi />,
      description:
        "Highly available FastAPI backend running as two ECS Fargate tasks with automatic recovery.",
    },
    {
      id: "postgres",
      name: "Amazon RDS",
      subtitle: "PostgreSQL",
      group: "data",
      healthKey: "postgres",
      icon: <SiPostgresql />,
      description:
        "Private managed PostgreSQL database storing operational supply-chain data.",
    },
    {
      id: "pgvector",
      name: "pgvector",
      subtitle: "Vector search",
      group: "data",
      healthKey: "postgres",
      icon: <FaProjectDiagram />,
      description:
        "Vector extension inside Amazon RDS used for semantic retrieval and RAG.",
    },
    {
      id: "redis",
      name: "Amazon Valkey",
      subtitle: "ElastiCache",
      group: "data",
      healthKey: "redis",
      icon: <SiRedis />,
      description:
        "Private managed cache used by the cloud application.",
    },
    {
      id: "bedrock",
      name: "Amazon Bedrock",
      subtitle: "Nova Micro",
      group: "ai",
      icon: <FaRobot />,
      description:
        "Managed cloud inference using Amazon Nova Micro through the ECS Task Role.",
    },
    {
      id: "ecr",
      name: "Amazon ECR",
      subtitle: "Container Registry",
      group: "delivery",
      icon: <FaAws />,
      description:
        "Stores the Docker images deployed to ECS Fargate.",
    },
    {
      id: "terraform",
      name: "Terraform",
      subtitle: "Infrastructure as Code",
      group: "delivery",
      icon: <SiTerraform />,
      description:
        "Versioned Infrastructure as Code for AWS networking, compute, data and observability resources.",
    },
    {
      id: "amp",
      name: "Amazon Managed Prometheus",
      subtitle: "Metrics",
      group: "observability",
      icon: <SiPrometheus />,
      description:
        "Managed Prometheus workspace receiving application metrics through ADOT.",
    },
    {
      id: "cloudwatch",
      name: "CloudWatch",
      subtitle: "Logs + Monitoring",
      group: "observability",
      icon: <VscPulse />,
      description:
        "Central AWS logging and operational monitoring for the cloud platform.",
    },
    {
      id: "grafana",
      name: "Grafana ECS",
      subtitle: "Visualization",
      group: "observability",
      icon: <SiGrafana />,
      description:
        "Grafana running on ECS and visualizing cloud metrics from Amazon Managed Prometheus.",
    },
    {
      id: "otel",
      name: "OpenTelemetry / ADOT",
      subtitle: "Telemetry pipeline",
      group: "observability",
      icon: <VscPulse />,
      description:
        "Collects and exports application telemetry to AWS observability services.",
    },
  ];

  const nodes: ArchitectureNode[] = IS_AWS ? awsNodes : localNodes;

  const controllableServices: Partial<Record<string, ControllableService>> = IS_AWS
    ? {}
    : {
        fastapi: "api",
        postgres: "db",
        redis: "redis",
        prometheus: "prometheus",
        tempo: "tempo",
        grafana: "grafana",
      };

  const getStatus = (node: ArchitectureNode): NodeStatus => {
    if (IS_AWS) {
      if (!node.healthKey) {
        return "architecture";
      }

      if (!platform) {
        return "down";
      }

      return platform.services[node.healthKey]?.status === "healthy"
        ? "live"
        : "down";
    }

    const statusServiceByNode: Partial<Record<string, string>> = {
      fastapi: "api",
      postgres: "db",
      pgvector: "pgvector",
      redis: "redis",
      ollama: "ollama",
      prometheus: "prometheus",
      tempo: "tempo",
      grafana: "grafana",
    };

    const statusService = statusServiceByNode[node.id];

    if (statusService && dockerServices) {
      return dockerServices.services[statusService]?.running ? "live" : "down";
    }

    if (!node.healthKey) {
      return "architecture";
    }

    if (!platform) {
      return "down";
    }

    return platform.services[node.healthKey]?.status === "healthy"
      ? "live"
      : "down";
  };

  const selectedNode = nodes.find((node) => node.id === selected) ?? nodes[0];

  const selectedService = controllableServices[selectedNode.id];

  const selectedStatus: NodeStatus =
    selectedService && serviceTransitions[selectedService]
      ? serviceTransitions[selectedService]!
      : getStatus(selectedNode);

  const healthyCount = platform
    ? Object.values(platform.services).filter(
        (service) => service.status === "healthy",
      ).length
    : 0;

  return (
    <section className="platform-page architecture-control-center">
      <div className="section-heading">
        <div>
          <p className="eyebrow">AI PLATFORM ENGINEERING</p>

          <h3>Interactive Architecture Control Center</h3>

          <p>
            Explore the application, Hybrid AI, delivery and observability
            architecture. Live services are connected to the FastAPI platform
            health endpoint.
          </p>
        </div>

        <div
          className={`platform-overall ${
            platform?.status === "healthy" ? "healthy" : "degraded"
          }`}
        >
          <span className="status-dot" />

          {loading
            ? "Checking platform..."
            : platform?.status === "healthy"
              ? "All Systems Operational"
              : "Platform Degraded"}
        </div>
      </div>

      <div className="platform-summary">
        <div className="card platform-stat">
          <span>Live Services</span>

          <strong>
            {healthyCount}
            {!IS_AWS && <small> / 6</small>}
          </strong>
        </div>

        <div className="card platform-stat">
          <span>Vector Database</span>

          <strong>
            {IS_AWS
              ? platform?.services.postgres?.status === "healthy"
                ? "Enabled"
                : "Unavailable"
              : dockerServices?.services.pgvector?.running
                ? "Enabled"
                : "Unavailable"}
          </strong>
        </div>

        <div className="card platform-stat">
          <span>LLM Model</span>

          <strong>
            {IS_AWS
              ? "Amazon Nova Micro"
              : dockerServices?.services.ollama?.running
                ? "llama3.2:3b"
                : "Unavailable"}
          </strong>
        </div>

        <div className="card platform-stat">
          <span>Service Status</span>
          <strong>{IS_AWS ? "10s" : "1s"}</strong>
        </div>
      </div>

      <div className="architecture-toolbar">
        <div className="architecture-legend">
          <span>
            <i className="legend-live" /> Live monitored
          </span>

          <span>
            <i className="legend-architecture" /> Architecture component
          </span>

          <span>
            <i className="legend-down" /> Unavailable
          </span>
        </div>

        <button type="button" onClick={loadHealth}>
          Refresh health
        </button>
      </div>

      {!platform && !loading && (
        <div className="platform-error">
          FastAPI health endpoint is currently unreachable. Architecture
          components remain available for exploration.
        </div>
      )}

      <div className={`architecture-layout${!IS_AWS ? " local-architecture-layout" : ""}`}>
        <div className={`architecture-canvas${IS_AWS ? " aws-architecture" : ""}`}>
          {IS_AWS ? (
            <>
          <div className="architecture-zone architecture-zone-app">
            <div className="architecture-zone-title">
              <span>01</span>
              APPLICATION
            </div>

            <div className="architecture-layout">
              <ArchitectureNodeCard
                id="cloudfront"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard
                id="alb"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard
                id="fastapi"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>
          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>02</span>
              DATA &amp; HYBRID AI
            </div>

            <div className="architecture-data-ai">
              <div className="architecture-data-stack">
                <ArchitectureNodeCard
                  id="postgres"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
                <ArchitectureNodeCard
                  id="pgvector"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
              </div>

              <span className="pipeline-arrow">→</span>

              <div className="architecture-data-stack">
                <ArchitectureNodeCard
                  id="redis"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
                <ArchitectureNodeCard
                  id="hybrid-ai"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
              </div>

              <span className="pipeline-arrow">→</span>

              <ArchitectureNodeCard
                id="bedrock"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>
          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>03</span>
              PLATFORM DELIVERY
            </div>

            <div className="architecture-delivery">
              <ArchitectureNodeCard
                id="terraform"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard
                id="ecr"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard
                id="fastapi"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>
          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>04</span>
              OBSERVABILITY
            </div>

            <div className="architecture-observability">
              <ArchitectureNodeCard
                id="otel"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
              <span className="pipeline-arrow">→</span>

              <div className="architecture-observability-split">
                <ArchitectureNodeCard
                  id="amp"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
                <ArchitectureNodeCard
                  id="cloudwatch"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
              </div>

              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard
                id="grafana"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>
            </>
          ) : (
            <>
          <div className="architecture-zone architecture-zone-app">
            <div className="architecture-zone-title">
              <span>01</span>
              APPLICATION
            </div>

            <div className="architecture-flow architecture-flow-main">
              <ArchitectureNodeCard
                id="react"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />

              <div className="architecture-link">
                <span>REST</span>
                <b>→</b>
              </div>

              <ArchitectureNodeCard
                id="fastapi"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>

          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>02</span>
              DATA & HYBRID AI
            </div>

            <div className="architecture-ai-grid">
              <div className="architecture-stack">
                <ArchitectureNodeCard
                  id="postgres"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />

                <div className="architecture-vertical-link">
                  <span>vector extension</span>↓
                </div>

                <ArchitectureNodeCard
                  id="pgvector"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
              </div>

              <div className="architecture-middle-links">
                <span>SQL / cache</span>
                <b>⇄</b>
              </div>

              <div className="architecture-stack">
                <ArchitectureNodeCard
                  id="redis"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />

                <div className="architecture-vertical-link">
                  <span>context</span>↓
                </div>

                <ArchitectureNodeCard
                  id="hybrid-ai"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
              </div>

              <div className="architecture-middle-links">
                <span>RAG</span>
                <b>→</b>
              </div>

              <ArchitectureNodeCard
                id="ollama"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>

          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>03</span>
              PLATFORM DELIVERY
            </div>

            <div className="architecture-delivery">
              <ArchitectureNodeCard
                id="github"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />

              <span className="pipeline-arrow">→</span>

              <ArchitectureNodeCard
                id="docker"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />

              <span className="pipeline-arrow">→</span>

              <ArchitectureNodeCard
                id="kubernetes"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />

              <span className="pipeline-arrow">→</span>

              <ArchitectureNodeCard
                id="helm"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />

              <span className="pipeline-arrow">→</span>

              <ArchitectureNodeCard
                id="terraform"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />

              <span className="pipeline-arrow">→</span>

              <ArchitectureNodeCard
                id="aws"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>

          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>04</span>
              OBSERVABILITY
            </div>

            <div className="architecture-observability">
              <ArchitectureNodeCard
                id="otel"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />

              <span className="pipeline-arrow">→</span>

              <div className="architecture-observability-split">
                <ArchitectureNodeCard
                  id="prometheus"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />

                <ArchitectureNodeCard
                  id="tempo"
                  nodes={nodes}
                  platform={platform}
                  dockerServices={dockerServices}
                  selected={selected}
                  onSelect={setSelected}
                />
              </div>

              <span className="pipeline-arrow">→</span>

              <ArchitectureNodeCard
                id="grafana"
                nodes={nodes}
                platform={platform}
                dockerServices={dockerServices}
                selected={selected}
                onSelect={setSelected}
              />
            </div>
          </div>

            </>
          )}
        </div>

        <aside className="architecture-inspector card">
          <p className="eyebrow">COMPONENT INSPECTOR</p>

          <div className="inspector-heading">
            <span className="inspector-icon">{selectedNode.icon}</span>

            <div>
              <h3>{selectedNode.name}</h3>
              <span>{selectedNode.subtitle}</span>
            </div>
          </div>

          <div className={`inspector-status ${selectedStatus}`}>
            <span className="status-dot" />

            {selectedStatus === "live"
              ? "Live monitored service"
              : selectedStatus === "down"
                ? "Service unavailable"
                : selectedStatus === "starting"
                  ? "Service starting..."
                  : selectedStatus === "stopping"
                    ? "Service stopping..."
                    : "Architecture component"}
          </div>

          <p className="inspector-description">{selectedNode.description}</p>

          <div className="inspector-meta">
            <div>
              <span>Layer</span>
              <strong>{selectedNode.group}</strong>
            </div>

            <div>
              <span>Monitoring</span>

              <strong>
                {selectedNode.healthKey ? "Live API health" : "Architecture"}
              </strong>
            </div>

            {selectedNode.id === "postgres" && (
              <>
                <div>
                  <span>PostgreSQL</span>

                  <strong>
                    {platform?.services.postgres?.postgres ?? "Unknown"}
                  </strong>
                </div>

                <div>
                  <span>pgvector</span>

                  <strong>
                    {platform?.services.postgres?.pgvector ?? "Unknown"}
                  </strong>
                </div>
              </>
            )}

            {selectedNode.id === "pgvector" && (
              <div>
                <span>Extension</span>

                <strong>
                  {dockerServices?.services.pgvector?.running
                    ? "enabled"
                    : "Unavailable"}
                </strong>
              </div>
            )}

            {selectedNode.id === "ollama" && (
              <>
                <div>
                  <span>Runtime</span>

                  <strong>
                    {dockerServices?.services.ollama?.running
                      ? "running"
                      : "Unavailable"}
                  </strong>
                </div>

                <div>
                  <span>Model</span>

                  <strong>
                    {dockerServices?.services.ollama?.running
                      ? "llama3.2:3b"
                      : "Unavailable"}
                  </strong>
                </div>
              </>
            )}
          </div>

          {selectedService && (
            <div className="inspector-control">
              <div>
                <span>Service Control</span>
                <small>Administrator authentication required</small>
              </div>

              <button
                type="button"
                className={`service-control-button ${
                  selectedStatus === "live"
                    ? "service-control-off"
                    : selectedStatus === "down"
                      ? "service-control-on"
                      : "service-control-transition"
                }`}
                disabled={
                  selectedStatus === "starting" || selectedStatus === "stopping"
                }
                onClick={() => {
                  setActionError("");
                  setAdminPassword("");
                  setPendingAction({
                    service: selectedService,
                    action: selectedStatus === "live" ? "stop" : "start",
                  });
                }}
              >
                {selectedStatus === "starting"
                  ? "STARTING..."
                  : selectedStatus === "stopping"
                    ? "STOPPING..."
                    : selectedStatus === "live"
                      ? "TURN OFF"
                      : "TURN ON"}
              </button>
            </div>
          )}

          <div className="inspector-note">
            Click any technology in the architecture to inspect its role and
            live status when monitoring is available.
          </div>

          {pendingAction && (
            <div
              className="control-modal-backdrop"
              role="presentation"
              onMouseDown={(event) => {
                if (event.target === event.currentTarget) {
                  setPendingAction(null);
                  setAdminPassword("");
                  setActionError("");
                }
              }}
            >
              <div
                className="control-modal card"
                role="dialog"
                aria-modal="true"
                aria-labelledby="control-modal-title"
              >
                <p className="eyebrow">ADMINISTRATOR AUTHENTICATION</p>

                <h3 id="control-modal-title">
                  {pendingAction.action === "stop"
                    ? "Turn off service?"
                    : "Turn on service?"}
                </h3>

                <p>
                  Authentication is required before changing the state of this
                  platform service.
                </p>

                <label htmlFor="control-admin-password">
                  Administrator password
                </label>

                <input
                  id="control-admin-password"
                  type="password"
                  autoComplete="current-password"
                  autoFocus
                  value={adminPassword}
                  onChange={(event) => {
                    setAdminPassword(event.target.value);
                    setActionError("");
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && adminPassword) {
                      void executeServiceAction();
                    }
                  }}
                  placeholder="Enter administrator password"
                />

                {actionError && (
                  <div className="control-modal-error">{actionError}</div>
                )}

                <button
                  type="button"
                  className="service-control-button service-control-on"
                  disabled={
                    passkeyBusy ||
                    (!passkeyStatus?.configured && !adminPassword)
                  }
                  onClick={() => {
                    if (passkeyStatus?.configured) {
                      void executePasskeyAction();
                    } else {
                      void setupPasskey();
                    }
                  }}
                >
                  {passkeyBusy
                    ? "WAITING FOR TOUCH ID..."
                    : passkeyStatus?.configured
                      ? "AUTHENTICATE WITH TOUCH ID"
                      : "SET UP TOUCH ID"}
                </button>

                <div className="control-modal-actions">
                  <button
                    type="button"
                    onClick={() => {
                      setPendingAction(null);
                      setAdminPassword("");
                      setActionError("");
                    }}
                  >
                    Cancel
                  </button>

                  <button
                    type="button"
                    disabled={!adminPassword}
                    onClick={() => void executeServiceAction()}
                  >
                    Authenticate &{" "}
                    {pendingAction.action === "stop" ? "Turn Off" : "Turn On"}
                  </button>
                </div>

                <div className="control-auth-options">
                  <span>Password authentication available</span>
                  <span>
                    {passkeyStatus?.configured
                      ? "Touch ID / Passkey configured"
                      : "Touch ID / Passkey not configured"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}

export default Platform;
