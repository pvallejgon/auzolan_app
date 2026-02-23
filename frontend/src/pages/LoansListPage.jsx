import { useEffect, useMemo, useState } from 'react'
import { Alert, Button, ButtonGroup, Card, Form } from 'react-bootstrap'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'
import LoanCard from '../components/LoanCard.jsx'

export default function LoansListPage() {
  const { currentCommunity } = useAuth()
  const [items, setItems] = useState([])
  const [count, setCount] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [mineOnly, setMineOnly] = useState(false)
  const [order, setOrder] = useState('latest')
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [createError, setCreateError] = useState('')
  const [creating, setCreating] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [createForm, setCreateForm] = useState({ title: '', description: '' })
  const [viewMode, setViewMode] = useState(() => {
    return localStorage.getItem('loans_view_mode') === 'grid' ? 'grid' : 'list'
  })

  const communityId = currentCommunity?.community_id
  const communityName = currentCommunity?.community_name || 'Sin comunidad seleccionada'

  const fetchLoans = async () => {
    if (!communityId) {
      setItems([])
      setCount(0)
      return
    }

    try {
      const res = await api.get('/loans', {
        params: {
          community_id: communityId,
          status: statusFilter || undefined,
          mine: mineOnly ? '1' : undefined,
          order,
          page,
          page_size: 6,
        },
      })
      setItems(res.data.results || [])
      setCount(res.data.count || 0)
      setError('')
    } catch {
      setError('No se pudo cargar el listado de prestamos.')
      setItems([])
      setCount(0)
    }
  }

  useEffect(() => {
    setPage(1)
  }, [communityId, statusFilter, mineOnly, order])

  useEffect(() => {
    fetchLoans()
  }, [communityId, statusFilter, mineOnly, order, page])

  useEffect(() => {
    localStorage.setItem('loans_view_mode', viewMode)
  }, [viewMode])

  const filteredItems = useMemo(() => {
    if (!search.trim()) return items
    const term = search.toLowerCase()
    return items.filter((item) => {
      return (
        item.title.toLowerCase().includes(term) ||
        (item.description || '').toLowerCase().includes(term) ||
        (item.owner_display_name || '').toLowerCase().includes(term)
      )
    })
  }, [items, search])

  const totalPages = Math.ceil(count / 6) || 1

  const handleCreateChange = (event) => {
    setCreateForm((prev) => ({ ...prev, [event.target.name]: event.target.value }))
  }

  const handleCreateSubmit = async (event) => {
    event.preventDefault()
    setCreateError('')
    if (!communityId) {
      setCreateError('Selecciona una comunidad para publicar el prestamo.')
      return
    }

    setCreating(true)
    try {
      await api.post('/loans', {
        community_id: communityId,
        title: createForm.title,
        description: createForm.description || undefined,
      })
      setCreateForm({ title: '', description: '' })
      setShowCreateForm(false)
      await fetchLoans()
    } catch {
      setCreateError('No se pudo crear el item de prestamo.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">Prestamos vecinales</h2>
          <div className="muted">
            {communityName} - {count} items
          </div>
        </div>
        <Button onClick={() => setShowCreateForm((prev) => !prev)}>
          {showCreateForm ? 'Cancelar' : '+ Publicar item'}
        </Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {showCreateForm && (
        <Card className="card-shadow mb-4">
          <Card.Body>
            <Card.Title className="section-title">Nuevo prestamo</Card.Title>
            <div className="muted mb-3">Mini formulario para ofrecer una herramienta u objeto util.</div>
            {createError && <Alert variant="danger">{createError}</Alert>}
            <Form onSubmit={handleCreateSubmit}>
              <Form.Group className="mb-3">
                <Form.Label>Nombre del item</Form.Label>
                <Form.Control
                  name="title"
                  value={createForm.title}
                  onChange={handleCreateChange}
                  placeholder="Ej: Taladro, escalera, carrito..."
                  maxLength={120}
                  required
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Descripcion (opcional)</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  name="description"
                  value={createForm.description}
                  onChange={handleCreateChange}
                  maxLength={500}
                  placeholder="Estado, condiciones de uso, disponibilidad aproximada..."
                />
              </Form.Group>
              <Button type="submit" disabled={creating}>
                {creating ? 'Publicando...' : 'Publicar prestamo'}
              </Button>
            </Form>
          </Card.Body>
        </Card>
      )}

      <div className="list-controls-panel">
        <input
          type="text"
          className="search-input"
          placeholder="Buscar prestamos..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        <div className="list-controls-grid">
          <div className="request-filters-block">
            <span className="control-label">Filtrar por</span>
            <div className="request-filters-selects">
              <Form.Select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className="filter-select"
                style={{ minWidth: 220 }}
              >
                <option value="">Todos los estados</option>
                <option value="available">Disponible</option>
                <option value="loaned">Prestado</option>
              </Form.Select>
              <Form.Check
                type="switch"
                id="mine-loans-switch"
                label="Solo los que presto yo"
                checked={mineOnly}
                onChange={(event) => setMineOnly(event.target.checked)}
                className="pt-2"
              />
            </div>
          </div>

          <div className="list-side-controls">
            <div className="control-stack view-toggle-desktop">
              <span className="control-label">Vista</span>
              <ButtonGroup size="sm" aria-label="Selector de vista de prestamos">
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
                onChange={(event) => setOrder(event.target.value)}
                className="filter-select"
                style={{ minWidth: 220 }}
              >
                <option value="latest">Mas recientes</option>
                <option value="oldest">Mas antiguos</option>
              </Form.Select>
            </div>
          </div>
        </div>
      </div>

      <div className={`cards-list-container ${viewMode === 'grid' ? 'view-grid' : 'view-list'} mt-4`}>
        {filteredItems.length === 0 ? (
          <div className="muted">No hay items que coincidan con la busqueda.</div>
        ) : (
          filteredItems.map((item) => <LoanCard key={item.id} item={item} />)
        )}
      </div>

      <div className="d-flex justify-content-between align-items-center mt-4">
        <Button
          variant="secondary"
          disabled={page <= 1}
          onClick={() => setPage((prev) => Math.max(1, prev - 1))}
        >
          Anterior
        </Button>
        <div className="muted">
          Pagina {page} de {totalPages}
        </div>
        <Button
          variant="secondary"
          disabled={page >= totalPages}
          onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
        >
          Siguiente
        </Button>
      </div>
    </div>
  )
}
