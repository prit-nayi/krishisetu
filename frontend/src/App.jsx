/**
 * App.jsx — KrishiLink AI root router.
 */
import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute'

const LoginPage      = React.lazy(() => import('./pages/Auth/LoginPage'))
const RegisterPage   = React.lazy(() => import('./pages/Auth/RegisterPage'))
const FarmerProfilePage = React.lazy(() => import('./pages/FarmerProfile/FarmerProfilePage'))
const DashboardPage  = React.lazy(() => import('./pages/Dashboard/DashboardPage'))
const CropLotListPage   = React.lazy(() => import('./pages/CropLot/CropLotListPage'))
const CropLotCreatePage = React.lazy(() => import('./pages/CropLot/CropLotCreatePage'))
const CropLotDetailPage = React.lazy(() => import('./pages/CropLot/CropLotDetailPage'))
const AnalysisPage   = React.lazy(() => import('./pages/Analysis/AnalysisPage'))
const MarketListPage = React.lazy(() => import('./pages/Market/MarketListPage'))

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <React.Suspense
          fallback={
            <div className="kl-loading-screen" role="status" aria-live="polite">
              Loading…
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login"    element={<PublicRoute><LoginPage /></PublicRoute>} />
            <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
            <Route path="/dashboard"       element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
            <Route path="/farmer/profile"  element={<ProtectedRoute><FarmerProfilePage /></ProtectedRoute>} />
            <Route path="/crop-lots"           element={<ProtectedRoute><CropLotListPage /></ProtectedRoute>} />
            <Route path="/crop-lots/new"       element={<ProtectedRoute><CropLotCreatePage /></ProtectedRoute>} />
            <Route path="/crop-lots/:id/edit"  element={<ProtectedRoute><CropLotDetailPage /></ProtectedRoute>} />
            <Route path="/analysis/:cropLotId" element={<ProtectedRoute><AnalysisPage /></ProtectedRoute>} />
            <Route path="/markets"         element={<ProtectedRoute><MarketListPage /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </React.Suspense>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
