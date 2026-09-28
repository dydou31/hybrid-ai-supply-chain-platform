import { useEffect, useState } from 'react'

type ServiceHealth = {
  status: string
  postgres?: string
  pgvector?: string
  redis?: string
  prometheus?: string
  grafana?: string
  tempo?: string
  ollama?: string
  model?: string
  model_ready?: boolean
}

type PlatformHealth = {
  status: string
  services: Record<string, ServiceHealth>
}

const serviceInfo: Record<string, { name: string; description: string }> = {
  postgres: {
    name: 'PostgreSQL + pgvector',
    description: 'Database & vector storage',
  },
  redis: {
    name: 'Redis',
    description: 'Cache & fast data access',
  },
  prometheus: {
    name: 'Prometheus',
    description: 'Metrics collection',
  },
  grafana: {
    name: 'Grafana',
    description: 'Observability dashboards',
  },
  tempo: {
    name: 'Tempo',
    description: 'Distributed tracing',
  },
  ollama: {
    name: 'Ollama + Llama',
    description: 'Local LLM inference',
  },
}

function Platform() {
  const [platform, setPlatform] = useState<PlatformHealth | null>(null)
  const [loading, setLoading] = useState(true)

  const loadHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health/platform')

      if (!response.ok) {
        throw new Error('Platform health request failed')
      }

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

  const healthyCount = platform
    ? Object.values(platform.services).filter(
        (service) => service.status === 'healthy',
      ).length
    : 0

  return (
    <section className="platform-page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">PLATFORM ENGINEERING</p>
          <h3>Platform Control Center</h3>
          <p>
            Live health monitoring across the application, data, AI and
            observability stack.
          </p>
        </div>

        <div
          className={`platform-overall ${
            platform?.status === 'healthy' ? 'healthy' : 'degraded'
          }`}
        >
          <span className="status-dot"></span>
          {loading
            ? 'Checking platform...'
            : platform?.status === 'healthy'
              ? 'All Systems Operational'
              : 'Platform Degraded'}
        </div>
      </div>

      <div className="platform-summary">
        <div className="card platform-stat">
          <span>Services Healthy</span>
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
          <span>Health Refresh</span>
          <strong>10s</strong>
        </div>
      </div>

      <div className="card platform-services">
        <div className="platform-services-header">
          <div>
            <p className="eyebrow">LIVE INFRASTRUCTURE</p>
            <h3>Service Health</h3>
          </div>

          <button type="button" onClick={loadHealth}>
            Refresh
          </button>
        </div>

        {!platform && !loading && (
          <div className="platform-error">
            FastAPI health endpoint is currently unreachable.
          </div>
        )}

        <div className="service-grid">
          {platform &&
            Object.entries(platform.services).map(([key, service]) => {
              const info = serviceInfo[key]

              return (
                <div className="service-card" key={key}>
                  <div className="service-card-top">
                    <div className="service-icon">
                      {info?.name.charAt(0) ?? '?'}
                    </div>

                    <div>
                      <strong>{info?.name ?? key}</strong>
                      <small>{info?.description}</small>
                    </div>

                    <span
                      className={`service-status ${
                        service.status === 'healthy'
                          ? 'service-healthy'
                          : 'service-unhealthy'
                      }`}
                    >
                      <span className="status-dot"></span>
                      {service.status}
                    </span>
                  </div>

                  {key === 'postgres' && (
                    <div className="service-details">
                      <span>PostgreSQL: {service.postgres}</span>
                      <span>pgvector: {service.pgvector}</span>
                    </div>
                  )}

                  {key === 'ollama' && (
                    <div className="service-details">
                      <span>Ollama: {service.ollama}</span>
                      <span>Model: {service.model}</span>
                    </div>
                  )}
                </div>
              )
            })}
        </div>
      </div>
    </section>
  )
}

export default Platform
