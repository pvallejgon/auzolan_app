import { Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from '../pages/LoginPage.jsx'
import RegisterPage from '../pages/RegisterPage.jsx'
import RequestsListPage from '../pages/RequestsListPage.jsx'
import RequestCreatePage from '../pages/RequestCreatePage.jsx'
import RequestDetailPage from '../pages/RequestDetailPage.jsx'
import ChatPage from '../pages/ChatPage.jsx'
import ProfilePage from '../pages/ProfilePage.jsx'
import HomePage from '../pages/HomePage.jsx'
import CommunityMembersPage from '../pages/CommunityMembersPage.jsx'
import LoansListPage from '../pages/LoansListPage.jsx'
import LoanDetailPage from '../pages/LoanDetailPage.jsx'
import ReportsPage from '../pages/ReportsPage.jsx'
import { useAuth } from '../auth/AuthContext.jsx'
import { Spinner } from 'react-bootstrap'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="d-flex justify-content-center py-5">
        <Spinner />
      </div>
    )
  }
  if (!user) {
    return <Navigate to="/" replace />
  }
  return children
}

function HomeRoute() {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="d-flex justify-content-center py-5">
        <Spinner />
      </div>
    )
  }
  if (user) {
    return <Navigate to="/requests" replace />
  }
  return <HomePage />
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<HomeRoute />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/requests"
        element={
          <ProtectedRoute>
            <RequestsListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/requests/mine"
        element={
          <ProtectedRoute>
            <RequestsListPage mine />
          </ProtectedRoute>
        }
      />
      <Route
        path="/requests/new"
        element={
          <ProtectedRoute>
            <RequestCreatePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/requests/:id"
        element={
          <ProtectedRoute>
            <RequestDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/requests/:id/chat"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/loans"
        element={
          <ProtectedRoute>
            <LoansListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/loans/:id"
        element={
          <ProtectedRoute>
            <LoanDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/community/members"
        element={
          <ProtectedRoute>
            <CommunityMembersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
