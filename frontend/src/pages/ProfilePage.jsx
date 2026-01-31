import { Card, ListGroup } from 'react-bootstrap'
import { useAuth } from '../auth/AuthContext.jsx'

export default function ProfilePage() {
  const { user } = useAuth()

  if (!user) return null

  return (
    <Card className="card-shadow">
      <Card.Body>
        <Card.Title className="page-title">Mi perfil</Card.Title>
        <ListGroup variant="flush">
          <ListGroup.Item>Nombre: {user.display_name}</ListGroup.Item>
          <ListGroup.Item>Email: {user.email}</ListGroup.Item>
        </ListGroup>
      </Card.Body>
    </Card>
  )
}
