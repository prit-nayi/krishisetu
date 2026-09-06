/**
 * components/Navigation/Navbar.jsx — Futuristic glassmorphic navigation bar.
 * Adapts menu links dynamically based on user role (Farmer, Buyer, Admin).
 */
import React from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './Navbar.module.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const role = user?.role || 'farmer'

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        {/* Logo */}
        <Link to="/dashboard" className={styles.logo}>
          <div className={styles.logoIcon}>
            <span className={styles.logoPulse} />
            🌾
          </div>
          <div className={styles.brandText}>
            <span className={styles.brandTitle}>KrishiLink <span className={styles.aiGlow}>AI</span></span>
            <span className={styles.brandTag}>Gujarat Agri Intelligence</span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className={styles.navLinks}>
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
          >
            Dashboard
          </NavLink>

          {/* Farmer specific links */}
          {role === 'farmer' && (
            <>
              <NavLink
                to="/crop-lots"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                Crop Lots
              </NavLink>
              <NavLink
                to="/marketplace/my-listings"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                My Listings
              </NavLink>
              <NavLink
                to="/marketplace"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                Marketplace
              </NavLink>
              <NavLink
                to="/markets"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                APMC Mandis
              </NavLink>
            </>
          )}

          {/* Buyer specific links */}
          {role === 'buyer' && (
            <>
              <NavLink
                to="/marketplace"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                Live Marketplace
              </NavLink>
              <NavLink
                to="/marketplace/inquiries"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                My Inquiries
              </NavLink>
              <NavLink
                to="/markets"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                APMC Rates
              </NavLink>
            </>
          )}

          {/* Admin specific links */}
          {role === 'admin' && (
            <>
              <NavLink
                to="/admin/users"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                Users Directory
              </NavLink>
              <NavLink
                to="/marketplace"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                Marketplace
              </NavLink>
              <NavLink
                to="/markets"
                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
              >
                APMC Mandis
              </NavLink>
            </>
          )}
        </nav>

        {/* User profile & actions */}
        <div className={styles.userActions}>
          <div className={styles.userInfo}>
            <span className={styles.userEmail}>{user?.email || 'User'}</span>
            <span className={`${styles.roleBadge} ${styles[`role_${role}`]}`}>
              {role.toUpperCase()}
            </span>
          </div>

          <Link
            to={role === 'buyer' ? '/buyer/profile' : '/farmer/profile'}
            className={styles.profileBtn}
            title="Profile Settings"
          >
            ⚙️
          </Link>

          <button onClick={handleLogout} className={styles.logoutBtn} title="Sign Out">
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}
