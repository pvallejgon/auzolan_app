import { useEffect, useState } from 'react'
import { Alert, Button, Card, Form } from 'react-bootstrap'
import { useParams } from 'react-router-dom'
import api from '../api/http.js'

function formatHourMinute(dateString) {
  if (!dateString) return '--:--'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return '--:--'
  return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}

export default function ChatPage() {
  const { id } = useParams()
  const [conversationId, setConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [body, setBody] = useState('')
  const [error, setError] = useState('')

  const fetchConversation = async () => {
    try {
      const res = await api.get(`/requests/${id}/conversation`)
      setConversationId(res.data.conversation_id)
    } catch {
      setError('No tienes acceso al chat o no hay voluntario aceptado.')
    }
  }

  const fetchMessages = async (conversation) => {
    try {
      const res = await api.get(`/conversations/${conversation}/messages`, {
        params: { page_size: 50 }
      })
      setMessages(res.data.results)
    } catch {
      setError('No se pudieron cargar los mensajes.')
    }
  }

  useEffect(() => {
    fetchConversation()
  }, [id])

  useEffect(() => {
    if (conversationId) {
      fetchMessages(conversationId)
    }
  }, [conversationId])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!body.trim()) return
    try {
      await api.post(`/conversations/${conversationId}/messages`, { body })
      setBody('')
      await fetchMessages(conversationId)
    } catch {
      setError('No se pudo enviar el mensaje.')
    }
  }

  return (
    <Card className="card-shadow">
      <Card.Body>
        <Card.Title className="page-title">Chat</Card.Title>
        {error && <Alert variant="danger">{error}</Alert>}
        <div className="mb-3" style={{ maxHeight: 300, overflowY: 'auto' }}>
          {messages.map((msg) => (
            <div key={msg.id} className="mb-2">
              <div className="small muted">
                {msg.sender_display_name || `Usuario #${msg.sender_user_id}`} ({formatHourMinute(msg.created_at)})
              </div>
              <div>{msg.body}</div>
            </div>
          ))}
        </div>
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Mensaje</Form.Label>
            <Form.Control
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
            />
          </Form.Group>
          <Button type="submit">Enviar</Button>
        </Form>
      </Card.Body>
    </Card>
  )
}
