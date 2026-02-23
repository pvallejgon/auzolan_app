import { Link } from 'react-router-dom'
import { INFO_ICONS } from '../data/icons.js'

const statusMap = {
  available: { label: 'Disponible', className: 'status-available' },
  loaned: { label: 'Prestado', className: 'status-loaned' },
}

function formatDate(dateString) {
  if (!dateString) return 'hace poco'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return 'hace poco'
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export default function LoanCard({ item }) {
  const status = statusMap[item.status] || statusMap.available
  const owner = item.owner_display_name || `Usuario #${item.owner_user_id}`
  const borrower = item.borrower_display_name || `Usuario #${item.borrower_user_id}`
  const pendingCount = item.pending_requests_count ?? 0

  return (
    <div className="request-card card-shadow">
      <div className="d-flex flex-wrap gap-2 mb-3">
        <span className={`chip ${status.className}`}>
          <span className="chip-dot" style={{ background: 'currentColor' }} />
          {status.label}
        </span>
        <span className="chip category-chip">Préstamo</span>
      </div>

      <h4 className="page-title mb-2">
        <Link to={`/loans/${item.id}`} className="text-decoration-none text-dark">
          {item.title}
        </Link>
      </h4>
      <p className="muted mb-3">{item.description || 'Sin descripción adicional.'}</p>

      <div className="info-row">
        <span className="d-flex align-items-center gap-2">
          <i className={`fi ${INFO_ICONS.user}`} />
          Lo presta: {owner}
        </span>
        {item.status === 'loaned' && (
          <span className="d-flex align-items-center gap-2">
            <i className={`fi ${INFO_ICONS.user}`} />
            En manos de: {borrower}
          </span>
        )}
        <span className="d-flex align-items-center gap-2">
          <i className={`fi ${INFO_ICONS.offers}`} />
          {pendingCount} solicitud{pendingCount === 1 ? '' : 'es'} pendiente
          {pendingCount === 1 ? '' : 's'}
        </span>
      </div>

      <div className="divider" />
      <div className="muted small">Publicado: {formatDate(item.created_at)}</div>
    </div>
  )
}
