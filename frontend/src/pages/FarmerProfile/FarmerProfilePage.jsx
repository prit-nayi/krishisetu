/**
 * FarmerProfilePage.jsx — View and edit the farmer's profile.
 */
import React, { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { fetchFarmerProfile, updateFarmerProfile, parseApiError } from '../../api/auth'
import styles from './FarmerProfile.module.css'

const IconAlert = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
)
const IconCheck = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
)

export default function FarmerProfilePage() {
  const { user } = useAuth()
  const [form, setForm] = useState({ district:'', taluka:'', village:'', pincode:'', latitude:'', longitude:'' })
  const [loading, setLoading]         = useState(true)
  const [saving, setSaving]           = useState(false)
  const [successMsg, setSuccessMsg]   = useState('')
  const [errorMsg, setErrorMsg]       = useState('')
  const [fieldErrors, setFieldErrors] = useState({})

  useEffect(() => {
    fetchFarmerProfile()
      .then((data) => {
        setForm({
          district:  data.district  || '',
          taluka:    data.taluka    || '',
          village:   data.village   || '',
          pincode:   data.pincode   || '',
          latitude:  data.latitude  != null ? String(data.latitude)  : '',
          longitude: data.longitude != null ? String(data.longitude) : '',
        })
      })
      .catch(() => setErrorMsg('Could not load your profile. Please refresh.'))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (fieldErrors[name]) setFieldErrors((prev) => ({ ...prev, [name]: '' }))
    if (successMsg) setSuccessMsg('')
    if (errorMsg)   setErrorMsg('')
  }

  function validate() {
    const errs = {}
    if (!form.district.trim()) errs.district = 'District is required.'
    if (!form.village.trim())  errs.village  = 'Village is required.'
    if (form.latitude  && isNaN(parseFloat(form.latitude)))  errs.latitude  = 'Must be a number.'
    if (form.longitude && isNaN(parseFloat(form.longitude))) errs.longitude = 'Must be a number.'
    return errs
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setFieldErrors(errs); return }
    setSaving(true)
    setSuccessMsg('')
    setErrorMsg('')
    try {
      const payload = { district: form.district.trim(), village: form.village.trim() }
      if (form.taluka.trim())    payload.taluka    = form.taluka.trim()
      if (form.pincode.trim())   payload.pincode   = form.pincode.trim()
      if (form.latitude.trim())  payload.latitude  = parseFloat(form.latitude)
      if (form.longitude.trim()) payload.longitude = parseFloat(form.longitude)
      await updateFarmerProfile(payload)
      setSuccessMsg('Profile updated successfully.')
    } catch (err) {
      setErrorMsg(parseApiError(err))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>
          <div className={styles.skeleton} />
          <div className={styles.skeleton} style={{ width:'60%', marginTop:'1rem' }} />
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.avatar} aria-hidden="true">
            {user?.username?.[0]?.toUpperCase() || '🌾'}
          </div>
          <div>
            <h1 className={styles.heading}>Farmer Profile</h1>
            <p className={styles.meta}>{user?.email} &bull; <span className={styles.badge}>{user?.role}</span></p>
          </div>
        </div>

        {successMsg && <div className={`${styles.alert} ${styles.alertSuccess}`} role="status"><IconCheck /> {successMsg}</div>}
        {errorMsg   && <div className={`${styles.alert} ${styles.alertError}`}   role="alert"><IconAlert /> {errorMsg}</div>}

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <h2 className={styles.sectionTitle}>📍 Location Details</h2>

          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="district">District <span className={styles.required}>*</span></label>
              <input id="district" name="district" type="text" placeholder="e.g. Rajkot"
                value={form.district} onChange={handleChange} disabled={saving}
                className={`${styles.input} ${fieldErrors.district ? styles.inputError : ''}`} />
              {fieldErrors.district && <span className={styles.fieldError}><IconAlert /> {fieldErrors.district}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="taluka">Taluka <span className={styles.labelOptional}>(optional)</span></label>
              <input id="taluka" name="taluka" type="text" placeholder="e.g. Gondal"
                value={form.taluka} onChange={handleChange} disabled={saving} className={styles.input} />
            </div>
          </div>

          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="village">Village <span className={styles.required}>*</span></label>
              <input id="village" name="village" type="text" placeholder="e.g. Gondal"
                value={form.village} onChange={handleChange} disabled={saving}
                className={`${styles.input} ${fieldErrors.village ? styles.inputError : ''}`} />
              {fieldErrors.village && <span className={styles.fieldError}><IconAlert /> {fieldErrors.village}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="pincode">Pincode <span className={styles.labelOptional}>(optional)</span></label>
              <input id="pincode" name="pincode" type="text" placeholder="e.g. 360311"
                value={form.pincode} onChange={handleChange} disabled={saving} className={styles.input} maxLength={10} />
            </div>
          </div>

          <h2 className={styles.sectionTitle} style={{ marginTop:'var(--sp-2)' }}>🗺️ GPS Coordinates <span className={styles.labelOptional}>(optional)</span></h2>
          <div className={styles.row}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="latitude">Latitude</label>
              <input id="latitude" name="latitude" type="text" placeholder="e.g. 22.1631"
                value={form.latitude} onChange={handleChange} disabled={saving}
                className={`${styles.input} ${fieldErrors.latitude ? styles.inputError : ''}`} />
              {fieldErrors.latitude && <span className={styles.fieldError}><IconAlert /> {fieldErrors.latitude}</span>}
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="longitude">Longitude</label>
              <input id="longitude" name="longitude" type="text" placeholder="e.g. 70.7934"
                value={form.longitude} onChange={handleChange} disabled={saving}
                className={`${styles.input} ${fieldErrors.longitude ? styles.inputError : ''}`} />
              {fieldErrors.longitude && <span className={styles.fieldError}><IconAlert /> {fieldErrors.longitude}</span>}
            </div>
          </div>

          <button type="submit" className={styles.saveBtn} disabled={saving}>
            {saving && <span className={styles.spinner} aria-hidden="true" />}
            {saving ? 'Saving…' : 'Save profile'}
          </button>
        </form>
      </div>
    </div>
  )
}
