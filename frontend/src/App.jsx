import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

// Page stubs — full implementation in Phase 9
const LoginPage = React.lazy(() => import('./pages/Auth/LoginPage'))
const RegisterPage = React.lazy(() => import('./pages/Auth/RegisterPage'))
const DashboardPage = React.lazy(() => import('./pages/Dashboard/DashboardPage'))
const CropLotCreatePage = React.lazy(() => import('./pages/CropLot/CropLotCreatePage'))
const CropLotListPage = React.lazy(() => import('./pages/CropLot/CropLotListPage'))
const AnalysisPage = React.lazy(() => import('./pages/Analysis/AnalysisPage'))
const MarketListPage = React.lazy(() => import('./pages/Market/MarketListPage'))

function App() {
  return (
    <BrowserRouter>
      <React.Suspense fallback={<div className="loading">Loading…</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/crop-lots" element={<CropLotListPage />} />
          <Route path="/crop-lots/new" element={<CropLotCreatePage />} />
          <Route path="/analysis/:cropLotId" element={<AnalysisPage />} />
          <Route path="/markets" element={<MarketListPage />} />
        </Routes>
      </React.Suspense>
    </BrowserRouter>
  )
}

export default App
