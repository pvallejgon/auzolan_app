import { useEffect, useState } from 'react'
import { Alert, Button, Form } from 'react-bootstrap'
import { useNavigate, useParams, Link } from 'react-router-dom'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'
import OfferList from '../components/OfferList.jsx'
import ReportModal from '../components/ReportModal.jsx'
import { CATEGORY_ICONS, INFO_ICONS } from '../data/icons.js'

const statusMap = {
  open: { label: 'Abierta', className: 'status-open' },
  in_progress: { label: 'En progreso', className: 'status-in_progress' },
  resolved: { label: 'Resuelta', className: 'status-resolved' },
  cancelled: { label: 'Cancelada', className: 'status-cancelled' }
}

function formatRelative(dateString) {
  if (!dateString) return 'hace poco'
  const date = new Date(dateString)
  const diffMs = Date.now() - date.getTime()
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (days >= 365) {
    const years = Math.round(days / 365)
    return `hace alrededor de ${years} año${years === 1 ? '' : 's'}`
  }
  if (days >= 30) {
    const months = Math.round(days / 30)
    return `hace alrededor de ${months} mes${months === 1 ? '' : 'es'}`
  }
  if (days >= 1) {
    return `hace ${days} día${days === 1 ? '' : 's'}`
  }
  return 'hace poco'
}

export default function RequestDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [request, setRequest] = useState(null)
  const [offers, setOffers] = useState([])
  const [offerMessage, setOfferMessage] = useState('')
  const [error, setError] = useState('')
  const [reportOpen, setReportOpen] = useState(false)
  const [canChat, setCanChat] = useState(false)

  const fetchRequest = async () => {
    try {
      const res = await api.get(`/requests/${id}`)
      setRequest({
        ...res.data.request,
        offers_count: res.data.offers_count,
        accepted_offer_id: res.data.accepted_offer_id,
        can_offer: res.data.can_offer,
        can_accept: res.data.can_accept,
        can_close: res.data.can_close,
        can_moderate: res.data.can_moderate
      })
    } catch {
      setError('No se pudo cargar la petición.')
    }
  }

  const fetchOffers = async () => {
    try {
      const res = await api.get(`/requests/${id}/offers`)
      setOffers(res.data)
    } catch {
      setOffers([])
    }
  }

  const checkChat = async () => {
    if (!request?.accepted_offer_id) return
    try {
      await api.get(`/requests/${id}/conversation`)
      setCanChat(true)
    } catch {
      setCanChat(false)
    }
  }

  useEffect(() => {
    fetchRequest()
  }, [id])

  const isCreator = request?.created_by_user_id === user?.id
  const canModerate = Boolean(request?.can_moderate)
  const canSeeOffers = Boolean(request && user && (isCreator || canModerate))

  useEffect(() => {
    if (canSeeOffers) {
      fetchOffers()
    }
    if (request) {
      checkChat()
    }
  }, [request, canSeeOffers])

  const handleOfferSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await api.post(`/requests/${id}/offers`, { message: offerMessage })
      setOfferMessage('')
      await fetchRequest()
    } catch {
      setError('No se pudo enviar la oferta.')
    }
  }

  const handleAccept = async (offerId) => {
    try {
      await api.post(`/requests/${id}/accept-offer/${offerId}`)
      await fetchRequest()
      await fetchOffers()
    } catch {
      setError('No se pudo aceptar la oferta.')
    }
  }

  const handleClose = async (statusValue) => {
    try {
      await api.post(`/requests/${id}/close`, { status: statusValue })
      await fetchRequest()
    } catch {
      setError('No se pudo cerrar la petición.')
    }
  }

  const handleModerationClose = async (statusValue = 'cancelled') => {
    try {
      await api.post(`/moderation/requests/${id}/close`, { status: statusValue })
      await fetchRequest()
      await fetchOffers()
    } catch {
      setError('No se pudo cerrar la petición por moderación.')
    }
  }

  const handleModerationDelete = async () => {
    const confirmed = window.confirm('¿Seguro que quieres eliminar esta petición por moderación?')
    if (!confirmed) return

    try {
      await api.delete(`/moderation/requests/${id}`)
      navigate('/requests')
    } catch {
      setError('No se pudo eliminar la petición por moderación.')
    }
  }

  const handleReport = async (payload) => {
    try {
      await api.post(`/requests/${id}/reports`, payload)
      setReportOpen(false)
    } catch {
      setError('No se pudo reportar la petición.')
    }
  }

  if (!request) {
    return null
  }

  const status = statusMap[request.status] || statusMap.open
  const canOffer = request.can_offer ?? (request.status === 'open' && !isCreator)
  const author = isCreator ? 'Tú' : request.created_by_display_name || `Usuario #${request.created_by_user_id}`
  const categoryIcon = CATEGORY_ICONS[request.category] || 'fi-rr-tags'

  return (
    <div>
      <Link to="/requests" className="back-link">
        ← Volver al listado
      </Link>

      {error && <Alert variant="danger">{error}</Alert>}

      <div className="request-card card-shadow mb-4">
        <div className="d-flex flex-wrap gap-2 mb-3">
          <span className={`chip ${status.className}`}>
            <span className="chip-dot" style={{ background: 'currentColor' }} />
            {status.label}
          </span>
          <span className="chip category-chip">
            <i className={`fi ${categoryIcon}`} />
            {request.category}
          </span>
          {canModerate && <span className="chip chip-amber">Modo moderación</span>}
        </div>

        <h3 className="page-title mb-2">{request.title}</h3>
        <p className="mb-3">{request.description}</p>

        <div className="info-row">
          <span className="d-flex align-items-center gap-2">
            <i className={`fi ${INFO_ICONS.user}`} />
            {author}
          </span>
          <span className="d-flex align-items-center gap-2">
            <i className={`fi ${INFO_ICONS.calendar}`} />
            {formatRelative(request.created_at)}
          </span>
          <span className="d-flex align-items-center gap-2">
            <i className={`fi ${INFO_ICONS.time}`} />
            {request.time_window_text || 'Sin ventana temporal'}
          </span>
          <span className="d-flex align-items-center gap-2">
            <i className={`fi ${INFO_ICONS.location}`} />
            {request.location_area_text || 'Zona aproximada no indicada'}
          </span>
        </div>

        <div className="divider" />

        <div className="action-row">
          {canChat && (
            <Button variant="secondary" onClick={() => navigate(`/requests/${id}/chat`)}>
              Ir al chat
            </Button>
          )}
          {request.can_close && (
            <>
              <Button variant="success" onClick={() => handleClose('resolved')}>
                Marcar resuelta
              </Button>
              <Button variant="outline-danger" onClick={() => handleClose('cancelled')}>
                Cancelar
              </Button>
            </>
          )}
          {canModerate && (
            <>
              {['open', 'in_progress'].includes(request.status) && (
                <Button variant="outline-warning" onClick={() => handleModerationClose('cancelled')}>
                  Cerrar por moderación
                </Button>
              )}
              <Button variant="outline-danger" onClick={handleModerationDelete}>
                Eliminar por moderación
              </Button>
            </>
          )}
          <Button variant="outline-secondary" onClick={() => setReportOpen(true)}>
            Reportar
          </Button>
        </div>
      </div>

      {canOffer && (
        <div className="section-card card-shadow mb-4">
          <div className="section-title">Ofrecer ayuda</div>
          <Form onSubmit={handleOfferSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Mensaje (opcional)</Form.Label>
              <Form.Control
                value={offerMessage}
                onChange={(e) => setOfferMessage(e.target.value)}
                maxLength={280}
              />
            </Form.Group>
            <Button type="submit">Ofrecer ayuda</Button>
          </Form>
        </div>
      )}

      {canSeeOffers && (
        <OfferList
          offers={offers}
          onAccept={handleAccept}
          canAccept={Boolean(request.can_accept)}
        />
      )}

      <ReportModal show={reportOpen} onHide={() => setReportOpen(false)} onSubmit={handleReport} />
    </div>
  )
}
