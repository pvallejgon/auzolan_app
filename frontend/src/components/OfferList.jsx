import { Button } from 'react-bootstrap'

const statusLabels = {
  offered: 'Pendiente',
  accepted: 'Aceptada',
  rejected: 'Rechazada',
  withdrawn: 'Retirada'
}

export default function OfferList({ offers, onAccept }) {
  return (
    <div className="section-card card-shadow">
      <div className="section-title">Ofertas de ayuda ({offers.length})</div>
      {offers.length === 0 && <div className="muted">Sin ofertas todavía.</div>}
      {offers.map((offer) => (
        <div key={offer.id} className="offer-card">
          <div className="avatar-circle">
            {(offer.volunteer_display_name || 'U').slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-grow-1">
            <div className="d-flex align-items-center gap-2">
              <strong>{offer.volunteer_display_name || `Usuario #${offer.volunteer_user_id}`}</strong>
              <span className={`chip ${offer.status === 'accepted' ? 'status-resolved' : 'category-chip'}`}>
                {statusLabels[offer.status] || offer.status}
              </span>
            </div>
            <div className="muted">{offer.message || 'Sin mensaje'}</div>
          </div>
          {offer.status === 'offered' && (
            <Button variant="primary" size="sm" onClick={() => onAccept(offer.id)}>
              Aceptar
            </Button>
          )}
        </div>
      ))}
    </div>
  )
}
