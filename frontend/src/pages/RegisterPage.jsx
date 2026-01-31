import { useState } from 'react'
import { Alert, Button, Form } from 'react-bootstrap'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { UI_ICONS } from '../data/icons.js'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', confirmPassword: '', display_name: '' })
  const [error, setError] = useState('')

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) {
      setError('Las contraseñas no coinciden.')
      return
    }
    try {
      await register({
        email: form.email,
        password: form.password,
        display_name: form.display_name
      })
      navigate('/login')
    } catch (err) {
      setError('No se pudo registrar. Revisa los datos.')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-header">
        <span className="brand-mark">
          <i className={`fi ${UI_ICONS.heart}`} />
        </span>
        <div className="brand-title">AuzolanApp</div>
        <div className="muted">Ayuda vecinal altruista</div>
      </div>

      <div className="auth-card card-shadow">
        <h3>Crear cuenta</h3>
        <p className="muted">Únete a la Comunidad Demo y empieza a ayudar</p>
        {error && <Alert variant="danger">{error}</Alert>}

        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Nombre para mostrar</Form.Label>
            <div className="auth-input">
              <i className={`fi ${UI_ICONS.users}`} />
              <Form.Control
                name="display_name"
                value={form.display_name}
                onChange={handleChange}
                placeholder="Tu nombre"
                className="auth-control"
                required
              />
            </div>
            <div className="auth-hint">Este nombre será visible para otros miembros de la comunidad</div>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Correo electrónico</Form.Label>
            <div className="auth-input">
              <i className={`fi ${UI_ICONS.mail}`} />
              <Form.Control
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="tu@email.com"
                className="auth-control"
                required
              />
            </div>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Contraseña</Form.Label>
            <div className="auth-input">
              <i className={`fi ${UI_ICONS.lock}`} />
              <Form.Control
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="auth-control"
                required
              />
            </div>
            <div className="auth-hint">Mínimo 6 caracteres</div>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Confirmar contraseña</Form.Label>
            <div className="auth-input">
              <i className={`fi ${UI_ICONS.lock}`} />
              <Form.Control
                type="password"
                name="confirmPassword"
                value={form.confirmPassword}
                onChange={handleChange}
                placeholder="••••••••"
                className="auth-control"
                required
              />
            </div>
          </Form.Group>

          <Button type="submit" className="w-100 auth-button">
            Crear cuenta
          </Button>
        </Form>

        <div className="auth-footer">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
        </div>
      </div>

      <div className="auth-benefits">
        <div className="auth-benefits-title">Al registrarte podrás:</div>
        <ul>
          <li>Publicar peticiones de ayuda</li>
          <li>Ofrecerte como voluntario</li>
          <li>Comunicarte con otros vecinos</li>
        </ul>
      </div>
    </div>
  )
}
