import { useEffect, useState } from 'react'
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
} from 'react-icons/si'
import { FaAws, FaRobot } from 'react-icons/fa'
import { FaGithub, FaProjectDiagram } from 'react-icons/fa'
import { VscPulse } from 'react-icons/vsc'

type ServiceHealth = {
  status: string
  postgres?: string
  pgvector?: string
  ollama?: string
  model?: string
  model_ready?: boolean
}

type PlatformHealth = {
  status: string
  services: Record<string, ServiceHealth>
}

type NodeStatus = 'live' | 'down' | 'architecture'

type ArchitectureNode = {
  id: string
  name: string
  subtitle: string
  group: 'application' | 'data' | 'ai' | 'delivery' | 'observability'
  healthKey?: string
  icon: React.ReactNode
  description: string
}

type ArchitectureNodeProps = {
  id: string
  nodes: ArchitectureNode[]
  platform: PlatformHealth | null
  selected: string
  onSelect: (id: string) => void
}

function ArchitectureNodeCard({
  id,
  nodes,
  platform,
  selected,
  onSelect,
}: ArchitectureNodeProps) {
  const node = nodes.find((item) => item.id === id)
  if (!node) return null

  let status: NodeStatus

  if (node.id === 'fastapi') {
    status = platform ? 'live' : 'down'
  } else if (!node.healthKey) {
    status = 'architecture'
  } else if (!platform) {
    status = 'down'
  } else {
    status =
      platform.services[node.healthKey]?.status === 'healthy'
        ? 'live'
        : 'down'
  }

  return (
    <button
      type="button"
      className={`architecture-node architecture-${status} ${
        selected === id ? 'architecture-selected' : ''
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
        {status === 'live'
          ? 'Live'
          : status === 'down'
            ? 'Unavailable'
            : 'Architecture'}
      </span>
    </button>
  )
}

function Platform() {
  const [platform, setPlatform] = useState<PlatformHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState('fastapi')

  const loadHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health/platform')
      if (!response.ok) throw new Error('Platform health request failed')

      const data: PlatformHealth = await response.json()
      setPlatform(data)
    } catch {
      setPlatform(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHealth()
    const interval = window.setInterval(loadHealth, 10000)
    return () => window.clearInterval(interval)
  }, [])

  const nodes: ArchitectureNode[] = [
    {
      id: 'react',
      name: 'React',
      subtitle: 'TypeScript + Vite',
      group: 'application',
      icon: <SiReact />,
      description: 'Interactive frontend for dashboards, suppliers, AI and platform operations.',
    },
    {
      id: 'fastapi',
      name: 'FastAPI',
      subtitle: 'REST API',
      group: 'application',
      icon: <SiFastapi />,
      description: 'Core backend exposing business, AI and platform health APIs.',
    },
    {
      id: 'postgres',
      name: 'PostgreSQL',
      subtitle: 'Operational data',
      group: 'data',
      healthKey: 'postgres',
      icon: <SiPostgresql />,
      description: 'Primary relational database for suppliers, purchase orders and application data.',
    },
    {
      id: 'pgvector',
      name: 'pgvector',
      subtitle: 'Vector storage',
      group: 'ai',
      healthKey: 'postgres',
      icon: <FaProjectDiagram />,
      description: 'PostgreSQL vector extension used for semantic knowledge retrieval.',
    },
    {
      id: 'redis',
      name: 'Redis',
      subtitle: 'Cache',
      group: 'data',
      healthKey: 'redis',
      icon: <SiRedis />,
      description: 'Low-latency cache and fast data access layer.',
    },
    {
      id: 'hybrid-ai',
      name: 'Hybrid AI',
      subtitle: 'Structured + RAG',
      group: 'ai',
      icon: <FaProjectDiagram />,
      description: 'Combines structured supply-chain retrieval with semantic RAG context.',
    },
    {
      id: 'ollama',
      name: 'Ollama / Llama',
      subtitle: 'Local inference',
      group: 'ai',
      healthKey: 'ollama',
      icon: <FaRobot />,
      description: 'Local LLM inference layer running the Llama model used by the AI Assistant.',
    },

    {
      id: 'github',
      name: 'GitHub Actions',
      subtitle: 'CI/CD',
      group: 'delivery',
      icon: <FaGithub />,
      description: 'Continuous integration pipeline validating the project.',
    },
    {
      id: 'docker',
      name: 'Docker',
      subtitle: 'Containers',
      group: 'delivery',
      icon: <SiDocker />,
      description: 'Containerization of the application and supporting services.',
    },
    {
      id: 'kubernetes',
      name: 'Kubernetes',
      subtitle: 'Orchestration',
      group: 'delivery',
      icon: <SiKubernetes />,
      description: 'Container orchestration layer demonstrated locally with Kubernetes.',
    },
    {
      id: 'helm',
      name: 'Helm',
      subtitle: 'K8s packaging',
      group: 'delivery',
      icon: <SiHelm />,
      description: 'Reusable Kubernetes deployment configuration.',
    },
    {
      id: 'terraform',
      name: 'Terraform',
      subtitle: 'Infrastructure as Code',
      group: 'delivery',
      icon: <SiTerraform />,
      description: 'Declarative infrastructure provisioning.',
    },
    {
      id: 'aws',
      name: 'AWS',
      subtitle: 'ECR + ECS/Fargate',
      group: 'delivery',
      icon: <FaAws />,
      description: 'Cloud deployment demonstration using ECR and ECS Fargate.',
    },

    {
      id: 'otel',
      name: 'OpenTelemetry',
      subtitle: 'Instrumentation',
      group: 'observability',
      icon: <VscPulse />,
      description: 'Application telemetry instrumentation and trace export.',
    },
    {
      id: 'prometheus',
      name: 'Prometheus',
      subtitle: 'Metrics',
      group: 'observability',
      healthKey: 'prometheus',
      icon: <SiPrometheus />,
      description: 'Metrics collection for platform observability.',
    },
    {
      id: 'tempo',
      name: 'Tempo',
      subtitle: 'Tracing',
      group: 'observability',
      healthKey: 'tempo',
      icon: <VscPulse />,
      description: 'Distributed tracing backend receiving OpenTelemetry traces.',
    },
    {
      id: 'grafana',
      name: 'Grafana',
      subtitle: 'Visualization',
      group: 'observability',
      healthKey: 'grafana',
      icon: <SiGrafana />,
      description: 'Dashboards for metrics and observability data.',
    },
  ]

  const getStatus = (node: ArchitectureNode): NodeStatus => {
    // A successful /health/platform response proves that FastAPI is reachable.
    if (node.id === 'fastapi') {
      return platform ? 'live' : 'down'
    }

    if (!node.healthKey) return 'architecture'
    if (!platform) return 'down'

    return platform.services[node.healthKey]?.status === 'healthy'
      ? 'live'
      : 'down'
  }

  const selectedNode =
    nodes.find((node) => node.id === selected) ?? nodes[0]

  const selectedStatus = getStatus(selectedNode)

  const healthyCount = platform
    ? Object.values(platform.services).filter(
        (service) => service.status === 'healthy',
      ).length
    : 0



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
            platform?.status === 'healthy' ? 'healthy' : 'degraded'
          }`}
        >
          <span className="status-dot" />
          {loading
            ? 'Checking platform...'
            : platform?.status === 'healthy'
              ? 'All Systems Operational'
              : 'Platform Degraded'}
        </div>
      </div>

      <div className="platform-summary">
        <div className="card platform-stat">
          <span>Live Services</span>
          <strong>
            {healthyCount}
            <small> / 6</small>
          </strong>
        </div>

        <div className="card platform-stat">
          <span>Vector Database</span>
          <strong>
            {platform?.services.postgres?.pgvector === 'enabled'
              ? 'Enabled'
              : 'Unknown'}
          </strong>
        </div>

        <div className="card platform-stat">
          <span>LLM Model</span>
          <strong>
            {platform?.services.ollama?.model_ready
              ? platform.services.ollama.model
              : 'Unavailable'}
          </strong>
        </div>

        <div className="card platform-stat">
          <span>Auto Refresh</span>
          <strong>10s</strong>
        </div>
      </div>

      <div className="architecture-toolbar">
        <div className="architecture-legend">
          <span><i className="legend-live" /> Live monitored</span>
          <span><i className="legend-architecture" /> Architecture component</span>
          <span><i className="legend-down" /> Unavailable</span>
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

      <div className="architecture-layout">
        <div className="architecture-canvas">

          <div className="architecture-zone architecture-zone-app">
            <div className="architecture-zone-title">
              <span>01</span>
              APPLICATION
            </div>

            <div className="architecture-flow architecture-flow-main">
              <ArchitectureNodeCard id="react" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              <div className="architecture-link">
                <span>REST</span>
                <b>→</b>
              </div>
              <ArchitectureNodeCard id="fastapi" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
            </div>
          </div>

          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>02</span>
              DATA & HYBRID AI
            </div>

            <div className="architecture-ai-grid">
              <div className="architecture-stack">
                <ArchitectureNodeCard id="postgres" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
                <div className="architecture-vertical-link">
                  <span>vector extension</span>
                  ↓
                </div>
                <ArchitectureNodeCard id="pgvector" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              </div>

              <div className="architecture-middle-links">
                <span>SQL / cache</span>
                <b>⇄</b>
              </div>

              <div className="architecture-stack">
                <ArchitectureNodeCard id="redis" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
                <div className="architecture-vertical-link">
                  <span>context</span>
                  ↓
                </div>
                <ArchitectureNodeCard id="hybrid-ai" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              </div>

              <div className="architecture-middle-links">
                <span>RAG</span>
                <b>→</b>
              </div>

              <ArchitectureNodeCard id="ollama" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
            </div>
          </div>

          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>03</span>
              PLATFORM DELIVERY
            </div>

            <div className="architecture-delivery">
              <ArchitectureNodeCard id="github" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard id="docker" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard id="kubernetes" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard id="helm" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard id="terraform" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard id="aws" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
            </div>
          </div>

          <div className="architecture-zone">
            <div className="architecture-zone-title">
              <span>04</span>
              OBSERVABILITY
            </div>

            <div className="architecture-observability">
              <ArchitectureNodeCard id="otel" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              <span className="pipeline-arrow">→</span>

              <div className="architecture-observability-split">
                <ArchitectureNodeCard id="prometheus" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
                <ArchitectureNodeCard id="tempo" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
              </div>

              <span className="pipeline-arrow">→</span>
              <ArchitectureNodeCard id="grafana" nodes={nodes} platform={platform} selected={selected} onSelect={setSelected} />
            </div>
          </div>
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
            {selectedStatus === 'live'
              ? 'Live monitored service'
              : selectedStatus === 'down'
                ? 'Service unavailable'
                : 'Architecture component'}
          </div>

          <p className="inspector-description">
            {selectedNode.description}
          </p>

          <div className="inspector-meta">
            <div>
              <span>Layer</span>
              <strong>{selectedNode.group}</strong>
            </div>

            <div>
              <span>Monitoring</span>
              <strong>
                {selectedNode.healthKey ? 'Live API health' : 'Architecture'}
              </strong>
            </div>

            {selectedNode.id === 'postgres' && (
              <>
                <div>
                  <span>PostgreSQL</span>
                  <strong>
                    {platform?.services.postgres?.postgres ?? 'Unknown'}
                  </strong>
                </div>
                <div>
                  <span>pgvector</span>
                  <strong>
                    {platform?.services.postgres?.pgvector ?? 'Unknown'}
                  </strong>
                </div>
              </>
            )}

            {selectedNode.id === 'pgvector' && (
              <div>
                <span>Extension</span>
                <strong>
                  {platform?.services.postgres?.pgvector ?? 'Unknown'}
                </strong>
              </div>
            )}

            {selectedNode.id === 'ollama' && (
              <>
                <div>
                  <span>Runtime</span>
                  <strong>
                    {platform?.services.ollama?.ollama ?? 'Unknown'}
                  </strong>
                </div>
                <div>
                  <span>Model</span>
                  <strong>
                    {platform?.services.ollama?.model ?? 'Unknown'}
                  </strong>
                </div>
              </>
            )}
          </div>

          <div className="inspector-note">
            Click any technology in the architecture to inspect its role and
            live status when monitoring is available.
          </div>
        </aside>
      </div>
    </section>
  )
}

export default Platform
