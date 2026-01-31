import { Button, Form, Modal } from 'react-bootstrap'
import { useState } from 'react'

export default function ReportModal({ show, onHide, onSubmit }) {
  const [reason, setReason] = useState('payments')
  const [description, setDescription] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    await onSubmit({ reason, description })
    setDescription('')
  }

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Reportar petición</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit}>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Motivo</Form.Label>
            <Form.Select value={reason} onChange={(e) => setReason(e.target.value)}>
              <option value="payments">Pagos</option>
              <option value="advertising">Publicidad</option>
              <option value="prohibited_content">Contenido prohibido</option>
              <option value="harassment">Acoso</option>
              <option value="other">Otros</option>
            </Form.Select>
          </Form.Group>
          <Form.Group>
            <Form.Label>Descripción (opcional)</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Cancelar
          </Button>
          <Button variant="warning" type="submit">
            Enviar reporte
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  )
}
