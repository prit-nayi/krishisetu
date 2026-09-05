/**
 * RegisterPage.jsx — Phase 1 Registration UI.
 */
import React, { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { parseApiError } from '../../api/auth'
import styles from './Auth.module.css'

const IconUser = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconEmail = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="2" y="4" width="20" height="16" rx="2"/>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
  </svg>
)
const IconPhone = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 14a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.62 3h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 10.56a16 16 0 0 0 6.07 6.07l.55-.55a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>
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

function isValidEmail(e) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim()) }
function isValidPhone(p) { return /^[+\d][\d\s\-()]{8,14}$/.test(p.trim()) }

function getPasswordStrength(password) {
  if (!password) return { score: -1, label: '' }
  let score = 0
  if (password.length >= 8) score++
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++
  if (/\d/.test(password) && /[^A-Za-z0-9]/.test(password)) score++
  if (score <= 1) return { score: 0, label: 'Weak' }
  if (score === 2) return { score: 1, label: 'Fair' }
  return { score: 2, label: 'Strong' }
}
const STRENGTH_CLASS = [styles.strengthWeak, styles.strengthFair, styles.strengthStrong]

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate      = useNavigate()

  const [form, setForm]     = useState({ username:'', email:'', phone:'', password:'', password_confirm:'' })
  const [errors, setErrors] = useState({})
  const [apiError, setApiError] = useState('')
  const [loading, setLoading]   = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const strength = useMemo(() => getPasswordStrength(form.password), [form.password])

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
    if (apiError) setApiError('')
  }

  function validate() {
    const errs = {}
    if (!form.username.trim())           errs.username = 'Username is required.'
    else if (form.username.trim().length < 3) errs.username = 'At least 3 characters.'
    else if (/\s/.test(form.username))   errs.username = 'No spaces allowed.'
    if (!form.email.trim())              errs.email = 'Email is required.'
    else if (!isValidEmail(form.email))  errs.email = 'Enter a valid email address.'
    if (form.phone.trim() && !isValidPhone(form.phone)) errs.phone = 'Enter a valid phone number.'
    if (!form.password)                  errs.password = 'Password is required.'
    else if (form.password.length < 8)   errs.password = 'At least 8 characters required.'
    if (!form.password_confirm)          errs.password_confirm = 'Please confirm your password.'
    else if (form.password !== form.password_confirm) errs.password_confirm = 'Passwords do not match.'
    return errs
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setLoading(true)
    setApiError('')
    try {
      const payload = {
        username: form.username.trim(),
        email: form.email.trim(),
        password: form.password,
        password_confirm: form.password_confirm,
        role: 'farmer',
      }
      if (form.phone.trim()) payload.phone = form.phone.trim()
      await register(payload)
      navigate('/dashboard', { replace: true })
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
          <div className={styles.brandTagline}>Smart market decisions for cotton &amp; groundnut farmers</div>
        </div>

        <h1 className={styles.heading}>Create your account</h1>
        <p className={styles.subheading}>Free for farmers. No credit card required.</p>

        {apiError && (
          <div className={`${styles.alert} ${styles.alertError}`} role="alert">
            <span className={styles.alertIcon}><IconAlert /></span>
            <span style={{ whiteSpace: 'pre-line' }}>{apiError}</span>
          </div>
        )}

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          {/* Username */}
          <div className={styles.field}>
            <label className={styles.label} htmlFor="username">Username</label>
            <div className={styles.inputWrapper}>
              <span className={styles.inputIcon}><IconUser /></span>
              <input id="username" name="username" type="text" autoComplete="username" autoFocus
                placeholder="e.g. ramesh_patel" value={form.username} onChange={handleChange}
                className={`${styles.input} ${errors.username ? styles.inputError : ''}`}
                aria-describedby={errors.username ? 'username-error' : undefined}
                aria-invalid={!!errors.username} disabled={loading} />
            </div>
            {errors.username && <span id="username-error" className={styles.fieldError} role="alert"><IconAlert /> {errors.username}</span>}
          </div>

          {/* Email */}
          <div className={styles.field}>
            <label className={styles.label} htmlFor="reg-email">Email address</label>
            <div className={styles.inputWrapper}>
              <span className={styles.inputIcon}><IconEmail /></span>
              <input id="reg-email" name="email" type="email" autoComplete="email"
                placeholder="you@example.com" value={form.email} onChange={handleChange}
                className={`${styles.input} ${errors.email ? styles.inputError : ''}`}
                aria-describedby={errors.email ? 'reg-email-error' : undefined}
                aria-invalid={!!errors.email} disabled={loading} />
            </div>
            {errors.email && <span id="reg-email-error" className={styles.fieldError} role="alert"><IconAlert /> {errors.email}</span>}
          </div>

          {/* Phone */}
          <div className={styles.field}>
            <label className={styles.label} htmlFor="phone">
              Phone number <span className={styles.labelOptional}>(optional)</span>
            </label>
            <div className={styles.inputWrapper}>
              <span className={styles.inputIcon}><IconPhone /></span>
              <input id="phone" name="phone" type="tel" autoComplete="tel"
                placeholder="+91 98765 43210" value={form.phone} onChange={handleChange}
                className={`${styles.input} ${errors.phone ? styles.inputError : ''}`}
                aria-describedby={errors.phone ? 'phone-error' : undefined}
                aria-invalid={!!errors.phone} disabled={loading} />
            </div>
            {errors.phone && <span id="phone-error" className={styles.fieldError} role="alert"><IconAlert /> {errors.phone}</span>}
          </div>

          {/* Password */}
          <div className={styles.field}>
            <label className={styles.label} htmlFor="reg-password">Password</label>
            <div className={styles.inputWrapper}>
              <span className={styles.inputIcon}><IconLock /></span>
              <input id="reg-password" name="password"
                type={showPass ? 'text' : 'password'} autoComplete="new-password"
                placeholder="At least 8 characters" value={form.password} onChange={handleChange}
                className={`${styles.input} ${styles.inputPassword} ${errors.password ? styles.inputError : ''}`}
                aria-invalid={!!errors.password} disabled={loading} />
              <button type="button" className={styles.inputToggle}
                onClick={() => setShowPass((v) => !v)}
                aria-label={showPass ? 'Hide password' : 'Show password'}>
                {showPass ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
            {form.password && strength.score >= 0 && (
              <div aria-live="polite">
                <div className={styles.strengthBar} aria-hidden="true">
                  <div className={`${styles.strengthFill} ${STRENGTH_CLASS[strength.score]}`} />
                </div>
                <p className={styles.strengthText}>Password strength: <strong>{strength.label}</strong></p>
              </div>
            )}
            {errors.password && <span className={styles.fieldError} role="alert"><IconAlert /> {errors.password}</span>}
          </div>

          {/* Confirm password */}
          <div className={styles.field}>
            <label className={styles.label} htmlFor="password-confirm">Confirm password</label>
            <div className={styles.inputWrapper}>
              <span className={styles.inputIcon}><IconLock /></span>
              <input id="password-confirm" name="password_confirm"
                type={showConfirm ? 'text' : 'password'} autoComplete="new-password"
                placeholder="Re-enter your password" value={form.password_confirm} onChange={handleChange}
                className={`${styles.input} ${styles.inputPassword} ${errors.password_confirm ? styles.inputError : ''}`}
                aria-invalid={!!errors.password_confirm} disabled={loading} />
              <button type="button" className={styles.inputToggle}
                onClick={() => setShowConfirm((v) => !v)}
                aria-label={showConfirm ? 'Hide password' : 'Show password'}>
                {showConfirm ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
            {errors.password_confirm && <span className={styles.fieldError} role="alert"><IconAlert /> {errors.password_confirm}</span>}
          </div>

          <button type="submit" className={styles.submitBtn} disabled={loading} aria-busy={loading}>
            {loading && <span className={styles.spinner} aria-hidden="true" />}
            {loading ? 'Creating account…' : 'Create free account'}
          </button>

          <p className={styles.terms}>By registering you agree to KrishiLink AI&apos;s terms of service.</p>
        </form>

        <p className={styles.footer}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
