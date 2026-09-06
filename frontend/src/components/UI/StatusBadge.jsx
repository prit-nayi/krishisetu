/**
 * components/UI/StatusBadge.jsx — High-contrast glowing status pill badges.
 */
import React from 'react'

export default function StatusBadge({ status, label }) {
  if (!status) return null

  const s = String(status).toUpperCase()
  let badgeClass = 'badge-glass'
  let displayLabel = label || s

  switch (s) {
    case 'ACTIVE':
    case 'SELL_NOW':
    case 'ACCEPTED':
    case 'HIGH':
    case 'COMPLETED':
      badgeClass = 'badge-emerald'
      break
    case 'PENDING':
    case 'HOLD':
    case 'MEDIUM':
    case 'PARTIAL_SELL':
    case 'PENDING_DEAL':
      badgeClass = 'badge-amber'
      break
    case 'REJECTED':
    case 'CLOSED':
    case 'SOLD':
    case 'DELISTED':
    case 'INSUFFICIENT':
    case 'LOW':
      badgeClass = 'badge-rose'
      break
    case 'BUYER':
    case 'COTTON':
      badgeClass = 'badge-cyan'
      break
    case 'FARMER':
    case 'GROUNDNUT':
      badgeClass = 'badge-emerald'
      break
    case 'ADMIN':
      badgeClass = 'badge-purple'
      break
    default:
      badgeClass = 'badge-glass'
  }

  return <span className={`badge ${badgeClass}`}>{displayLabel}</span>
}
