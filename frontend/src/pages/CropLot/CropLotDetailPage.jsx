/**
 * CropLotDetailPage.jsx — View and edit an existing crop lot.
 * Route: /crop-lots/:id/edit
 */
import React, { useState, useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Navbar from '../../components/Navigation/Navbar'
import { fetchCropLot, updateCropLot, parseApiError } from '../../api/cropLots'
import styles from './CropLot.module.css'

/* ── Icons ────────────────────────────────────────────────────────────────── */
const IconBack   = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
const IconUser   = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
const IconLogout = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>

/* ── Same field constants as Create ──────────────────────────────────────── */
const UNIT_OPTIONS    = [{ value:'quintal',label:'Quintal'},{ value:'kg',label:'Kilogram'},{ value:'tonne',label:'Tonne'}]
const QUALITY_OPTIONS = [{ value:'',label:'Not specified'},{ value:'A',label:'Grade A – Premium'},{ value:'B',label:'Grade B – Standard'},{ value:'C',label:'Grade C – Below Standard'}]
const STORAGE_OPTIONS = [{ value:'farm',label:'At Farm'},{ value:'warehouse',label:'Warehouse'},{ value:'cold_storage',label:'Cold Storage'}]

/* ── Validation ───────────────────────────────────────────────────────────── */
function validate(form) {
  const errors = {}
  if (!form.quantity)     errors.quantity     = 'Quantity is required.'
  else if (Number(form.quantity) <= 0) errors.quantity = 'Quantity must be greater than zero.'
  if (!form.harvest_date) errors.harvest_date = 'Harvest date is required.'
  if (form.moisture_percent !== '' && form.moisture_percent !== null) {
    const v = Number(form.moisture_percent)
    if (v < 0 || v > 100) errors.moisture_percent = 'Must be between 0 and 100.'
  }
  return errors
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' })
}

/* ── Page ─────────────────────────────────────────────────────────────────── */
export default function CropLotDetailPage() {
  const { id }       = useParams()
  const { logout }   = useAuth()
  const navigate     = useNavigate()
  const queryClient  = useQueryClient()

  const { data: lot, isLoading, isError, error } = useQuery({
    queryKey: ['cropLot', id],
    queryFn:  () => fetchCropLot(id),
  })

  const [form, setForm]           = useState(null)
  const [errors, setErrors]       = useState({})
  const [serverError, setServerError] = useState('')
  const [saved, setSaved]         = useState(false)

  /* Pre-fill form when lot loads */
  useEffect(() => {
    if (lot) {
      setForm({
        commodity:          lot.commodity,
        variety:            lot.variety ?? '',
        quantity:           lot.quantity,
        unit:               lot.unit,
        moisture_percent:   lot.moisture_percent ?? '',
        quality_grade:      lot.quality_grade ?? '',
        harvest_date:       lot.harvest_date,
        storage_status:     lot.storage_status,
        storage_start_date: lot.storage_start_date ?? '',
        notes:              lot.notes ?? '',
      })
    }
  }, [lot])

  const mutation = useMutation({
    mutationFn: (payload) => updateCropLot(id, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['cropLot', id], updated)
      queryClient.invalidateQueries({ queryKey: ['cropLots'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
    onError: (err) => {
      setServerError(parseApiError(err))
    },
  })

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: undefined }))
    setServerError('')
    setSaved(false)
  }

  function handleSubmit(e) {
    e.preventDefault()
    const validationErrors = validate(form)
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    const payload = { ...form }
    // Clean empty optional strings to null-ish (backend treats blank as null for optional fields)
    if (!payload.variety)            delete payload.variety
    if (!payload.moisture_percent)   delete payload.moisture_percent
    if (!payload.quality_grade)      delete payload.quality_grade
    if (!payload.storage_start_date) delete payload.storage_start_date
    if (!payload.notes)              delete payload.notes
    // commodity is not editable after creation
    delete payload.commodity

    mutation.mutate(payload)
  }

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const isBusy = mutation.isPending

  /* ── Render ──────────────────────────────────────────────────────────────── */
  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerText}>
            <h1>Edit Crop Lot</h1>
            {lot && <p>{lot.commodity_display} — added {formatDate(lot.created_at)}</p>}
          </div>
          <Link to="/crop-lots" className={styles.btnSecondary}>
            <IconBack /> Back to lots
          </Link>
        </div>

        {/* Loading */}
        {isLoading && <div className={styles.loadingCenter}><div className={styles.spinnerDark} aria-label="Loading…" /></div>}

        {/* Fetch error */}
        {isError && (
          <div className={styles.errorBox} role="alert">
            {parseApiError(error)}
          </div>
        )}

        {/* Form */}
        {!isLoading && !isError && form && (
          <div className={styles.formCard}>
            {saved && (
              <div className={`${styles.alert} ${styles.alertSuccess}`} role="status">
                ✓ Changes saved successfully.
              </div>
            )}
            {serverError && (
              <div className={`${styles.alert} ${styles.alertError}`} role="alert">
                {serverError}
              </div>
            )}

            {/* Read-only commodity banner */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              marginBottom: '1.5rem', padding: '0.5rem 0.75rem',
              background: 'var(--clr-surface-raised)',
              border: '1px solid var(--clr-border)',
              borderRadius: 'var(--radius)', fontSize: 'var(--font-size-sm)',
              color: 'var(--clr-text-muted)',
            }}>
              <span>Commodity:</span>
              <strong style={{ color: 'var(--clr-text)' }}>{lot.commodity_display}</strong>
              <span style={{ marginLeft: 'auto', fontSize: 'var(--font-size-xs)' }}>
                Commodity cannot be changed after creation
              </span>
            </div>

            <form onSubmit={handleSubmit} noValidate>
              <div className={styles.formGrid}>

                {/* Variety */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="variety">
                    Variety <span className={styles.labelOptional}>(optional)</span>
                  </label>
                  <input id="variety" name="variety" type="text"
                    placeholder="e.g. Shankar-6, Bold"
                    value={form.variety} onChange={handleChange}
                    className={styles.input} disabled={isBusy} />
                </div>

                {/* Quantity */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="quantity">
                    Quantity <span style={{ color:'var(--clr-error)' }}>*</span>
                  </label>
                  <input id="quantity" name="quantity" type="number"
                    min="0.01" step="0.01"
                    value={form.quantity} onChange={handleChange}
                    className={`${styles.input}${errors.quantity ? ' '+styles.inputError : ''}`}
                    disabled={isBusy} />
                  {errors.quantity && <span className={styles.fieldError}>{errors.quantity}</span>}
                </div>

                {/* Unit */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="unit">Unit</label>
                  <select id="unit" name="unit" value={form.unit}
                    onChange={handleChange} className={styles.select} disabled={isBusy}>
                    {UNIT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>

                {/* Harvest date */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="harvest_date">
                    Harvest Date <span style={{ color:'var(--clr-error)' }}>*</span>
                  </label>
                  <input id="harvest_date" name="harvest_date" type="date"
                    value={form.harvest_date} onChange={handleChange}
                    max={new Date().toISOString().split('T')[0]}
                    className={`${styles.input}${errors.harvest_date ? ' '+styles.inputError : ''}`}
                    disabled={isBusy} />
                  {errors.harvest_date && <span className={styles.fieldError}>{errors.harvest_date}</span>}
                </div>

                {/* Moisture */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="moisture_percent">
                    Moisture % <span className={styles.labelOptional}>(optional)</span>
                  </label>
                  <input id="moisture_percent" name="moisture_percent" type="number"
                    min="0" max="100" step="0.1" placeholder="e.g. 8.5"
                    value={form.moisture_percent} onChange={handleChange}
                    className={`${styles.input}${errors.moisture_percent ? ' '+styles.inputError : ''}`}
                    disabled={isBusy} />
                  {errors.moisture_percent && <span className={styles.fieldError}>{errors.moisture_percent}</span>}
                </div>

                {/* Quality grade */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="quality_grade">
                    Quality Grade <span className={styles.labelOptional}>(optional)</span>
                  </label>
                  <select id="quality_grade" name="quality_grade" value={form.quality_grade}
                    onChange={handleChange} className={styles.select} disabled={isBusy}>
                    {QUALITY_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>

                {/* Storage status */}
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="storage_status">Storage Status</label>
                  <select id="storage_status" name="storage_status" value={form.storage_status}
                    onChange={handleChange} className={styles.select} disabled={isBusy}>
                    {STORAGE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>

                {/* Storage start date */}
                {form.storage_status !== 'farm' && (
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor="storage_start_date">
                      In Storage Since <span className={styles.labelOptional}>(optional)</span>
                    </label>
                    <input id="storage_start_date" name="storage_start_date" type="date"
                      value={form.storage_start_date} onChange={handleChange}
                      max={new Date().toISOString().split('T')[0]}
                      className={styles.input} disabled={isBusy} />
                  </div>
                )}

                {/* Notes */}
                <div className={`${styles.field} ${styles.formGridFull}`}>
                  <label className={styles.label} htmlFor="notes">
                    Notes <span className={styles.labelOptional}>(optional)</span>
                  </label>
                  <textarea id="notes" name="notes"
                    placeholder="Any additional details…"
                    value={form.notes} onChange={handleChange}
                    className={styles.textarea} disabled={isBusy} />
                </div>
              </div>

              <div className={styles.formActions}>
                <Link to="/crop-lots" className={styles.btnSecondary}>Cancel</Link>
                <button type="submit" className={styles.btnPrimary} disabled={isBusy}>
                  {isBusy
                    ? <><span className={styles.spinner} aria-hidden="true" /> Saving…</>
                    : 'Save changes'}
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  )
}
