/**
 * BuyerProfilePage.jsx — Buyer profile management.
 */
import React, { useState, useEffect } from 'react'
import Navbar from '../../components/Navigation/Navbar'
import { fetchBuyerProfile, updateBuyerProfile } from '../../api/auth'
import styles from './BuyerProfile.module.css'

export default function BuyerProfilePage() {
  const [profile, setProfile] = useState({
    company_name: '',
    business_type: 'Wholesaler',
    district: 'Rajkot',
    state: 'Gujarat',
    phone: '',
    gst_number: '',
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchBuyerProfile()
      .then((data) => {
        setProfile({
          company_name: data.company_name || '',
          business_type: data.business_type || 'Wholesaler',
          district: data.district || 'Rajkot',
          state: data.state || 'Gujarat',
          phone: data.phone || '',
          gst_number: data.gst_number || '',
        })
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setSuccess('')
    setError('')
    try {
      await updateBuyerProfile(profile)
      setSuccess('Buyer profile updated successfully!')
    } catch (err) {
      setError('Failed to update buyer profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        <div className="glass-panel" style={{ maxWidth: '640px', margin: '0 auto', width: '100%', padding: 'var(--sp-8)' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.25rem' }}>
            🏢 Buyer Profile &amp; Verification
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1.5rem' }}>
            Configure your enterprise details for verified direct farmer purchasing
          </p>

          {success && <div className="badge badge-emerald" style={{ padding: '0.6rem 1rem', marginBottom: '1rem', width: '100%' }}>{success}</div>}
          {error && <div className="badge badge-rose" style={{ padding: '0.6rem 1rem', marginBottom: '1rem', width: '100%' }}>{error}</div>}

          {loading ? (
            <div className="kl-loading-screen" style={{ minHeight: '200px' }}>
              <div className="kl-spinner" />
            </div>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase' }}>Company / Trading Name</label>
                <input
                  type="text"
                  value={profile.company_name}
                  onChange={(e) => setProfile({ ...profile, company_name: e.target.value })}
                  placeholder="e.g. Saurashtra Agro Exports Ltd"
                  required
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase' }}>Business Type</label>
                <select
                  value={profile.business_type}
                  onChange={(e) => setProfile({ ...profile, business_type: e.target.value })}
                >
                  <option value="Wholesaler">Wholesaler / Trader</option>
                  <option value="Ginning Mill">Ginning Mill / Spinning Mill</option>
                  <option value="Oil Mill">Oil Extraction Mill</option>
                  <option value="Processor">Food Processor / Exporter</option>
                  <option value="Commission Agent">Commission Agent / Broker</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase' }}>Primary District</label>
                  <input
                    type="text"
                    value={profile.district}
                    onChange={(e) => setProfile({ ...profile, district: e.target.value })}
                    required
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase' }}>State</label>
                  <input
                    type="text"
                    value={profile.state}
                    onChange={(e) => setProfile({ ...profile, state: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase' }}>Phone</label>
                  <input
                    type="tel"
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    placeholder="+91 98765 43210"
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase' }}>GST Number</label>
                  <input
                    type="text"
                    value={profile.gst_number}
                    onChange={(e) => setProfile({ ...profile, gst_number: e.target.value })}
                    placeholder="24AAAAA0000A1Z5"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-cyan"
                disabled={saving}
                style={{ marginTop: '0.5rem', padding: '0.85rem' }}
              >
                {saving ? 'Saving Profile…' : 'Save Buyer Profile'}
              </button>
            </form>
          )}
        </div>
      </main>
    </div>
  )
}
