/**
 * LoginPage.jsx — Multi-Role Login with Instant Hackathon Demo Presets.
 */
import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { parseApiError } from '../../api/auth'
import styles from './Auth.module.css'

const IconEmail = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="2" y="4" width="20" height="16" rx="2"/>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
  </svg>
)
const IconLock = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
)
const IconEye = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
)
const IconEyeOff = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
)
const IconAlert = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
)

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [apiError, setApiError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPass, setShowPass] = useState(false)

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
    if (apiError) setApiError('')
  }

  function handleDemoFill(role) {
    if (role === 'farmer') {
      setForm({ email: 'farmer_demo@krishilink.in', password: 'Password123!' })
    } else if (role === 'buyer') {
      setForm({ email: 'buyer_demo@krishilink.in', password: 'Password123!' })
    } else if (role === 'admin') {
      setForm({ email: 'admin_demo@krishilink.in', password: 'Password123!' })
    }
    setErrors({})
    setApiError('')
  }

  function validate() {
    const errs = {}
    if (!form.email.trim()) errs.email = 'Email is required.'
    else if (!isValidEmail(form.email)) errs.email = 'Enter a valid email address.'
    if (!form.password) errs.password = 'Password is required.'
    return errs
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) {
      setErrors(errs)
      return
    }
    setLoading(true)
    setApiError('')
    try {
      await login(form.email.trim(), form.password)
      navigate(from, { replace: true })
    } catch (err) {
      setApiError(parseApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.brand}>
          <div className={styles.brandIcon} aria-hidden="true">🌾</div>
          <div className={styles.brandName}>KrishiLink AI</div>
          <div className={styles.brandTagline}>Autonomous Agricultural Market Intelligence</div>
        </div>

        <h1 className={styles.heading}>Sign In</h1>
        <p className={styles.subheading}>Access farmer intelligence &amp; buyer marketplace</p>

        {apiError && (
          <div className={`${styles.alert} ${styles.alertError}`} role="alert">
            <span className={styles.alertIcon}><IconAlert /></span>
            <span style={{ whiteSpace: 'pre-line' }}>{apiError}</span>
          </div>
        )}

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          {/* Email */}
          <div className={styles.field}>
            <label className={styles.label} htmlFor="email">Email Address</label>
            <div className={styles.inputWrapper}>
              <span className={styles.inputIcon}><IconEmail /></span>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                autoFocus
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
                className={`${styles.input} ${errors.email ? styles.inputError : ''}`}
                aria-describedby={errors.email ? 'email-error' : undefined}
                aria-invalid={!!errors.email}
                disabled={loading}
              />
            </div>
            {errors.email && (
              <span id="email-error" className={styles.fieldError} role="alert">
                <IconAlert /> {errors.email}
              </span>
            )}
          </div>

          {/* Password */}
          <div className={styles.field}>
            <label className={styles.label} htmlFor="password">Password</label>
            <div className={styles.inputWrapper}>
              <span className={styles.inputIcon}><IconLock /></span>
              <input
                id="password"
                name="password"
                type={showPass ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Your password"
                value={form.password}
                onChange={handleChange}
                className={`${styles.input} ${styles.inputPassword} ${errors.password ? styles.inputError : ''}`}
                aria-describedby={errors.password ? 'password-error' : undefined}
                aria-invalid={!!errors.password}
                disabled={loading}
              />
              <button
                type="button"
                className={styles.inputToggle}
                onClick={() => setShowPass((v) => !v)}
                aria-label={showPass ? 'Hide password' : 'Show password'}
              >
                {showPass ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
            {errors.password && (
              <span id="password-error" className={styles.fieldError} role="alert">
                <IconAlert /> {errors.password}
              </span>
            )}
          </div>

          <button type="submit" className={styles.submitBtn} disabled={loading} aria-busy={loading}>
            {loading && <span className={styles.spinner} aria-hidden="true" />}
            {loading ? 'Authenticating…' : 'Sign In'}
          </button>
        </form>

        {/* Demo Quick Logins for Hackathon Judges */}
        <div className={styles.demoBox}>
          <span className={styles.demoTitle}>⚡ Instant Demo Credentials</span>
          <div className={styles.demoButtons}>
            <button type="button" onClick={() => handleDemoFill('farmer')} className={styles.demoBtn}>
              🌾 Farmer
            </button>
            <button type="button" onClick={() => handleDemoFill('buyer')} className={styles.demoBtn}>
              🏢 Buyer
            </button>
            <button type="button" onClick={() => handleDemoFill('admin')} className={styles.demoBtn}>
              🛡️ Admin
            </button>
          </div>
        </div>

        <p className={styles.footer}>
          Don&apos;t have an account?{' '}
          <Link to="/register">Create one free</Link>
        </p>
      </div>
    </div>
  )
}
