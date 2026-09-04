/**
 * DashboardPage.jsx — Farmer home screen (Phase 1).
 */
import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './Dashboard.module.css'

const IconPlus = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>)
const IconMarket = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>)
const IconUser = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>)
const IconLogout = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>)
const IconCrop = () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 2a10 10 0 0 1 10 10"/><path d="M12 2v20"/><path d="M2 12h20"/><circle cx="12" cy="12" r="3"/></svg>)
const IconChevron = () => (<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>)

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning,'
  if (h < 17) return 'Good afternoon,'
  return 'Good evening,'
}

export default function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate          = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className={styles.page}>
      <nav className={styles.nav}>
        <div className={styles.navBrand}>
          <span className={styles.navLogo} aria-hidden="true">🌾</span>
          <span className={styles.navTitle}>KrishiLink AI</span>
        </div>
        <div className={styles.navActions}>
          <Link to="/farmer/profile" className={styles.navLink}><IconUser /> Profile</Link>
          <button onClick={handleLogout} className={styles.navLogout} aria-label="Log out">
            <IconLogout /> Log out
          </button>
        </div>
      </nav>

      <main className={styles.main}>
        {/* Welcome */}
        <section className={styles.welcome}>
          <div>
            <p className={styles.welcomeGreeting}>{getGreeting()}</p>
            <h1 className={styles.welcomeHeading}>{user?.username || 'Farmer'} 👋</h1>
            <p className={styles.welcomeSub}>Get the best price for your cotton &amp; groundnut — smart decisions, backed by data.</p>
          </div>
          <div className={styles.welcomeIllustration} aria-hidden="true">🌱</div>
        </section>

        {/* Quick actions */}
        <section className={styles.section}>
          <h2 className={styles.sectionHeading}>Quick actions</h2>
          <div className={styles.actionGrid}>
            <Link to="/crop-lots/new" className={`${styles.actionCard} ${styles.actionCardPrimary}`}>
              <div className={styles.actionIcon}><IconPlus /></div>
              <div className={styles.actionText}>
                <span className={styles.actionTitle}>Add Crop Lot</span>
                <span className={styles.actionDesc}>List your cotton or groundnut for analysis</span>
              </div>
              <span className={styles.actionChevron}><IconChevron /></span>
            </Link>
            <Link to="/markets" className={styles.actionCard}>
              <div className={styles.actionIcon}><IconMarket /></div>
              <div className={styles.actionText}>
                <span className={styles.actionTitle}>View Markets</span>
                <span className={styles.actionDesc}>Browse current APMC prices near you</span>
              </div>
              <span className={styles.actionChevron}><IconChevron /></span>
            </Link>
            <Link to="/crop-lots" className={styles.actionCard}>
              <div className={styles.actionIcon}><IconCrop /></div>
              <div className={styles.actionText}>
                <span className={styles.actionTitle}>My Crop Lots</span>
                <span className={styles.actionDesc}>View and manage your active lots</span>
              </div>
              <span className={styles.actionChevron}><IconChevron /></span>
            </Link>
            <Link to="/farmer/profile" className={styles.actionCard}>
              <div className={styles.actionIcon}><IconUser /></div>
              <div className={styles.actionText}>
                <span className={styles.actionTitle}>Edit Profile</span>
                <span className={styles.actionDesc}>Update location for accurate market matching</span>
              </div>
              <span className={styles.actionChevron}><IconChevron /></span>
            </Link>
          </div>
        </section>

        {/* Phase notice */}
        <section className={styles.phaseNotice}>
          <div className={styles.phaseNoticeInner}>
            <span className={styles.phaseTag}>Phase 1 ✓</span>
            <p>Authentication is live. <strong>Crop lot analysis, market prices, and AI recommendations</strong> are coming in the next phases.</p>
          </div>
        </section>

        {/* Account card */}
        <section className={styles.section}>
          <h2 className={styles.sectionHeading}>Account</h2>
          <div className={styles.accountCard}>
            <div className={styles.accountAvatar} aria-hidden="true">
              {user?.username?.[0]?.toUpperCase() || '🌾'}
            </div>
            <div className={styles.accountInfo}>
              <p className={styles.accountName}>{user?.username}</p>
              <p className={styles.accountEmail}>{user?.email}</p>
            </div>
            <span className={styles.roleBadge}>{user?.role}</span>
          </div>
        </section>
      </main>
    </div>
  )
}
