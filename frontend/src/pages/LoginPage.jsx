import { useState } from 'react'
import { Alert, Button, Form } from 'react-bootstrap'
import { useAuth } from '../auth/AuthContext.jsx'
import { useNavigate, Link } from 'react-router-dom'
import { UI_ICONS } from '../data/icons.js'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/requests')
    } catch (err) {
      setError('Credenciales incorrectas.')
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
        <h3>Iniciar sesión</h3>
        <p className="muted">Accede a tu cuenta para ver y crear peticiones</p>
        {error && <Alert variant="danger">{error}</Alert>}

        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Correo electrónico</Form.Label>
            <div className="auth-input">
              <i className={`fi ${UI_ICONS.mail}`} />
              <Form.Control
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="auth-control"
                required
              />
            </div>
          </Form.Group>

          <Button type="submit" className="w-100 auth-button">
            Iniciar sesión
          </Button>
        </Form>

        <div className="auth-footer">
          ¿No tienes cuenta? <Link to="/register">Regístrate aquí</Link>
        </div>
      </div>

      <div className="auth-demo">
        <strong>Demo:</strong> maria.garcia@example.com / Demo1234!
      </div>
    </div>
  )
}
