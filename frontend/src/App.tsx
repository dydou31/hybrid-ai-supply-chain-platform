import { useEffect, useState } from 'react'
import './App.css'
import AIAssistant from './AIAssistant'
import Platform from './Platform'
import { API_URL } from './config'

type NavItem = 'Dashboard' | 'Suppliers' | 'AI Assistant' | 'Platform'

type Supplier = {
  id: number
  name: string
  country: string
  risk_level: string
  blocked_stock_eur: string
}

type ServiceHealth = {
  status: string
  pgvector?: string
}

type PlatformHealth = {
  status: string
  services: Record<string, ServiceHealth>
}

const navItems: { label: NavItem; icon: string }[] = [
  { label: 'Dashboard', icon: '▦' },
  { label: 'Suppliers', icon: '◫' },
  { label: 'AI Assistant', icon: '✦' },
  { label: 'Platform', icon: '◉' },
]

function App() {
  const getPageFromPath = (): NavItem => {
  switch (window.location.pathname) {
    case '/suppliers':
      return 'Suppliers'
    case '/ai-assistant':
      return 'AI Assistant'
    case '/platform':
      return 'Platform'
    default:
      return 'Dashboard'
  }
}

const [activePage, setActivePage] = useState<NavItem>(getPageFromPath)
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [supplierSearch, setSupplierSearch] = useState('')
  const [supplierSort, setSupplierSort] = useState<keyof Supplier>('name')
  const [supplierSortDirection, setSupplierSortDirection] =
    useState<'asc' | 'desc'>('asc')
  const [suppliersAvailable, setSuppliersAvailable] = useState(false)
  const [apiHealthy, setApiHealthy] = useState(false)
  const [platformHealth, setPlatformHealth] =
    useState<PlatformHealth | null>(null)
  const [knowledgeCount, setKnowledgeCount] = useState(0)
  const [knowledgeAvailable, setKnowledgeAvailable] = useState(false)

  const navigateTo = (page: NavItem) => {
  const paths: Record<NavItem, string> = {
    Dashboard: '/',
    Suppliers: '/suppliers',
    'AI Assistant': '/ai-assistant',
    Platform: '/platform',
  }

  window.history.pushState({}, '', paths[page])
  setActivePage(page)
}

useEffect(() => {
  const handlePopState = () => {
    setActivePage(getPageFromPath())
  }

  window.addEventListener('popstate', handlePopState)

  return () => {
    window.removeEventListener('popstate', handlePopState)
  }
}, [])

  useEffect(() => {
    const loadDashboard = async () => {
      const [
        healthResult,
        suppliersResult,
        platformResult,
        knowledgeResult,
      ] = await Promise.allSettled([
        fetch(`${API_URL}/health`),
        fetch(`${API_URL}/suppliers`),
        fetch(`${API_URL}/health/platform`),
        fetch(`${API_URL}/ai/knowledge/count`),
      ])

      if (
        healthResult.status === 'fulfilled' &&
        healthResult.value.ok
      ) {
        const health = await healthResult.value.json()
        setApiHealthy(health.status === 'healthy')
      } else {
        setApiHealthy(false)
      }

      if (
        platformResult.status === 'fulfilled' &&
        platformResult.value.ok
      ) {
        const platformData = await platformResult.value.json()
        setPlatformHealth(platformData)
      } else {
        setPlatformHealth(null)
      }

      if (
        suppliersResult.status === 'fulfilled' &&
        suppliersResult.value.ok
      ) {
        const supplierData = await suppliersResult.value.json()
        setSuppliers(supplierData)
        setSuppliersAvailable(true)
      } else {
        setSuppliers([])
        setSuppliersAvailable(false)
      }

      if (
        knowledgeResult.status === 'fulfilled' &&
        knowledgeResult.value.ok
      ) {
        const knowledgeData = await knowledgeResult.value.json()
        setKnowledgeCount(knowledgeData.count)
        setKnowledgeAvailable(true)
      } else {
        setKnowledgeCount(0)
        setKnowledgeAvailable(false)
      }
    }

    loadDashboard()
  }, [])

  const handleSupplierSort = (column: keyof Supplier) => {
    if (supplierSort === column) {
      setSupplierSortDirection((current) =>
        current === 'asc' ? 'desc' : 'asc',
      )
    } else {
      setSupplierSort(column)
      setSupplierSortDirection('asc')
    }
  }

  const supplierSortIcon = (column: keyof Supplier) => {
    if (supplierSort !== column) return '↕'
    return supplierSortDirection === 'asc' ? '↑' : '↓'
  }

  const visibleSuppliers = suppliers
    .filter((supplier) => {
      const search = supplierSearch.trim().toLowerCase()

      if (!search) return true

      return (
        supplier.name.toLowerCase().includes(search) ||
        supplier.country.toLowerCase().includes(search) ||
        supplier.risk_level.toLowerCase().includes(search) ||
        String(supplier.id).includes(search)
      )
    })
    .sort((a, b) => {
      let comparison = 0

      if (supplierSort === 'blocked_stock_eur') {
        comparison =
          Number(a.blocked_stock_eur) - Number(b.blocked_stock_eur)
      } else if (supplierSort === 'id') {
        comparison = a.id - b.id
      } else {
        comparison = String(a[supplierSort]).localeCompare(
          String(b[supplierSort]),
          undefined,
          { sensitivity: 'base' },
        )
      }

      return supplierSortDirection === 'asc'
        ? comparison
        : -comparison
    })

  const blockedStock = suppliers.reduce(
    (total, supplier) => total + Number(supplier.blocked_stock_eur),
    0,
  )

  const highRiskSuppliers = suppliers.filter(
    (supplier) => supplier.risk_level === 'high',
  ).length

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">AI</div>

          <div>
            <h1>Hybrid AI</h1>
            <span>Supply Chain Platform</span>
          </div>
        </div>

        <nav>
          {navItems.map((item) => (
            <button
              key={item.label}
              className={
                activePage === item.label ? 'nav-item active' : 'nav-item'
              }
              onClick={() => navigateTo(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="environment">
            <span className="status-dot"></span>
            Local environment
          </div>

          <span>Platform v0.1.0</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <p className="eyebrow">HYBRID AI SUPPLY CHAIN PLATFORM</p>
            <h2>{activePage}</h2>
          </div>

          <div className="api-badge">
            <span className="status-dot"></span>
            {apiHealthy ? 'API Operational' : 'API Unavailable'}
          </div>
        </header>

        {activePage === 'Dashboard' && (
          <>
            <section className="hero">
              <div>
                <p className="eyebrow">SUPPLY CHAIN INTELLIGENCE</p>

                <h3>Operational visibility powered by AI.</h3>

                <p>
                  Monitor supplier risk, inventory exposure and platform health
                  from a single interface.
                </p>
              </div>

              <button onClick={() => navigateTo('AI Assistant')}>
                Ask AI Assistant →
              </button>
            </section>

            <section className="kpi-grid">
              <article className="card kpi">
                <span>Active Suppliers</span>
                <strong>{suppliersAvailable ? suppliers.length : '—'}</strong>
                <small>FastAPI / PostgreSQL</small>
              </article>

              <article className="card kpi">
                <span>Blocked Stock</span>

                <strong>
                  {suppliersAvailable
                    ? blockedStock.toLocaleString('fr-FR', {
                        style: 'currency',
                        currency: 'EUR',
                      })
                    : '—'}
                </strong>

                <small>Inventory exposure</small>
              </article>

              <article className="card kpi">
                <span>High Risk Suppliers</span>
                <strong>{suppliersAvailable ? highRiskSuppliers : '—'}</strong>
                <small>Risk monitoring</small>
              </article>

              <article className="card kpi">
                <span>AI Knowledge Base</span>
                <strong>{knowledgeAvailable ? knowledgeCount : '—'}</strong>
                <small>Vector documents</small>
              </article>
            </section>

            <section className="dashboard-grid">
              <article className="card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">INFRASTRUCTURE</p>
                    <h3>Platform Health</h3>
                  </div>

                  <span
                    className={
                      !apiHealthy
                        ? 'unknown'
                        : platformHealth?.status === 'healthy'
                          ? 'healthy'
                          : 'unhealthy'
                    }
                  >
                    {!apiHealthy
                      ? 'Monitoring Unavailable'
                      : platformHealth?.status === 'healthy'
                        ? 'Healthy'
                        : 'Degraded'}
                  </span>
                </div>

                <div className="service-list">
                  {[
                    {
                      name: 'FastAPI',
                      status: apiHealthy ? 'running' : 'unavailable',
                    },
                    {
                      name: 'PostgreSQL + pgvector',
                      status: !platformHealth
                        ? 'unknown'
                        : platformHealth.services.postgres?.status ===
                              'healthy' &&
                            platformHealth.services.postgres?.pgvector ===
                              'enabled'
                          ? 'running'
                          : 'unavailable',
                    },
                    {
                      name: 'Redis',
                      status: !platformHealth
                        ? 'unknown'
                        : platformHealth.services.redis?.status === 'healthy'
                          ? 'running'
                          : 'unavailable',
                    },
                    {
                      name: 'Prometheus',
                      status: !platformHealth
                        ? 'unknown'
                        : platformHealth.services.prometheus?.status ===
                            'healthy'
                          ? 'running'
                          : 'unavailable',
                    },
                    {
                      name: 'Grafana',
                      status: !platformHealth
                        ? 'unknown'
                        : platformHealth.services.grafana?.status ===
                            'healthy'
                          ? 'running'
                          : 'unavailable',
                    },
                    {
                      name: 'Tempo',
                      status: !platformHealth
                        ? 'unknown'
                        : platformHealth.services.tempo?.status === 'healthy'
                          ? 'running'
                          : 'unavailable',
                    },
                    {
                      name: 'Ollama + Llama',
                      status: !platformHealth
                        ? 'unknown'
                        : platformHealth.services.ollama?.status === 'healthy'
                          ? 'running'
                          : 'unavailable',
                    },
                  ].map((service) => (
                    <div className="service" key={service.name}>
                      <span>{service.name}</span>

                      <span
                        className={`service-status ${
                          service.status === 'unavailable'
                            ? 'service-down'
                            : service.status === 'unknown'
                              ? 'service-unknown'
                              : ''
                        }`}
                      >
                        <span className="status-dot"></span>

                        {service.status === 'running'
                          ? 'Running'
                          : service.status === 'unavailable'
                            ? 'Unavailable'
                            : 'Unknown'}
                      </span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="card ai-card">
                <p className="eyebrow">RAG / LLAMA</p>
                <h3>AI Supply Chain Assistant</h3>

                <p>
                  Ask operational questions using semantic search over the
                  platform knowledge base and local Llama inference.
                </p>

                <div className="ai-example">
                  <span>Example</span>
                  <p>Which supplier has recurring delivery delays?</p>
                </div>

                <button onClick={() => setActivePage('AI Assistant')}>
                  Open AI Assistant
                </button>
              </article>
            </section>
          </>
        )}

        {activePage === 'Suppliers' && (
          <section className="suppliers-page">
            <div className="section-heading">
              <div>
                <p className="eyebrow">SUPPLIER MANAGEMENT</p>
                <h3>Supplier Overview</h3>

                <p>
                  Monitor supplier risk and blocked stock exposure from
                  PostgreSQL.
                </p>
              </div>

              <div className="supplier-summary">
                <div>
                  <span>Suppliers</span>
                  <strong>{suppliers.length}</strong>
                </div>

                <div>
                  <span>Total Exposure</span>

                  <strong>
                    {blockedStock.toLocaleString('fr-FR', {
                      style: 'currency',
                      currency: 'EUR',
                    })}
                  </strong>
                </div>
              </div>
            </div>

            <div className="supplier-table-tools">
              <input
                type="search"
                value={supplierSearch}
                onChange={(event) => setSupplierSearch(event.target.value)}
                placeholder="Search suppliers, country, risk level..."
                aria-label="Search suppliers"
              />

              <span>
                {visibleSuppliers.length} of {suppliers.length} suppliers
              </span>
            </div>

            <div className="card supplier-table-card">
              <div className="table-header">
                <button
                  type="button"
                  onClick={() => handleSupplierSort('name')}
                >
                  Supplier {supplierSortIcon('name')}
                </button>

                <button
                  type="button"
                  onClick={() => handleSupplierSort('country')}
                >
                  Country {supplierSortIcon('country')}
                </button>

                <button
                  type="button"
                  onClick={() => handleSupplierSort('risk_level')}
                >
                  Risk Level {supplierSortIcon('risk_level')}
                </button>

                <button
                  type="button"
                  onClick={() => handleSupplierSort('blocked_stock_eur')}
                >
                  Blocked Stock {supplierSortIcon('blocked_stock_eur')}
                </button>
              </div>

              {visibleSuppliers.map((supplier) => (
                <div className="supplier-row" key={supplier.id}>
                  <div className="supplier-name">
                    <div className="supplier-avatar">
                      {supplier.name.charAt(0)}
                    </div>

                    <div>
                      <strong>{supplier.name}</strong>
                      <small>ID #{supplier.id}</small>
                    </div>
                  </div>

                  <span>{supplier.country}</span>

                  <span
                    className={`risk-badge risk-${supplier.risk_level.toLowerCase()}`}
                  >
                    {supplier.risk_level}
                  </span>

                  <strong className="stock-value">
                    {Number(supplier.blocked_stock_eur).toLocaleString(
                      'fr-FR',
                      {
                        style: 'currency',
                        currency: 'EUR',
                      },
                    )}
                  </strong>
                </div>
              ))}
            </div>
          </section>
        )}

        {activePage === 'AI Assistant' && <AIAssistant />}

        {activePage === 'Platform' && <Platform />}
      </main>
    </div>
  )
}

export default App
