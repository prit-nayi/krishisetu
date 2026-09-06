/**
 * MarketplacePage.jsx — Live Direct Marketplace for Farmers & Buyers.
 */
import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Navbar from '../../components/Navigation/Navbar'
import StatusBadge from '../../components/UI/StatusBadge'
import { fetchMarketplaceListings, createBuyerInquiry } from '../../api/marketplace'
import styles from './Marketplace.module.css'

export default function MarketplacePage() {
  const { user } = useAuth()
  const role = user?.role || 'farmer'

  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [commodityFilter, setCommodityFilter] = useState('')
  const [districtFilter, setDistrictFilter] = useState('')

  // Inquiry modal state
  const [selectedListing, setSelectedListing] = useState(null)
  const [inquiryForm, setInquiryForm] = useState({
    offered_price_per_quintal: '',
    requested_quantity_quintal: '',
    message: '',
    contact_phone: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [modalSuccess, setModalSuccess] = useState('')
  const [modalError, setModalError] = useState('')

  useEffect(() => {
    loadListings()
  }, [commodityFilter, districtFilter])

  async function loadListings() {
    setLoading(true)
    try {
      const params = {}
      if (commodityFilter) params.commodity = commodityFilter
      if (districtFilter) params.location_district = districtFilter
      const res = await fetchMarketplaceListings(params)
      setListings(res?.results || res || [])
    } finally {
      setLoading(false)
    }
  }

  function handleOpenInquiry(listing) {
    setSelectedListing(listing)
    setInquiryForm({
      offered_price_per_quintal: listing.expected_price_per_quintal || '',
      requested_quantity_quintal: listing.quantity_quintal || '',
      message: 'Interested in purchasing this lot. Please confirm pickup schedule.',
      contact_phone: user?.phone || '',
    })
    setModalSuccess('')
    setModalError('')
  }

  async function handleSendInquiry(e) {
    e.preventDefault()
    setSubmitting(true)
    setModalError('')
    setModalSuccess('')
    try {
      await createBuyerInquiry({
        listing: selectedListing.id,
        offered_price_per_quintal: inquiryForm.offered_price_per_quintal,
        requested_quantity_quintal: inquiryForm.requested_quantity_quintal,
        message: inquiryForm.message,
        contact_phone: inquiryForm.contact_phone,
      })
      setModalSuccess('Inquiry submitted successfully! The farmer will review your offer.')
      setTimeout(() => {
        setSelectedListing(null)
      }, 1500)
    } catch (err) {
      setModalError(err?.response?.data?.error || 'Failed to submit inquiry. Please verify details.')
    } finally {
      setSubmitting(false)
    }
  }

  const filteredListings = listings.filter((l) => {
    if (!searchTerm) return true
    const term = searchTerm.toLowerCase()
    return (
      l.title?.toLowerCase().includes(term) ||
      l.commodity?.toLowerCase().includes(term) ||
      l.location_district?.toLowerCase().includes(term) ||
      l.description?.toLowerCase().includes(term)
    )
  })

  const offeredVal = (Number(inquiryForm.offered_price_per_quintal) || 0) * (Number(inquiryForm.requested_quantity_quintal) || 0)

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        <div className={styles.headerRow}>
          <div className={styles.headerTitleGroup}>
            <h1>🌾 Live Crop Marketplace</h1>
            <p>Direct farmer-to-buyer marketplace across 33 districts of Gujarat</p>
          </div>

          {role === 'farmer' && (
            <Link to="/marketplace/my-listings" className="btn btn-primary">
              + Publish My Crop Lot
            </Link>
          )}
        </div>

        {/* Filter bar */}
        <div className={styles.filterBar}>
          <input
            type="text"
            placeholder="🔍 Search lots by commodity, district, grade…"
            className={styles.filterInput}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />

          <select
            className={styles.filterSelect}
            value={commodityFilter}
            onChange={(e) => setCommodityFilter(e.target.value)}
          >
            <option value="">All Commodities</option>
            <option value="Cotton">Cotton</option>
            <option value="Groundnut">Groundnut</option>
            <option value="Wheat">Wheat</option>
            <option value="Mustard">Mustard</option>
          </select>

          <select
            className={styles.filterSelect}
            value={districtFilter}
            onChange={(e) => setDistrictFilter(e.target.value)}
          >
            <option value="">All Districts</option>
            <option value="Rajkot">Rajkot</option>
            <option value="Junagadh">Junagadh</option>
            <option value="Amreli">Amreli</option>
            <option value="Jamnagar">Jamnagar</option>
            <option value="Bhavnagar">Bhavnagar</option>
            <option value="Surendranagar">Surendranagar</option>
            <option value="Morbi">Morbi</option>
            <option value="Patan">Patan</option>
            <option value="Mehsana">Mehsana</option>
          </select>
        </div>

        {/* Listing cards grid */}
        {loading ? (
          <div className="kl-loading-screen">
            <div className="kl-spinner" />
            <p>Loading live crop listings from Gujarat farmers…</p>
          </div>
        ) : filteredListings.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '4rem 1rem', color: 'var(--clr-text-muted)' }}>
            <h3>No listings found matching your search.</h3>
            <p>Try clearing your filters or check back shortly.</p>
          </div>
        ) : (
          <div className={styles.grid}>
            {filteredListings.map((item) => (
              <div key={item.id} className={styles.card}>
                <div className={styles.cardHeader}>
                  <span className={styles.commodityTag}>
                    {item.commodity?.toLowerCase() === 'cotton' ? '⚪' : '🥜'} {item.commodity}
                  </span>
                  <StatusBadge status={item.status} />
                </div>

                <h3 className={styles.cardTitle}>{item.title}</h3>
                {item.description && <p className={styles.cardDesc}>{item.description}</p>}

                <div className={styles.detailsGrid}>
                  <div className={styles.detailItem}>
                    <span className={styles.detailLabel}>Available Quantity</span>
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
                    <span className={styles.detailLabel}>Grade</span>
                    <span className={styles.detailVal}>{item.quality_grade || 'Standard'}</span>
                  </div>
                </div>

                <div className={styles.cardFooter}>
                  <div className={styles.farmerInfo}>
                    <span>Listed by: {item.farmer?.email?.split('@')[0] || 'Farmer'}</span>
                  </div>

                  {role === 'buyer' && (
                    <button
                      onClick={() => handleOpenInquiry(item)}
                      className="btn btn-cyan"
                      style={{ padding: '0.45rem 0.95rem' }}
                    >
                      Express Interest
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Express Interest / Purchase Inquiry Modal ── */}
        {selectedListing && (
          <div className={styles.modalOverlay} onClick={() => setSelectedListing(null)}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
              <div className={styles.modalHeader}>
                <h2 className={styles.modalTitle}>⚡ Send Purchase Inquiry</h2>
                <button className={styles.closeBtn} onClick={() => setSelectedListing(null)}>✕</button>
              </div>

              <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                Submitting inquiry for: <strong style={{ color: '#ffffff' }}>{selectedListing.title}</strong>
              </p>

              {modalSuccess && <div className="badge badge-emerald" style={{ padding: '0.5rem' }}>{modalSuccess}</div>}
              {modalError && <div className="badge badge-rose" style={{ padding: '0.5rem' }}>{modalError}</div>}

              <form className={styles.modalForm} onSubmit={handleSendInquiry}>
                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Offered Price (₹ / Quintal)</label>
                  <input
                    type="number"
                    step="1"
                    className={styles.modalInput}
                    value={inquiryForm.offered_price_per_quintal}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, offered_price_per_quintal: e.target.value })}
                    required
                  />
                </div>

                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Requested Quantity (Quintals)</label>
                  <input
                    type="number"
                    step="0.01"
                    className={styles.modalInput}
                    value={inquiryForm.requested_quantity_quintal}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, requested_quantity_quintal: e.target.value })}
                    required
                  />
                </div>

                <div className={styles.modalCalculated}>
                  <span>Total Deal Valuation:</span>
                  <span>₹{offeredVal.toLocaleString('en-IN')}</span>
                </div>

                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Contact Phone</label>
                  <input
                    type="tel"
                    className={styles.modalInput}
                    placeholder="+91 98765 43210"
                    value={inquiryForm.contact_phone}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, contact_phone: e.target.value })}
                  />
                </div>

                <div className={styles.modalField}>
                  <label className={styles.modalLabel}>Message / Terms for Farmer</label>
                  <textarea
                    rows={3}
                    className={styles.modalInput}
                    value={inquiryForm.message}
                    onChange={(e) => setInquiryForm({ ...inquiryForm, message: e.target.value })}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-cyan"
                  disabled={submitting}
                  style={{ width: '100%', padding: '0.85rem' }}
                >
                  {submitting ? 'Sending Inquiry…' : 'Submit Purchase Offer'}
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
