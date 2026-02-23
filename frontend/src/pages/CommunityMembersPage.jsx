import { useEffect, useMemo, useState } from 'react'
import { Alert, Badge, Button, Card, Col, Form, Row, Table } from 'react-bootstrap'

import api from '../api/http.js'
import { useAuth } from '../auth/AuthContext.jsx'

const roleLabels = {
  member: 'Miembro',
  moderator: 'Moderador',
  superadmin: 'Superadmin',
}

const statusLabels = {
  pending: 'Pendiente',
  approved: 'Aprobado',
  rejected: 'Rechazado',
  expelled: 'Expulsado',
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleDateString('es-ES')
}

export default function CommunityMembersPage() {
  const { user, currentCommunity, refreshMe } = useAuth()
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState('')
  const [editingMember, setEditingMember] = useState(null)
  const [editForm, setEditForm] = useState({
    display_name: '',
    bio: '',
    status: 'approved',
    role_in_community: 'member',
  })

  const isSuperadmin = Boolean(user?.is_superadmin)
  const isCommunityModerator = currentCommunity?.role_in_community === 'moderator'
  const canManageCommunity = Boolean(isSuperadmin || isCommunityModerator)

  const communityId = currentCommunity?.community_id

  const fetchMembers = async () => {
    if (!communityId) {
      setMembers([])
      setLoading(false)
      return
    }

    setLoading(true)
    setError('')
    try {
      const res = await api.get(`/communities/${communityId}/members`, {
        params: { page_size: 200 },
      })
      setMembers(res.data.results || [])
    } catch {
      setError('No se pudo cargar la lista de miembros de la comunidad.')
      setMembers([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMembers()
  }, [communityId])

  const sortedMembers = useMemo(() => {
    return [...members].sort((a, b) => {
      if (a.role_in_community === b.role_in_community) {
        return (a.display_name || '').localeCompare(b.display_name || '')
      }
      if (a.role_in_community === 'moderator') return -1
      if (b.role_in_community === 'moderator') return 1
      return 0
    })
  }, [members])

  const openEdit = (member) => {
    setSuccess('')
    setError('')
    setEditingMember(member)
    setEditForm({
      display_name: member.display_name || '',
      bio: member.bio || '',
      status: member.status || 'approved',
      role_in_community: member.role_in_community || 'member',
    })
  }

  const closeEdit = () => {
    setEditingMember(null)
  }

  const handleEditChange = (event) => {
    setEditForm((prev) => ({ ...prev, [event.target.name]: event.target.value }))
  }

  const handleSaveMember = async (event) => {
    event.preventDefault()
    if (!editingMember) return

    setSaving(true)
    setError('')
    setSuccess('')

    const payload = {
      display_name: editForm.display_name,
      bio: editForm.bio,
      status: editForm.status,
    }

    if (isSuperadmin) {
      payload.role_in_community = editForm.role_in_community
    }

    try {
      await api.patch(`/communities/${communityId}/members/${editingMember.user_id}`, payload)
      await fetchMembers()
      if (editingMember.user_id === user?.id) {
        await refreshMe()
      }
      setSuccess('Miembro actualizado correctamente.')
      closeEdit()
    } catch {
      setError('No se pudo actualizar el miembro.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h2 className="page-title">Gestión de comunidad</h2>
          <div className="muted">{currentCommunity?.community_name || 'Sin comunidad seleccionada'}</div>
        </div>
      </div>

      {!canManageCommunity && (
        <Alert variant="warning">
          No tienes permisos de moderación en esta comunidad.
        </Alert>
      )}

      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      {canManageCommunity && (
        <Card className="card-shadow">
          <Card.Body>
            <Card.Title className="section-title">Miembros de la comunidad</Card.Title>
            {loading ? (
              <div className="muted">Cargando miembros...</div>
            ) : (
              <Table responsive hover>
                <thead>
                  <tr>
                    <th>Nombre</th>
                    <th>Email</th>
                    <th>Rol</th>
                    <th>Estado</th>
                    <th>Alta</th>
                    <th>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedMembers.map((member) => (
                    <tr key={member.user_id}>
                      <td>{member.display_name}</td>
                      <td>{member.email}</td>
                      <td>
                        <Badge bg={member.role_in_community === 'moderator' ? 'warning' : 'secondary'}>
                          {roleLabels[member.role_in_community] || member.role_in_community}
                        </Badge>
                      </td>
                      <td>{statusLabels[member.status] || member.status}</td>
                      <td>{formatDate(member.joined_at)}</td>
                      <td>
                        <Button size="sm" variant="outline-primary" onClick={() => openEdit(member)}>
                          Editar
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card.Body>
        </Card>
      )}

      {canManageCommunity && editingMember && (
        <Card className="card-shadow mt-4">
          <Card.Body>
            <Card.Title className="section-title">Editar usuario</Card.Title>
            <Form onSubmit={handleSaveMember}>
              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Nombre para mostrar</Form.Label>
                    <Form.Control
                      name="display_name"
                      value={editForm.display_name}
                      onChange={handleEditChange}
                      maxLength={80}
                      required
                    />
                  </Form.Group>
                </Col>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Email (no editable)</Form.Label>
                    <Form.Control value={editingMember.email} disabled readOnly />
                  </Form.Group>
                </Col>
              </Row>

              <Form.Group className="mb-3">
                <Form.Label>Bio</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  name="bio"
                  value={editForm.bio}
                  onChange={handleEditChange}
                  maxLength={280}
                />
              </Form.Group>

              <Row>
                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Estado en comunidad</Form.Label>
                    <Form.Select name="status" value={editForm.status} onChange={handleEditChange}>
                      <option value="pending">Pendiente</option>
                      <option value="approved">Aprobado</option>
                      <option value="rejected">Rechazado</option>
                      <option value="expelled">Expulsado</option>
                    </Form.Select>
                  </Form.Group>
                </Col>

                <Col md={6}>
                  <Form.Group className="mb-3">
                    <Form.Label>Rol en comunidad</Form.Label>
                    <Form.Select
                      name="role_in_community"
                      value={editForm.role_in_community}
                      onChange={handleEditChange}
                      disabled={!isSuperadmin}
                    >
                      <option value="member">Miembro</option>
                      <option value="moderator">Moderador</option>
                    </Form.Select>
                    {!isSuperadmin && (
                      <Form.Text className="text-muted">
                        Solo superadmin puede cambiar el rol en comunidad.
                      </Form.Text>
                    )}
                  </Form.Group>
                </Col>
              </Row>

              <div className="d-flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? 'Guardando...' : 'Guardar'}
                </Button>
                <Button type="button" variant="outline-secondary" onClick={closeEdit}>
                  Cancelar
                </Button>
              </div>
            </Form>
          </Card.Body>
        </Card>
      )}
    </div>
  )
}
