import { useEffect, useState } from 'react'
import { Alert, Button, Card, Form } from 'react-bootstrap'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'

export default function ProfilePage() {
  const { user, refreshMe } = useAuth()
  const [form, setForm] = useState({ email: '', display_name: '', bio: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/profile')
        setForm({
          email: res.data.email || '',
          display_name: res.data.display_name || '',
          bio: res.data.bio || '',
        })
      } catch {
        setError('No se pudo cargar tu perfil.')
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [])

  if (!user) return null

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setSaving(true)

    try {
      await api.patch('/profile', {
        display_name: form.display_name,
        bio: form.bio,
      })
      await refreshMe()
      setSuccess('Perfil actualizado correctamente.')
    } catch {
      setError('No se pudo guardar el perfil.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="card-shadow">
      <Card.Body>
        <Card.Title className="page-title">Mi perfil</Card.Title>

        {error && <Alert variant="danger">{error}</Alert>}
        {success && <Alert variant="success">{success}</Alert>}

        {loading ? (
          <div className="muted">Cargando perfil...</div>
        ) : (
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>Email (no editable)</Form.Label>
              <Form.Control value={form.email} disabled readOnly />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Nombre para mostrar</Form.Label>
              <Form.Control
                name="display_name"
                value={form.display_name}
                onChange={handleChange}
                maxLength={80}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Bio</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                name="bio"
                value={form.bio}
                onChange={handleChange}
                maxLength={280}
                placeholder="Cuéntanos algo breve sobre ti"
              />
            </Form.Group>

            <Button type="submit" disabled={saving}>
              {saving ? 'Guardando...' : 'Guardar cambios'}
            </Button>
          </Form>
        )}
      </Card.Body>
    </Card>
  )
}
