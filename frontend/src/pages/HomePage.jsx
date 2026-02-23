import { useEffect } from 'react'
import { Button, Container } from 'react-bootstrap'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { CATEGORIES } from '../data/categories.js'
import { CATEGORY_ICONS, UI_ICONS } from '../data/icons.js'

const categoryStyles = {
  Recados: 'chip-blue',
  Acompañamiento: 'chip-green',
  Tecnología: 'chip-purple',
  Hogar: 'chip-amber',
  Transporte: 'chip-sky'
}

export default function HomePage() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!loading && user) {
      navigate('/requests')
    }
  }, [loading, user, navigate])

  return (
    <div className="home-page">
      <Container className="home-hero">
        <div className="home-pill">
          <i className={`fi ${UI_ICONS.logo}`} /> Ayuda vecinal altruista
        </div>
        <h1 className="home-title">
          Vecinos que se ayudan,
          <span> comunidades que crecen</span>
        </h1>
        <p className="home-subtitle">
          Publica lo que necesitas y recibe ayuda de voluntarios de tu comunidad. Sin dinero, sin
          complicaciones, solo solidaridad vecinal.
        </p>
        <div className="home-actions">
          <Button as={Link} to="/register" variant="primary">
            Únete a la comunidad
          </Button>
          <Button as={Link} to="/login" variant="outline-secondary">
            Ya tengo cuenta
          </Button>
        </div>
      </Container>

      <Container className="home-categories">
        <div className="muted text-center">Tipos de ayuda que puedes pedir o ofrecer</div>
        <div className="home-chip-row">
          {CATEGORIES.map((item) => (
            <div key={item} className={`chip category-chip ${categoryStyles[item] || ''}`}>
              <i className={`fi ${CATEGORY_ICONS[item] || 'fi-rr-tags'}`} />
              {item}
            </div>
          ))}
        </div>
      </Container>

      <Container className="home-section">
        <h2 className="text-center mb-2">¿Cómo funciona?</h2>
        <p className="muted text-center">AuzolanApp conecta a personas que necesitan ayuda con vecinos dispuestos a echar una mano</p>
        <div className="home-grid">
          <div className="home-card">
            <div className="home-icon">
              <i className={`fi ${UI_ICONS.list}`} />
            </div>
            <h4>Publica tu petición</h4>
            <p>Describe lo que necesitas y otros vecinos podrán ofrecerse para ayudarte.</p>
          </div>
          <div className="home-card">
            <div className="home-icon">
              <i className={`fi ${UI_ICONS.users}`} />
            </div>
            <h4>Comunidad cercana</h4>
            <p>Conecta con vecinos de tu zona que quieren ayudar de forma altruista.</p>
          </div>
          <div className="home-card">
            <div className="home-icon">
              <i className={`fi ${UI_ICONS.chat}`} />
            </div>
            <h4>Chat privado</h4>
            <p>Comunícate de forma segura una vez aceptes a un voluntario.</p>
          </div>
          <div className="home-card">
            <div className="home-icon">
              <i className={`fi ${UI_ICONS.shield}`} />
            </div>
            <h4>100% gratuito</h4>
            <p>Sin pagos, sin propinas, sin publicidad. Solo ayuda vecinal genuina.</p>
          </div>
        </div>
      </Container>

      <section className="home-cta">
        <Container>
          <h3>Únete a tu comunidad</h3>
          <p>Empieza a ayudar y recibir ayuda de tus vecinos hoy mismo. Es gratis, seguro y sin compromisos.</p>
          <Button as={Link} to="/register" variant="success">
            Crear mi cuenta gratis
          </Button>
        </Container>
      </section>

      <footer className="home-footer">
        <Container className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-2">
            <span className="brand-mark" style={{ width: 28, height: 28 }}>
              <i className={`fi ${UI_ICONS.logo}`} />
            </span>
            <span className="fw-semibold">AuzolanApp</span>
          </div>
          <div className="muted">Ayuda vecinal altruista • Sin ánimo de lucro</div>
        </Container>
      </footer>
    </div>
  )
}
