import { Container } from 'react-bootstrap'
import { useLocation } from 'react-router-dom'
import AppNavbar from './components/AppNavbar.jsx'
import AppRouter from './routes/AppRouter.jsx'
import { AuthProvider } from './auth/AuthContext.jsx'

export default function App() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <AuthProvider>
      <div className="app-shell">
        <AppNavbar />
        {isHome ? (
          <AppRouter />
        ) : (
          <Container className="py-4">
            <AppRouter />
          </Container>
        )}
      </div>
    </AuthProvider>
  )
}
