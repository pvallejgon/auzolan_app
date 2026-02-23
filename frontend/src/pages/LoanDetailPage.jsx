import { useEffect, useState } from 'react'
import { Alert, Button, Form } from 'react-bootstrap'
import { Link, useParams } from 'react-router-dom'

import api from '../api/http.js'
import { INFO_ICONS } from '../data/icons.js'

const statusMap = {
  available: { label: 'Disponible', className: 'status-available' },
  loaned: { label: 'Prestado', className: 'status-loaned' },
}

const requestStatusMap = {
  pending: { label: 'Pendiente', className: 'chip-amber' },
  accepted: { label: 'Aceptada', className: 'chip-green' },
  rejected: { label: 'Rechazada', className: 'status-cancelled' },
  withdrawn: { label: 'Retirada', className: 'chip-sky' },
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

export default function LoanDetailPage() {
  const { id } = useParams()
  const [item, setItem] = useState(null)
  const [canRequest, setCanRequest] = useState(false)
  const [canManageItem, setCanManageItem] = useState(false)
  const [canManageRequests, setCanManageRequests] = useState(false)
  const [canMarkReturned, setCanMarkReturned] = useState(false)
  const [loanRequests, setLoanRequests] = useState([])
  const [requestMessage, setRequestMessage] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loadingRequests, setLoadingRequests] = useState(false)

  const fetchItem = async () => {
    try {
      const res = await api.get(`/loans/${id}`)
      setItem(res.data.item)
      setCanRequest(Boolean(res.data.can_request))
      setCanManageItem(Boolean(res.data.can_manage_item))
      setCanManageRequests(Boolean(res.data.can_manage_requests))
      setCanMarkReturned(Boolean(res.data.can_mark_returned))
      setError('')
    } catch {
      setError('No se pudo cargar el detalle del préstamo.')
      setItem(null)
    }
  }

  const fetchLoanRequests = async () => {
    setLoadingRequests(true)
    try {
      const res = await api.get(`/loans/${id}/requests`, { params: { page_size: 100 } })
      const rows = Array.isArray(res.data) ? res.data : res.data.results || []
      setLoanRequests(rows)
    } catch {
      setLoanRequests([])
    } finally {
      setLoadingRequests(false)
    }
  }

  useEffect(() => {
    fetchItem()
  }, [id])

  useEffect(() => {
    if (canManageRequests) {
      fetchLoanRequests()
    }
  }, [canManageRequests, id])

  const handleRequestSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    try {
      await api.post(`/loans/${id}/requests`, { message: requestMessage })
      setRequestMessage('')
      setSuccess('Solicitud enviada correctamente.')
      await fetchItem()
    } catch {
      setError('No se pudo enviar la solicitud de préstamo.')
    }
  }

  const handleAccept = async (requestId) => {
    setError('')
    setSuccess('')
    try {
      await api.post(`/loans/${id}/requests/${requestId}/accept`)
      setSuccess('Solicitud aceptada. El item está marcado como prestado.')
      await fetchItem()
      await fetchLoanRequests()
    } catch {
      setError('No se pudo aceptar la solicitud.')
    }
  }

  const handleReject = async (requestId) => {
    setError('')
    setSuccess('')
    try {
      await api.post(`/loans/${id}/requests/${requestId}/reject`)
      setSuccess('Solicitud rechazada.')
      await fetchItem()
      await fetchLoanRequests()
    } catch {
      setError('No se pudo rechazar la solicitud.')
    }
  }

  const handleMarkReturned = async () => {
    setError('')
    setSuccess('')
    try {
      await api.post(`/loans/${id}/mark-returned`)
      setSuccess('Item marcado como devuelto y disponible.')
      await fetchItem()
      await fetchLoanRequests()
    } catch {
      setError('No se pudo marcar la devolución.')
    }
  }

  if (!item) return null

  const status = statusMap[item.status] || statusMap.available
  const owner = item.owner_display_name || `Usuario #${item.owner_user_id}`
  const borrower = item.borrower_display_name || `Usuario #${item.borrower_user_id}`

  return (
    <div>
      <Link to="/loans" className="back-link">
        ← Volver al listado de préstamos
      </Link>

      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <div className="request-card card-shadow mb-4">
        <div className="d-flex flex-wrap gap-2 mb-3">
          <span className={`chip ${status.className}`}>
            <span className="chip-dot" style={{ background: 'currentColor' }} />
            {status.label}
          </span>
          <span className="chip category-chip">Préstamo</span>
          {canManageItem && <span className="chip chip-amber">Eres quien presta este item</span>}
        </div>

        <h3 className="page-title mb-2">{item.title}</h3>
        <p className="mb-3">{item.description || 'Sin descripción adicional.'}</p>

        <div className="info-row">
          <span className="d-flex align-items-center gap-2">
            <i className={`fi ${INFO_ICONS.user}`} />
            Lo presta: {owner}
          </span>
          <span className="d-flex align-items-center gap-2">
            <i className={`fi ${INFO_ICONS.calendar}`} />
            Publicado: {formatDateTime(item.created_at)}
          </span>
          {item.status === 'loaned' && (
            <>
              <span className="d-flex align-items-center gap-2">
                <i className={`fi ${INFO_ICONS.user}`} />
                En manos de: {borrower}
              </span>
              <span className="d-flex align-items-center gap-2">
                <i className={`fi ${INFO_ICONS.time}`} />
                Prestado desde: {formatDateTime(item.loaned_at)}
              </span>
            </>
          )}
        </div>

        <div className="divider" />
        <div className="action-row">
          {canMarkReturned && (
            <Button variant="success" onClick={handleMarkReturned}>
              Marcar como devuelto
            </Button>
          )}
        </div>
      </div>

      {canRequest && (
        <div className="section-card card-shadow mb-4">
          <div className="section-title">Solicitar préstamo</div>
          <Form onSubmit={handleRequestSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Mensaje (opcional)</Form.Label>
              <Form.Control
                value={requestMessage}
                onChange={(event) => setRequestMessage(event.target.value)}
                maxLength={280}
                placeholder="Ej: Lo necesito para este fin de semana."
              />
            </Form.Group>
            <Button type="submit">Enviar solicitud</Button>
          </Form>
        </div>
      )}

      {canManageRequests && (
        <div className="section-card card-shadow">
          <div className="section-title">Solicitudes recibidas</div>
          {loadingRequests ? (
            <div className="muted">Cargando solicitudes...</div>
          ) : loanRequests.length === 0 ? (
            <div className="muted">Todavía no hay solicitudes para este item.</div>
          ) : (
            loanRequests.map((loanRequest) => {
              const requestStatus = requestStatusMap[loanRequest.status] || requestStatusMap.pending
              return (
                <div key={loanRequest.id} className="offer-card">
                  <div className="w-100">
                    <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
                      <strong>{loanRequest.requester_display_name}</strong>
                      <span className={`chip ${requestStatus.className}`}>{requestStatus.label}</span>
                    </div>
                    <div className="muted small mt-1">
                      Solicitud enviada: {formatDateTime(loanRequest.created_at)}
                    </div>
                    {loanRequest.message && <div className="mt-2">{loanRequest.message}</div>}
                    {loanRequest.responded_at && (
                      <div className="muted small mt-2">
                        Resuelta: {formatDateTime(loanRequest.responded_at)}
                      </div>
                    )}
                    {loanRequest.status === 'pending' && item.status === 'available' && (
                      <div className="action-row mt-3">
                        <Button size="sm" onClick={() => handleAccept(loanRequest.id)}>
                          Aceptar
                        </Button>
                        <Button
                          size="sm"
                          variant="outline-danger"
                          onClick={() => handleReject(loanRequest.id)}
                        >
                          Rechazar
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
