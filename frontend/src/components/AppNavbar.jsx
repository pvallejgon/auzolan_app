import { Container, Form, Nav, Navbar } from 'react-bootstrap'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext.jsx'
import { UI_ICONS } from '../data/icons.js'

export default function AppNavbar() {
  const {
    user,
    logout,
    currentCommunity,
    currentCommunityId,
    setCurrentCommunityId,
  } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const initials = user?.display_name
    ? user.display_name
        .split(' ')
        .map((part) => part[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : 'U'

  const approvedCommunities = (user?.communities || []).filter((item) => item.status === 'approved')
  const canManageCommunity = Boolean(
    user?.is_superadmin || currentCommunity?.role_in_community === 'moderator'
  )
  const path = location.pathname
  const isMineSection = path.startsWith('/requests/mine')
  const isRequestsSection = path.startsWith('/requests') && !isMineSection
  const isLoansSection = path.startsWith('/loans')
  const isCommunitySection = path.startsWith('/community')
  const isReportsSection = path.startsWith('/reports')
  const navTabClass = (isActive) => `nav-link-tab${isActive ? ' active' : ''}`

  return (
    <Navbar expand="lg" className="navbar-clean" sticky="top">
      <Container>
        <Navbar.Brand as={Link} to="/" className="d-flex align-items-center">
          <span className="brand-mark">
            <i className={`fi ${UI_ICONS.logo}`} />
          </span>
          <span className="brand-title">AuzolanApp</span>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="main-nav" />
        <Navbar.Collapse id="main-nav">
          <Nav className="mx-auto gap-3">
            {user && (
              <>
                <Nav.Link as={NavLink} to="/requests" className={navTabClass(isRequestsSection)}>
                  Peticiones
                </Nav.Link>
                <Nav.Link as={NavLink} to="/requests/mine" className={navTabClass(isMineSection)}>
                  Mis peticiones
                </Nav.Link>
                {canManageCommunity && (
                  <Nav.Link as={NavLink} to="/community/members" className={navTabClass(isCommunitySection)}>
                    Mi comunidad
                  </Nav.Link>
                )}
                {canManageCommunity && (
                  <Nav.Link as={NavLink} to="/reports" className={navTabClass(isReportsSection)}>
                    Reportes
                  </Nav.Link>
                )}
                <Nav.Link as={NavLink} to="/loans" className={navTabClass(isLoansSection)}>
                  Préstamos
                </Nav.Link>
              </>
            )}
          </Nav>
          <Nav className="ms-auto">
            {user ? (
              <div className="d-flex align-items-center gap-3">
                {approvedCommunities.length > 0 && (
                  <div className="d-flex flex-column">
                    <small className="muted">Comunidad actual</small>
                    {approvedCommunities.length > 1 ? (
                      <Form.Select
                        size="sm"
                        value={currentCommunityId || currentCommunity?.community_id || ''}
                        onChange={(e) => setCurrentCommunityId(e.target.value)}
                        style={{ minWidth: 180 }}
                      >
                        {approvedCommunities.map((item) => (
                          <option key={item.community_id} value={item.community_id}>
                            {item.community_name}
                          </option>
                        ))}
                      </Form.Select>
                    ) : (
                      <div className="small fw-semibold">{currentCommunity?.community_name}</div>
                    )}
                  </div>
                )}

                <div className="user-pill">
                  <span className="avatar-circle">{initials}</span>
                  <Link to="/profile" className="text-decoration-none text-dark">
                    {user.display_name || 'Perfil'}
                  </Link>
                </div>
                <Nav.Link onClick={handleLogout} className="nav-link-soft">
                  Salir
                </Nav.Link>
              </div>
            ) : (
              <div className="d-flex align-items-center gap-3">
                <Nav.Link as={Link} to="/login" className="nav-link-soft">
                  Iniciar sesión
                </Nav.Link>
                <Nav.Link as={Link} to="/register" className="nav-register">
                  Registrarse
                </Nav.Link>
              </div>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}
