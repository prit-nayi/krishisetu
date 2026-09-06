/**
 * components/UI/MetricCard.jsx — Futuristic KPI metric card.
 */
import React from 'react'

export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
  accent = 'emerald', // emerald | cyan | amber | rose | purple
  badge,
}) {
  const accentGlow = {
    emerald: 'rgba(16, 185, 129, 0.25)',
    cyan: 'rgba(6, 182, 212, 0.25)',
    amber: 'rgba(245, 158, 11, 0.25)',
    rose: 'rgba(244, 63, 94, 0.25)',
    purple: 'rgba(139, 92, 246, 0.25)',
  }[accent] || 'rgba(16, 185, 129, 0.25)'

  const accentColor = {
    emerald: '#34d399',
    cyan: '#38bdf8',
    amber: '#fbbf24',
    rose: '#fb7185',
    purple: '#c084fc',
  }[accent] || '#34d399'

  return (
    <div
      className="glass-panel glass-panel-hover"
      style={{
        padding: '1.25rem 1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.65rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '3px',
          background: `linear-gradient(90deg, ${accentColor} 0%, transparent 100%)`,
        }}
      />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--clr-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {title}
        </span>
        {icon && (
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: accentGlow,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.1rem',
            }}
          >
            {icon}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
        <span style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
          {value}
        </span>
        {badge && <span>{badge}</span>}
      </div>

      {subtitle && (
        <span style={{ fontSize: '0.8rem', color: 'var(--clr-text-secondary)' }}>
          {subtitle}
        </span>
      )}
    </div>
  )
}
