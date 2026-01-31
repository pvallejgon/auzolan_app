import { Link } from 'react-router-dom'
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

export default function RequestCard({ request }) {
  const status = statusMap[request.status] || statusMap.open
  const offersCount = request.offers_count ?? 0
  const createdLabel = formatRelative(request.created_at)
  const author = request.created_by_display_name || `Usuario #${request.created_by_user_id}`
  const categoryIcon = CATEGORY_ICONS[request.category] || 'fi-rr-tags'

  return (
    <div className="request-card card-shadow">
      <div className="d-flex flex-wrap gap-2 mb-3">
        <span className={`chip ${status.className}`}>
          <span className="chip-dot" style={{ background: 'currentColor' }} />
          {status.label}
        </span>
        <span className="chip category-chip">
          <i className={`fi ${categoryIcon}`} />
          {request.category}
        </span>
      </div>

      <h4 className="page-title mb-2">
        <Link to={`/requests/${request.id}`} className="text-decoration-none text-dark">
          {request.title}
        </Link>
      </h4>
      <p className="muted mb-3">{request.description}</p>

      <div className="info-row">
        <span className="d-flex align-items-center gap-2">
          <i className={`fi ${INFO_ICONS.user}`} />
          {author}
        </span>
        <span className="d-flex align-items-center gap-2">
          <i className={`fi ${INFO_ICONS.location}`} />
          {request.location_area_text || 'Zona aproximada no indicada'}
        </span>
        <span className="d-flex align-items-center gap-2">
          <i className={`fi ${INFO_ICONS.time}`} />
          {request.time_window_text || 'Sin ventana temporal'}
        </span>
        <span className="d-flex align-items-center gap-2">
          <i className={`fi ${INFO_ICONS.offers}`} />
          {offersCount} oferta{offersCount === 1 ? '' : 's'}
        </span>
      </div>

      <div className="divider" />
      <div className="muted small">Publicada {createdLabel}</div>
    </div>
  )
}
