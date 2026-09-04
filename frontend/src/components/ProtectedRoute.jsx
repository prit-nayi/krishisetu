/**
 * components/ProtectedRoute.jsx + PublicRoute
 */
import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()
  if (loading) return <div className="kl-loading-screen" role="status">Loading…</div>
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

export function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return <div className="kl-loading-screen" role="status">Loading…</div>
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return children
}
