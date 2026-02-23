import { useEffect, useState } from 'react'
import { Alert, Badge, Button, Card, Form, Spinner } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'

const reasonLabels = {
  payments: 'Pagos',
  advertising: 'Publicidad',
  prohibited_content: 'Contenido prohibido',
  harassment: 'Acoso',
  other: 'Otro',
}

const statusLabels = {
  open: 'Abierto',
  in_review: 'En revision',
  closed: 'Cerrado',
}

const requestStatusLabels = {
  open: 'Abierta',
  in_progress: 'En progreso',
  resolved: 'Resuelta',
  cancelled: 'Cancelada',
}

const statusVariants = {
  open: 'danger',
  in_review: 'warning',
  closed: 'secondary',
}

function formatDateTime(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function ReportsPage() {
  const { user, currentCommunity } = useAuth()
  const navigate = useNavigate()
  const [reports, setReports] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const isSuperadmin = Boolean(user?.is_superadmin)
  const isCommunityModerator = currentCommunity?.role_in_community === 'moderator'
  const canManageReports = Boolean(isSuperadmin || isCommunityModerator)
  const communityId = currentCommunity?.community_id
  const communityName = currentCommunity?.community_name || 'Sin comunidad seleccionada'

  const fetchReports = async () => {
    if (!canManageReports) {
      setReports([])
      setCount(0)
      return
    }

    setLoading(true)
    setError('')
    try {
      const res = await api.get('/reports', {
        params: {
          community_id: communityId || undefined,
          status: statusFilter || undefined,
          page,
          page_size: 10,
        },
      })
      setReports(res.data.results || [])
      setCount(res.data.count || 0)
    } catch {
      setError('No se pudieron cargar los reportes de esta comunidad.')
      setReports([])
      setCount(0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setPage(1)
  }, [communityId, statusFilter, canManageReports])

  useEffect(() => {
    fetchReports()
  }, [communityId, page, statusFilter, canManageReports])

  const totalPages = Math.ceil(count / 10) || 1

  const updateReportStatus = async (reportId, newStatus) => {
    setError('')
    setSuccess('')
    try {
      await api.post(`/reports/${reportId}/status`, { status: newStatus })
      setSuccess('Estado del reporte actualizado correctamente.')
      await fetchReports()
    } catch {
      setError('No se pudo actualizar el estado del reporte.')
    }
  }

  const closeRequestByModeration = async (requestId) => {
    const confirmed = window.confirm('¿Quieres cerrar esta petición por moderación?')
    if (!confirmed) return

    setError('')
    setSuccess('')
    try {
      await api.post(`/moderation/requests/${requestId}/close`, { status: 'cancelled' })
      setSuccess('Petición cerrada por moderación.')
      await fetchReports()
    } catch {
      setError('No se pudo cerrar la petición por moderación.')
    }
  }

  const deleteRequestByModeration = async (requestId) => {
    const confirmed = window.confirm('¿Seguro que quieres eliminar la petición reportada?')
    if (!confirmed) return

    setError('')
    setSuccess('')
    try {
      await api.delete(`/moderation/requests/${requestId}`)
      setSuccess('Petición eliminada por moderación.')
      await fetchReports()
    } catch {
      setError('No se pudo eliminar la petición reportada.')
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">Reportes de peticiones</h2>
          <div className="muted">{communityName}</div>
        </div>
      </div>

      {!canManageReports && (
        <Alert variant="warning">
          Solo moderadores y superadmin pueden gestionar reportes.
        </Alert>
      )}

      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      {canManageReports && (
        <>
          <div className="list-controls-panel">
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
                    <option value="open">Abierto</option>
                    <option value="in_review">En revision</option>
                    <option value="closed">Cerrado</option>
                  </Form.Select>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4">
            {loading ? (
              <div className="d-flex align-items-center gap-2 muted">
                <Spinner size="sm" />
                Cargando reportes...
              </div>
            ) : reports.length === 0 ? (
              <div className="muted">No hay reportes para los filtros seleccionados.</div>
            ) : (
              reports.map((report) => (
                <Card key={report.id} className="card-shadow mb-3">
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2">
                      <div className="fw-semibold">
                        #{report.id} · {report.request_title}
                      </div>
                      <div className="d-flex align-items-center gap-2">
                        <Badge bg="info">{reasonLabels[report.reason] || report.reason}</Badge>
                        <Badge bg={statusVariants[report.status] || 'secondary'}>
                          {statusLabels[report.status] || report.status}
                        </Badge>
                      </div>
                    </div>

                    <div className="muted small mb-2">
                      Comunidad: {report.request_community_name} · Estado petición:{' '}
                      {requestStatusLabels[report.request_status] || report.request_status} · Reportado por:{' '}
                      {report.reporter_display_name} ·{' '}
                      {formatDateTime(report.created_at)}
                    </div>

                    {report.description && <div className="mb-3">{report.description}</div>}

                    <div className="action-row">
                      <Button size="sm" variant="outline-primary" onClick={() => navigate(`/requests/${report.request_id}`)}>
                        Ver petición
                      </Button>

                      {report.status !== 'in_review' && (
                        <Button
                          size="sm"
                          variant="outline-warning"
                          onClick={() => updateReportStatus(report.id, 'in_review')}
                        >
                          Marcar en revisión
                        </Button>
                      )}

                      {report.status !== 'closed' && (
                        <Button
                          size="sm"
                          variant="outline-success"
                          onClick={() => updateReportStatus(report.id, 'closed')}
                        >
                          Cerrar reporte
                        </Button>
                      )}

                      {report.status !== 'open' && (
                        <Button
                          size="sm"
                          variant="outline-secondary"
                          onClick={() => updateReportStatus(report.id, 'open')}
                        >
                          Reabrir reporte
                        </Button>
                      )}

                      <Button
                        size="sm"
                        variant="outline-warning"
                        onClick={() => closeRequestByModeration(report.request_id)}
                      >
                        Cerrar petición
                      </Button>

                      <Button
                        size="sm"
                        variant="outline-danger"
                        onClick={() => deleteRequestByModeration(report.request_id)}
                      >
                        Eliminar petición
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              ))
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
              Página {page} de {totalPages}
            </div>
            <Button
              variant="secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
            >
              Siguiente
            </Button>
          </div>
        </>
      )}
    </div>
  )
}
