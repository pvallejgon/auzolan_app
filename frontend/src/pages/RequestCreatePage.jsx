import { useState } from 'react'
import { Alert, Button, Card, Form } from 'react-bootstrap'
import { useNavigate } from 'react-router-dom'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'
import { CATEGORIES } from '../data/categories.js'

export default function RequestCreatePage() {
  const { currentCommunity } = useAuth()
  const navigate = useNavigate()
  const communityId = currentCommunity?.community_id
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: '',
    time_window_text: '',
    location_area_text: ''
  })
  const [error, setError] = useState('')

  const handleChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (!communityId) {
      setError('Selecciona una comunidad para publicar la petición.')
      return
    }

    try {
      const payload = {
        community_id: communityId,
        title: form.title,
        description: form.description,
        category: form.category,
        time_window_text: form.time_window_text || undefined,
        location_area_text: form.location_area_text || undefined
      }
      const res = await api.post('/requests', payload)
      navigate(`/requests/${res.data.id}`)
    } catch {
      setError('No se pudo crear la petición.')
    }
  }

  return (
    <Card className="card-shadow">
      <Card.Body>
        <Card.Title className="page-title">Nueva petición</Card.Title>
        <div className="muted mb-3">Comunidad: {currentCommunity?.community_name || 'Sin seleccionar'}</div>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Título</Form.Label>
            <Form.Control name="title" value={form.title} onChange={handleChange} required />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Descripción</Form.Label>
            <Form.Control
              as="textarea"
              rows={4}
              name="description"
              value={form.description}
              onChange={handleChange}
              required
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Categoría</Form.Label>
            <Form.Select name="category" value={form.category} onChange={handleChange} required>
              <option value="">Selecciona una categoría</option>
              {CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Ventana temporal</Form.Label>
            <Form.Control
              name="time_window_text"
              value={form.time_window_text}
              onChange={handleChange}
              placeholder="Ej: Esta tarde"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Zona aproximada</Form.Label>
            <Form.Control
              name="location_area_text"
              value={form.location_area_text}
              onChange={handleChange}
              placeholder="Ej: Barrio norte"
            />
          </Form.Group>
          <Button type="submit">Publicar petición</Button>
        </Form>
      </Card.Body>
    </Card>
  )
}
