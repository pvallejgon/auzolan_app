import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Form } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'
import RequestCard from '../components/RequestCard.jsx'
import RequestFilters from '../components/RequestFilters.jsx'
import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function RequestsListPage({ mine = false }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [requests, setRequests] = useState([])
  const [count, setCount] = useState(0)
  const [filters, setFilters] = useState({ status: '', category: '' })
  const [order, setOrder] = useState('latest')
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [communityName, setCommunityName] = useState('Comunidad Demo')

  const communityId = user?.communities?.[0]?.community_id

  const fetchCommunity = async () => {
    try {
      const res = await api.get('/communities')
      const community = res.data.find((c) => c.id === communityId)
      if (community) setCommunityName(community.name)
    } catch {
      setCommunityName('Comunidad Demo')
    }
  }

  const fetchRequests = async () => {
    if (!communityId) return
    try {
      const res = await api.get('/requests', {
        params: {
          community_id: communityId,
          status: filters.status || undefined,
          category: filters.category || undefined,
          mine: mine ? '1' : undefined,
          order,
          page,
          page_size: 6
        }
      })
      setRequests(res.data.results)
      setCount(res.data.count)
    } catch {
      setError('No se pudieron cargar las peticiones.')
    }
  }

  useEffect(() => {
    fetchCommunity()
  }, [communityId])

  useEffect(() => {
    fetchRequests()
  }, [communityId, filters, page, mine, order])

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

      <input
        type="text"
        className="search-input mb-3"
        placeholder="Buscar peticiones..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="d-flex justify-content-between align-items-center flex-wrap gap-3">
        <RequestFilters status={filters.status} category={filters.category} onChange={handleChange} />
        <div className="d-flex align-items-center gap-2">
          <span className="muted">Ordenar por:</span>
          <Form.Select
            value={order}
            onChange={(e) => setOrder(e.target.value)}
            className="filter-select"
            style={{ minWidth: 180 }}
          >
            <option value="latest">Más nuevas</option>
            <option value="oldest">Más antiguas</option>
          </Form.Select>
        </div>
      </div>

      <div className="mt-4">
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
