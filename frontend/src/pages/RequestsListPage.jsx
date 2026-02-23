import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, ButtonGroup, Form } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'
import RequestCard from '../components/RequestCard.jsx'
import RequestFilters from '../components/RequestFilters.jsx'

export default function RequestsListPage({ mine = false }) {
  const { currentCommunity } = useAuth()
  const navigate = useNavigate()
  const [requests, setRequests] = useState([])
  const [count, setCount] = useState(0)
  const [filters, setFilters] = useState({ status: '', category: '' })
  const [order, setOrder] = useState('latest')
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState(() => {
    return localStorage.getItem('requests_view_mode') === 'grid' ? 'grid' : 'list'
  })

  const communityId = currentCommunity?.community_id
  const communityName = currentCommunity?.community_name || 'Sin comunidad seleccionada'

  const fetchRequests = async () => {
    if (!communityId) {
      setRequests([])
      setCount(0)
      return
    }

    try {
      const res = await api.get('/requests', {
        params: {
          community_id: communityId,
          status: filters.status || undefined,
          category: filters.category || undefined,
          mine: mine ? '1' : undefined,
          order,
          page,
          page_size: 6,
        },
      })
      setRequests(res.data.results)
      setCount(res.data.count)
      setError('')
    } catch {
      setError('No se pudieron cargar las peticiones.')
      setRequests([])
      setCount(0)
    }
  }

  useEffect(() => {
    setPage(1)
  }, [communityId])

  useEffect(() => {
    fetchRequests()
  }, [communityId, filters, page, mine, order])

  useEffect(() => {
    localStorage.setItem('requests_view_mode', viewMode)
  }, [viewMode])

  const handleChange = (event) => {
    setPage(1)
    setFilters((prev) => ({ ...prev, [event.target.name]: event.target.value }))
  }

  const filteredRequests = useMemo(() => {
    if (!search.trim()) return requests
    const term = search.toLowerCase()
    return requests.filter((request) => {
      return (
        request.title.toLowerCase().includes(term) ||
        request.description.toLowerCase().includes(term) ||
        request.category.toLowerCase().includes(term)
      )
    })
  }, [requests, search])

  const totalPages = Math.ceil(count / 6) || 1

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">{mine ? 'Mis peticiones' : 'Peticiones de ayuda'}</h2>
          <div className="muted">
            {communityName} • {count} peticiones
          </div>
        </div>
        <Button variant="primary" onClick={() => navigate('/requests/new')}>
          + Nueva petición
        </Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <div className="list-controls-panel">
        <input
          type="text"
          className="search-input"
          placeholder="Buscar peticiones..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <div className="list-controls-grid">
          <RequestFilters status={filters.status} category={filters.category} onChange={handleChange} />

          <div className="list-side-controls">
            <div className="control-stack view-toggle-desktop">
              <span className="control-label">Vista</span>
              <ButtonGroup size="sm" aria-label="Selector de vista de peticiones">
                <Button
                  variant={viewMode === 'list' ? 'primary' : 'outline-secondary'}
                  onClick={() => setViewMode('list')}
                >
                  Listado
                </Button>
                <Button
                  variant={viewMode === 'grid' ? 'primary' : 'outline-secondary'}
                  onClick={() => setViewMode('grid')}
                >
                  2 columnas
                </Button>
              </ButtonGroup>
            </div>
            <div className="control-stack">
              {/* <span className="control-label">Orden</span> */}
              <Form.Select
                value={order}
                onChange={(e) => setOrder(e.target.value)}
                className="filter-select"
                style={{ minWidth: 220 }}
              >
                <option value="latest">Más nuevas</option>
                <option value="oldest">Más antiguas</option>
              </Form.Select>
            </div>
          </div>
        </div>
      </div>

      <div className={`cards-list-container ${viewMode === 'grid' ? 'view-grid' : 'view-list'} mt-4`}>
        {filteredRequests.length === 0 ? (
          <div className="muted">No hay peticiones que coincidan con la búsqueda.</div>
        ) : (
          filteredRequests.map((request) => <RequestCard key={request.id} request={request} />)
        )}
      </div>

      <div className="d-flex justify-content-between align-items-center mt-4">
        <Button
          variant="secondary"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Anterior
        </Button>
        <div className="muted">
          Página {page} de {totalPages}
        </div>
        <Button
          variant="secondary"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Siguiente
        </Button>
      </div>
    </div>
  )
}
