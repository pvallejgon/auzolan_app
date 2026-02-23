import { useEffect, useState } from 'react'
import { Alert, Button, Form } from 'react-bootstrap'
import { Link, useNavigate } from 'react-router-dom'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { UI_ICONS } from '../data/icons.js'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    display_name: '',
    community_id: '',
  })
  const [communities, setCommunities] = useState([])
  const [loadingCommunities, setLoadingCommunities] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchCommunities = async () => {
      try {
        const res = await api.get('/communities')
        const list = Array.isArray(res.data) ? res.data : []
        setCommunities(list)
        if (list.length > 0) {
          setForm((prev) => ({ ...prev, community_id: String(list[0].id) }))
        }
      } catch {
        setError('No se pudieron cargar las comunidades disponibles.')
      } finally {
        setLoadingCommunities(false)
      }
    }

    fetchCommunities()
  }, [])

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

    if (!form.community_id) {
      setError('Debes seleccionar una comunidad.')
      return
    }

    try {
      await register({
        email: form.email,
        password: form.password,
        display_name: form.display_name,
        community_id: Number(form.community_id),
      })
      navigate('/login')
    } catch {
      setError('No se pudo registrar. Revisa los datos.')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-header">
        <span className="brand-mark">
          <i className={`fi ${UI_ICONS.logo}`} />
        </span>
        <div className="brand-title">AuzolanApp</div>
        <div className="muted">Ayuda vecinal altruista</div>
      </div>

      <div className="auth-card card-shadow">
        <h3>Crear cuenta</h3>
        <p className="muted">Elige tu comunidad y empieza a ayudar</p>
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
            <div className="auth-hint">Este nombre sera visible para otros miembros</div>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Correo electronico</Form.Label>
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
            <Form.Label>Comunidad</Form.Label>
            <Form.Select
              name="community_id"
              value={form.community_id}
              onChange={handleChange}
              required
              disabled={loadingCommunities || communities.length === 0}
            >
              {loadingCommunities ? (
                <option value="">Cargando comunidades...</option>
              ) : communities.length === 0 ? (
                <option value="">No hay comunidades disponibles</option>
              ) : (
                communities.map((community) => (
                  <option key={community.id} value={community.id}>
                    {community.name}
                  </option>
                ))
              )}
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Contrasena</Form.Label>
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
            <Form.Label>Confirmar contrasena</Form.Label>
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

          <Button type="submit" className="w-100 auth-button" disabled={loadingCommunities || communities.length === 0}>
            Crear cuenta
          </Button>
        </Form>

        <div className="auth-footer">
          ¿Ya tienes cuenta? <Link to="/login">Inicia sesion</Link>
        </div>
      </div>

      <div className="auth-benefits">
        <div className="auth-benefits-title">Al registrarte podras:</div>
        <ul>
          <li>Publicar peticiones de ayuda</li>
          <li>Ofrecerte como voluntario</li>
          <li>Comunicarte con otros vecinos</li>
        </ul>
      </div>
    </div>
  )
}
