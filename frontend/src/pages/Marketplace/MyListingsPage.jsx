/**
 * MyListingsPage.jsx — Farmer Crop Listing Management & Inquiries Responder.
 */
import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../../components/Navigation/Navbar'
import StatusBadge from '../../components/UI/StatusBadge'
import { fetchMyListings, createCropListing, fetchReceivedInquiries, respondToInquiry } from '../../api/marketplace'
import { fetchCropLots } from '../../api/cropLots'
import styles from './Marketplace.module.css'

export default function MyListingsPage() {
  const [listings, setListings] = useState([])
  const [inquiries, setInquiries] = useState([])
  const [cropLots, setCropLots] = useState([])
  const [loading, setLoading] = useState(true)

  // New listing form modal
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [form, setForm] = useState({
    crop_lot: '',
    title: '',
    commodity: 'Cotton',
    quantity_quintal: '',
    expected_price_per_quintal: '',
    location_district: 'Rajkot',
    location_state: 'Gujarat',
    quality_grade: 'Grade A',
    description: '',
  })
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  // Inquiry response modal
  const [selectedInquiry, setSelectedInquiry] = useState(null)
  const [respondStatus, setRespondStatus] = useState('ACCEPTED')
  const [farmerNotes, setFarmerNotes] = useState('')
  const [responding, setResponding] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [listRes, inqRes, lotsRes] = await Promise.allSettled([
        fetchMyListings(),
        fetchReceivedInquiries(),
        fetchCropLots(),
      ])
      if (listRes.status === 'fulfilled') setListings(listRes.value?.results || listRes.value || [])
      if (inqRes.status === 'fulfilled') setInquiries(inqRes.value?.results || inqRes.value || [])
      if (lotsRes.status === 'fulfilled') setCropLots(lotsRes.value?.results || lotsRes.value || [])
    } finally {
      setLoading(false)
    }
  }

  function handleLotSelect(lotId) {
    const lot = cropLots.find((l) => String(l.id) === String(lotId))
    if (lot) {
      setForm((prev) => ({
        ...prev,
        crop_lot: lot.id,
        commodity: lot.commodity ? lot.commodity.charAt(0).toUpperCase() + lot.commodity.slice(1) : 'Cotton',
        quantity_quintal: lot.quantity || '',
        title: `${lot.commodity?.toUpperCase()} Lot (${lot.quantity} ${lot.unit})`,
        quality_grade: lot.quality_grade || 'Grade A',
      }))
    }
  }

  async function handleCreateListing(e) {
    e.preventDefault()
    setSaving(true)
    setFormError('')
    try {
      await createCropListing(form)
      setShowCreateModal(false)
      setForm({
        crop_lot: '',
        title: '',
        commodity: 'Cotton',
        quantity_quintal: '',
        expected_price_per_quintal: '',
        location_district: 'Rajkot',
        location_state: 'Gujarat',
        quality_grade: 'Grade A',
        description: '',
      })
      loadData()
    } catch (err) {
      setFormError(err?.response?.data?.error || 'Failed to create listing. Please check inputs.')
    } finally {
      setSaving(false)
    }
  }

  async function handleRespondSubmit(e) {
    e.preventDefault()
    setResponding(true)
    try {
      await respondToInquiry(selectedInquiry.id, respondStatus, farmerNotes)
      setSelectedInquiry(null)
      loadData()
    } catch (err) {
      alert('Failed to update inquiry status.')
    } finally {
      setResponding(false)
    }
  }

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        <div className={styles.headerRow}>
          <div className={styles.headerTitleGroup}>
            <h1>🌾 My Crop Listings &amp; Inquiries</h1>
            <p>Publish lots directly to Gujarat buyers and manage incoming purchase offers</p>
          </div>

          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
            + Create New Marketplace Listing
          </button>
        </div>

        {/* ── My Listings Section ── */}
        <section className="glass-panel" style={{ padding: 'var(--sp-6)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>
            📦 Published Crop Lots ({listings.length})
          </h2>

          {loading ? (
            <div className="kl-loading-screen" style={{ minHeight: '180px' }}>
              <div className="kl-spinner" />
            </div>
          ) : listings.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#94a3b8' }}>
              <p>You have not published any crop lots to the marketplace yet.</p>
              <button onClick={() => setShowCreateModal(true)} className="btn btn-primary" style={{ marginTop: '0.75rem' }}>
                + Publish Your First Lot
              </button>
            </div>
          ) : (
            <div className={styles.grid}>
              {listings.map((item) => (
                <div key={item.id} className={styles.card}>
                  <div className={styles.cardHeader}>
                    <span className={styles.commodityTag}>
                      {item.commodity?.toLowerCase() === 'cotton' ? '⚪' : '🥜'} {item.commodity}
                    </span>
                    <StatusBadge status={item.status} />
                  </div>

                  <h3 className={styles.cardTitle}>{item.title}</h3>

                  <div className={styles.detailsGrid}>
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>Quantity</span>
                      <span className={styles.detailVal}>{item.quantity_quintal} Qtl</span>
                    </div>
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>Asking Price</span>
                      <span className={styles.detailVal} style={{ color: '#38bdf8' }}>₹{item.expected_price_per_quintal}/Qtl</span>
                    </div>
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>District</span>
                      <span className={styles.detailVal}>{item.location_district}</span>
                    </div>
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>Inquiries</span>
                      <span className={styles.detailVal} style={{ color: '#34d399' }}>{item.inquiry_count || 0} offers</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* ── Incoming Buyer Inquiries Section ── */}
        <section className="glass-panel" style={{ padding: 'var(--sp-6)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-4)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>
            💬 Incoming Purchase Inquiries ({inquiries.length})
          </h2>

          {inquiries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#94a3b8' }}>
              <p>No inquiries received yet. When buyers submit purchase offers, they will appear here.</p>
            </div>
          ) : (
            <div className={styles.tableWrapper}>
              <table className={styles.table} style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Listing</th>
                    <th>Buyer Email</th>
                    <th>Offered Rate</th>
                    <th>Requested Qtl</th>
                    <th>Deal Valuation</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {inquiries.map((inq) => (
                    <tr key={inq.id}>
                      <td style={{ fontWeight: 600, color: '#ffffff' }}>{inq.listing_title}</td>
                      <td>{inq.buyer?.email}</td>
                      <td style={{ color: '#34d399', fontWeight: 700 }}>₹{inq.offered_price_per_quintal}/Qtl</td>
                      <td>{inq.requested_quantity_quintal} Qtl</td>
                      <td style={{ fontWeight: 700 }}>₹{(Number(inq.total_offered_value) || 0).toLocaleString('en-IN')}</td>
                      <td><StatusBadge status={inq.status} /></td>
                      <td>
                        {inq.status === 'PENDING' ? (
                          <button
                            onClick={() => {
                              setSelectedInquiry(inq)
                              setRespondStatus('ACCEPTED')
                              setFarmerNotes('')
                            }}
                            className="btn btn-primary"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
                          >
                            Respond / Accept
                          </button>
                        ) : (
                          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Processed</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* ── Create Listing Modal ── */}
        {showCreateModal && (
          <div className={styles.modalOverlay} onClick={() => setShowCreateModal(false)}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
              <div className={styles.modalHeader}>
                <h2 className={styles.modalTitle}>🌾 Publish Crop Lot</h2>
                <button className={styles.closeBtn} onClick={() => setShowCreateModal(false)}>✕</button>
              </div>

              {formError && <div className="badge badge-rose" style={{ padding: '0.5rem' }}>{formError}</div>}

              <form className={styles.modalForm} onSubmit={handleCreateListing}>
                {cropLots.length > 0 && (
                  <div className={styles.modalField}>
                    <label className={styles.modalLabel}>Link Existing Registered Crop Lot (Optional)</label>
                    <select
                      className={styles.modalInput}
                      value={form.crop_lot}
                      onChange={(e) => handleLotSelect(e.target.value)}
                    >
                      <option value="">-- Manual Listing (Or pick from crop lots) --</option>
                      {cropLots.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.commodity?.toUpperCase()} — {l.quantity} {l.unit} ({l.harvest_date})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Listing Title</label>
                  <input
                    type="text"
                    className={styles.modalInput}
                    placeholder="e.g. Shankar-6 Cotton Lot 50 Qtl"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    required
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div className={styles.modalField}>
                    <label className={styles.modalLabel}>Commodity</label>
                    <select
                      className={styles.modalInput}
                      value={form.commodity}
                      onChange={(e) => setForm({ ...form, commodity: e.target.value })}
                    >
                      <option value="Cotton">Cotton</option>
                      <option value="Groundnut">Groundnut</option>
                      <option value="Wheat">Wheat</option>
                      <option value="Mustard">Mustard</option>
                    </select>
                  </div>

                  <div className={styles.modalField}>
                    <label className={styles.modalLabel}>Quality Grade</label>
                    <input
                      type="text"
                      className={styles.modalInput}
                      value={form.quality_grade}
                      onChange={(e) => setForm({ ...form, quality_grade: e.target.value })}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div className={styles.modalField}>
                    <label className={styles.modalLabel}>Quantity (Quintals)</label>
                    <input
                      type="number"
                      step="0.01"
                      className={styles.modalInput}
                      value={form.quantity_quintal}
                      onChange={(e) => setForm({ ...form, quantity_quintal: e.target.value })}
                      required
                    />
                  </div>

                  <div className={styles.modalField}>
                    <label className={styles.modalLabel}>Asking Price (₹ / Qtl)</label>
                    <input
                      type="number"
                      step="1"
                      className={styles.modalInput}
                      value={form.expected_price_per_quintal}
                      onChange={(e) => setForm({ ...form, expected_price_per_quintal: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>District</label>
                  <input
                    type="text"
                    className={styles.modalInput}
                    value={form.location_district}
                    onChange={(e) => setForm({ ...form, location_district: e.target.value })}
                    required
                  />
                </div>

                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Description / Quality Details</label>
                  <textarea
                    rows={2}
                    className={styles.modalInput}
                    placeholder="Moisture < 8%, stored in warehouse, ready for instant pickup"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={saving}
                  style={{ width: '100%', padding: '0.85rem' }}
                >
                  {saving ? 'Publishing Lot…' : 'Publish to Marketplace'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ── Respond to Inquiry Modal ── */}
        {selectedInquiry && (
          <div className={styles.modalOverlay} onClick={() => setSelectedInquiry(null)}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
              <div className={styles.modalHeader}>
                <h2 className={styles.modalTitle}>💬 Respond to Inquiry</h2>
                <button className={styles.closeBtn} onClick={() => setSelectedInquiry(null)}>✕</button>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.04)', padding: '0.75rem', borderRadius: '8px' }}>
                <p style={{ fontSize: '0.85rem', color: '#ffffff', margin: 0 }}>
                  Offer: <strong>₹{selectedInquiry.offered_price_per_quintal}/Qtl</strong> for <strong>{selectedInquiry.requested_quantity_quintal} Qtl</strong>
                </p>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: '4px 0 0 0' }}>
                  Buyer message: &quot;{selectedInquiry.message || 'No note attached'}&quot;
                </p>
              </div>

              <form className={styles.modalForm} onSubmit={handleRespondSubmit}>
                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Decision</label>
                  <select
                    className={styles.modalInput}
                    value={respondStatus}
                    onChange={(e) => setRespondStatus(e.target.value)}
                  >
                    <option value="ACCEPTED">✅ Accept Offer (Mark Deal Pending)</option>
                    <option value="REJECTED">❌ Reject Offer</option>
                    <option value="CLOSED">🔒 Close Inquiry</option>
                  </select>
                </div>

                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Farmer Response / Pickup Note</label>
                  <textarea
                    rows={3}
                    className={styles.modalInput}
                    placeholder="e.g. Deal accepted. Pickup available at farm from Monday 10am."
                    value={farmerNotes}
                    onChange={(e) => setFarmerNotes(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={responding}
                  style={{ width: '100%', padding: '0.85rem' }}
                >
                  {responding ? 'Saving…' : 'Submit Response'}
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
