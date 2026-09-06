/**
 * InquiriesPage.jsx — Buyer purchase inquiries tracking dashboard.
 */
import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../../components/Navigation/Navbar'
import StatusBadge from '../../components/UI/StatusBadge'
import { fetchSentInquiries } from '../../api/marketplace'
import styles from './Marketplace.module.css'

export default function InquiriesPage() {
  const [inquiries, setInquiries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadInquiries()
  }, [])

  async function loadInquiries() {
    setLoading(true)
    try {
      const res = await fetchSentInquiries()
      setInquiries(res?.results || res || [])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        <div className={styles.headerRow}>
          <div className={styles.headerTitleGroup}>
            <h1>💬 My Purchase Inquiries</h1>
            <p>Track offers submitted to Gujarat farmers &amp; deal confirmation status</p>
          </div>

          <Link to="/marketplace" className="btn btn-cyan">
            + Browse More Listings
          </Link>
        </div>

        {loading ? (
          <div className="kl-loading-screen">
            <div className="kl-spinner" />
            <p>Loading your purchase inquiries…</p>
          </div>
        ) : inquiries.length === 0 ? (
          <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem 2rem', color: '#94a3b8' }}>
            <span style={{ fontSize: '2.5rem' }}>📫</span>
            <h3 style={{ color: '#ffffff', marginTop: '0.5rem' }}>No inquiries submitted yet</h3>
            <p style={{ marginTop: '0.25rem' }}>Browse the live crop marketplace and express interest in farmer crop lots.</p>
            <Link to="/marketplace" className="btn btn-cyan" style={{ marginTop: '1rem' }}>
              Explore Crop Marketplace
            </Link>
          </div>
        ) : (
          <div className="glass-panel" style={{ padding: 'var(--sp-6)' }}>
            <div className={styles.tableWrapper}>
              <table className={styles.table} style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>Listing Title</th>
                    <th>Commodity</th>
                    <th>Farmer District</th>
                    <th>Offered Rate</th>
                    <th>Requested Qtl</th>
                    <th>Deal Valuation</th>
                    <th>Status</th>
                    <th>Farmer Notes</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {inquiries.map((inq) => (
                    <tr key={inq.id}>
                      <td style={{ fontWeight: 600, color: '#ffffff' }}>{inq.listing_title}</td>
                      <td>{inq.commodity}</td>
                      <td>{inq.farmer_district || 'Gujarat'}</td>
                      <td style={{ color: '#38bdf8', fontWeight: 700 }}>₹{inq.offered_price_per_quintal}/Qtl</td>
                      <td>{inq.requested_quantity_quintal} Qtl</td>
                      <td style={{ fontWeight: 700 }}>₹{(Number(inq.total_offered_value) || 0).toLocaleString('en-IN')}</td>
                      <td><StatusBadge status={inq.status} /></td>
                      <td style={{ fontSize: '0.85rem', color: inq.farmer_notes ? '#34d399' : '#94a3b8' }}>
                        {inq.farmer_notes || 'Awaiting response'}
                      </td>
                      <td>{new Date(inq.created_at).toLocaleDateString('en-IN')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
