import { Container, Nav, Navbar } from 'react-bootstrap'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { UI_ICONS } from '../data/icons.js'

export default function AppNavbar() {
  const { user, logout } = useAuth()
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

  return (
    <Navbar expand="lg" className="navbar-clean" sticky="top">
      <Container>
        <Navbar.Brand as={Link} to="/" className="d-flex align-items-center">
          <span className="brand-mark">
            <i className={`fi ${UI_ICONS.heart}`} />
          </span>
          <span className="brand-title">AuzolanApp</span>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="main-nav" />
        <Navbar.Collapse id="main-nav">
          <Nav className="mx-auto gap-3">
            {user && (
              <>
                <Nav.Link as={NavLink} to="/requests" className="nav-pill">
                  Peticiones
                </Nav.Link>
                <Nav.Link as={NavLink} to="/requests/mine" className="nav-link-soft">
                  Mis peticiones
                </Nav.Link>
                <Nav.Link className="nav-link-soft nav-disabled" aria-disabled="true">
                  Préstamos
                </Nav.Link>
              </>
            )}
          </Nav>
          <Nav className="ms-auto">
            {user ? (
              <div className="d-flex align-items-center gap-3">
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
