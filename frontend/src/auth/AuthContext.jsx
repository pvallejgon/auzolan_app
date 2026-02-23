import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api/http.js'

const AuthContext = createContext(null)
const CURRENT_COMMUNITY_KEY = 'current_community_id'

function getApprovedCommunities(userData) {
  const communities = userData?.communities || []
  return communities.filter((item) => item.status === 'approved')
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentCommunityId, setCurrentCommunityIdState] = useState(null)

  const resolveCurrentCommunityId = (userData) => {
    const approved = getApprovedCommunities(userData)
    if (!approved.length) {
      return null
    }

    const stored = localStorage.getItem(CURRENT_COMMUNITY_KEY)
    if (stored) {
      const storedInt = Number(stored)
      if (approved.some((item) => item.community_id === storedInt)) {
        return storedInt
      }
    }

    return approved[0].community_id
  }

  const fetchMe = async () => {
    try {
      const res = await api.get('/me')
      setUser(res.data)
      const resolved = resolveCurrentCommunityId(res.data)
      setCurrentCommunityIdState(resolved)
      if (resolved) {
        localStorage.setItem(CURRENT_COMMUNITY_KEY, String(resolved))
      } else {
        localStorage.removeItem(CURRENT_COMMUNITY_KEY)
      }
    } catch {
      setUser(null)
      setCurrentCommunityIdState(null)
      localStorage.removeItem(CURRENT_COMMUNITY_KEY)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (localStorage.getItem('access')) {
      fetchMe()
    } else {
      setLoading(false)
    }

    const handler = () => {
      setUser(null)
      setCurrentCommunityIdState(null)
      localStorage.removeItem(CURRENT_COMMUNITY_KEY)
    }
    window.addEventListener('auth:logout', handler)
    return () => window.removeEventListener('auth:logout', handler)
  }, [])

  const login = async (email, password) => {
    const res = await api.post('/auth/token', { email, password })
    localStorage.setItem('access', res.data.access)
    localStorage.setItem('refresh', res.data.refresh)
    await fetchMe()
  }

  const register = async (payload) => {
    return api.post('/auth/register', payload)
  }

  const logout = () => {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem(CURRENT_COMMUNITY_KEY)
    setUser(null)
    setCurrentCommunityIdState(null)
  }

  const setCurrentCommunityId = (communityId) => {
    const approved = getApprovedCommunities(user)
    const parsed = Number(communityId)
    if (!approved.some((item) => item.community_id === parsed)) {
      return
    }

    setCurrentCommunityIdState(parsed)
    localStorage.setItem(CURRENT_COMMUNITY_KEY, String(parsed))
  }

  const currentCommunity = useMemo(() => {
    const approved = getApprovedCommunities(user)
    if (!approved.length) {
      return null
    }
    return approved.find((item) => item.community_id === currentCommunityId) || approved[0]
  }, [user, currentCommunityId])

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      logout,
      register,
      refreshMe: fetchMe,
      currentCommunity,
      currentCommunityId,
      setCurrentCommunityId,
    }),
    [user, loading, currentCommunity, currentCommunityId]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
