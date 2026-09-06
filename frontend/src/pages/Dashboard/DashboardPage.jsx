/**
 * DashboardPage.jsx — Role-dispatched futuristic dashboard for Farmer, Buyer, Admin.
 */
import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Navbar from '../../components/Navigation/Navbar'
import MetricCard from '../../components/UI/MetricCard'
import StatusBadge from '../../components/UI/StatusBadge'
import { fetchCropLots } from '../../api/cropLots'
import { fetchMarketplaceListings, fetchMarketplaceStats, fetchReceivedInquiries, fetchSentInquiries } from '../../api/marketplace'
import { fetchMarkets } from '../../api/markets'
import { fetchAdminUsers } from '../../api/auth'
import styles from './Dashboard.module.css'

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good Morning'
  if (h < 17) return 'Good Afternoon'
  return 'Good Evening'
}

export default function DashboardPage() {
  const { user } = useAuth()
  const role = user?.role || 'farmer'

  const [loading, setLoading] = useState(true)
  const [cropLots, setCropLots] = useState([])
  const [listings, setListings] = useState([])
  const [inquiries, setInquiries] = useState([])
  const [stats, setStats] = useState(null)
  const [markets, setMarkets] = useState([])
  const [adminUsers, setAdminUsers] = useState([])

  useEffect(() => {
    let isMounted = true
    setLoading(true)

    async function loadData() {
      try {
        if (role === 'farmer') {
          const [lotsRes, inqRes, statsRes, mktsRes] = await Promise.allSettled([
            fetchCropLots(),
            fetchReceivedInquiries(),
            fetchMarketplaceStats(),
            fetchMarkets(),
          ])
          if (isMounted) {
            if (lotsRes.status === 'fulfilled') setCropLots(lotsRes.value?.results || lotsRes.value || [])
            if (inqRes.status === 'fulfilled') setInquiries(inqRes.value?.results || inqRes.value || [])
            if (statsRes.status === 'fulfilled') setStats(statsRes.value)
            if (mktsRes.status === 'fulfilled') setMarkets(mktsRes.value?.results || mktsRes.value || [])
          }
        } else if (role === 'buyer') {
          const [listRes, inqRes, statsRes, mktsRes] = await Promise.allSettled([
            fetchMarketplaceListings(),
            fetchSentInquiries(),
            fetchMarketplaceStats(),
            fetchMarkets(),
          ])
          if (isMounted) {
            if (listRes.status === 'fulfilled') setListings(listRes.value?.results || listRes.value || [])
            if (inqRes.status === 'fulfilled') setInquiries(inqRes.value?.results || inqRes.value || [])
            if (statsRes.status === 'fulfilled') setStats(statsRes.value)
            if (mktsRes.status === 'fulfilled') setMarkets(mktsRes.value?.results || mktsRes.value || [])
          }
        } else if (role === 'admin') {
          const [usersRes, listRes, statsRes, mktsRes] = await Promise.allSettled([
            fetchAdminUsers(),
            fetchMarketplaceListings(),
            fetchMarketplaceStats(),
            fetchMarkets(),
          ])
          if (isMounted) {
            if (usersRes.status === 'fulfilled') setAdminUsers(usersRes.value?.results || usersRes.value || [])
            if (listRes.status === 'fulfilled') setListings(listRes.value?.results || listRes.value || [])
            if (statsRes.status === 'fulfilled') setStats(statsRes.value)
            if (mktsRes.status === 'fulfilled') setMarkets(mktsRes.value?.results || mktsRes.value || [])
          }
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadData()
    return () => { isMounted = false }
  }, [role])

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        {/* Top Hero Banner */}
        <section className={styles.heroBanner}>
          <div className={styles.heroContent}>
            <span className={styles.greeting}>✨ {getGreeting()}, {user?.username || 'User'}</span>
            <h1 className={styles.heroHeading}>
              {role === 'farmer' && 'Autonomous Farmer Decision Engine'}
              {role === 'buyer' && 'Direct Agri Commodity Marketplace'}
              {role === 'admin' && 'KrishiLink AI Platform Administration'}
            </h1>
            <p className={styles.heroSub}>
              {role === 'farmer' && 'Analyze real-time APMC prices, execute AI price forecasts, and sell directly to verified buyers.'}
              {role === 'buyer' && 'Source premium cotton and groundnut lots directly from farmers across Gujarat with transparent pricing.'}
              {role === 'admin' && 'Real-time telemetry of Gujarat APMC mandis, AI recommendation pipelines, and multi-role marketplace trades.'}
            </p>
          </div>

          <div className={styles.heroActions}>
            {role === 'farmer' && (
              <>
                <Link to="/crop-lots/new" className="btn btn-primary">
                  <span>+</span> Add Crop Lot
                </Link>
                <Link to="/marketplace/my-listings" className="btn btn-cyan">
                  <span>🌾</span> Create Listing
                </Link>
              </>
            )}
            {role === 'buyer' && (
              <>
                <Link to="/marketplace" className="btn btn-cyan">
                  <span>🔍</span> Browse Listings
                </Link>
                <Link to="/markets" className="btn btn-glass">
                  <span>📊</span> APMC Live Rates
                </Link>
              </>
            )}
            {role === 'admin' && (
              <>
                <Link to="/admin/users" className="btn btn-primary">
                  <span>👥</span> User Directory
                </Link>
                <Link to="/markets" className="btn btn-glass">
                  <span>🏛️</span> 80 Mandis Status
                </Link>
              </>
            )}
          </div>
        </section>

        {/* ── Role: FARMER DASHBOARD ── */}
        {role === 'farmer' && (
          <>
            {/* KPI Metric Cards */}
            <div className={styles.kpiGrid}>
              <MetricCard
                title="Active Crop Lots"
                value={cropLots.length}
                subtitle="Registered for AI analysis"
                icon="📦"
                accent="emerald"
              />
              <MetricCard
                title="Buyer Inquiries"
                value={inquiries.length}
                subtitle={`${inquiries.filter((i) => i.status === 'PENDING').length} awaiting response`}
                icon="💬"
                accent="cyan"
              />
              <MetricCard
                title="Gujarat Mandis"
                value={markets.length || 80}
                subtitle="Live AGMARKNET rates"
                icon="🏛️"
                accent="amber"
              />
              <MetricCard
                title="AI Engine Status"
                value="ONLINE"
                subtitle="IBM Granite Demo/Mock active"
                icon="⚡"
                accent="purple"
              />
            </div>

            {/* Active Crop Lots & Quick Analysis */}
            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>🌾 My Crop Lots for Analysis</h2>
                <Link to="/crop-lots" className={styles.sectionAction}>View all ({cropLots.length}) →</Link>
              </div>

              {cropLots.length === 0 ? (
                <div className={styles.emptyState}>
                  <span className={styles.emptyIcon}>🌱</span>
                  <h3 className={styles.emptyTitle}>No crop lots added yet</h3>
                  <p className={styles.emptySub}>Add your cotton or groundnut harvest lot to get instant AI SELL/HOLD recommendations.</p>
                  <Link to="/crop-lots/new" className="btn btn-primary">+ Add Your First Crop Lot</Link>
                </div>
              ) : (
                <div className={styles.gridCards}>
                  {cropLots.slice(0, 6).map((lot) => (
                    <div key={lot.id} className={styles.lotCard}>
                      <div className={styles.lotCardHeader}>
                        <span className={styles.lotCommodity}>
                          {lot.commodity?.toLowerCase() === 'cotton' ? '⚪' : '🥜'} {lot.commodity?.toUpperCase()}
                        </span>
                        <StatusBadge status={lot.quality_grade || 'ACTIVE'} label={lot.quality_grade || 'Grade A'} />
                      </div>

                      <div className={styles.lotDetails}>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>Quantity</span>
                          <span className={styles.detailValue}>{lot.quantity} {lot.unit}</span>
                        </div>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>Harvest Date</span>
                          <span className={styles.detailValue}>{lot.harvest_date || 'Recent'}</span>
                        </div>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>Storage</span>
                          <span className={styles.detailValue}>{lot.storage_status || 'Farm'}</span>
                        </div>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>Moisture</span>
                          <span className={styles.detailValue}>{lot.moisture_percent ? `${lot.moisture_percent}%` : 'N/A'}</span>
                        </div>
                      </div>

                      <div className={styles.lotActions}>
                        <Link to={`/analysis/${lot.id}`} className="btn btn-primary" style={{ flex: 1 }}>
                          ⚡ Run AI Decision
                        </Link>
                        <Link to={`/crop-lots/${lot.id}/edit`} className="btn btn-glass">
                          Edit
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Received Buyer Inquiries */}
            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>💬 Incoming Buyer Inquiries</h2>
                <Link to="/marketplace/my-listings" className={styles.sectionAction}>Manage Listings →</Link>
              </div>

              {inquiries.length === 0 ? (
                <div className={styles.emptyState}>
                  <span className={styles.emptyIcon}>📫</span>
                  <h3 className={styles.emptyTitle}>No buyer inquiries received yet</h3>
                  <p className={styles.emptySub}>When buyers across Gujarat express interest in your crop listings, they will appear here.</p>
                </div>
              ) : (
                <div className={styles.tableWrapper}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Listing</th>
                        <th>Buyer</th>
                        <th>Offered Price</th>
                        <th>Quantity</th>
                        <th>Total Value</th>
                        <th>Status</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inquiries.slice(0, 5).map((inq) => (
                        <tr key={inq.id}>
                          <td style={{ fontWeight: 600, color: '#ffffff' }}>{inq.listing_title || 'Listing'}</td>
                          <td>{inq.buyer?.email || 'Buyer'}</td>
                          <td style={{ color: '#34d399', fontWeight: 700 }}>₹{inq.offered_price_per_quintal}/Qtl</td>
                          <td>{inq.requested_quantity_quintal} Qtl</td>
                          <td style={{ fontWeight: 700 }}>₹{(Number(inq.total_offered_value) || 0).toLocaleString('en-IN')}</td>
                          <td><StatusBadge status={inq.status} /></td>
                          <td>{new Date(inq.created_at).toLocaleDateString('en-IN')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}

        {/* ── Role: BUYER DASHBOARD ── */}
        {role === 'buyer' && (
          <>
            <div className={styles.kpiGrid}>
              <MetricCard
                title="Active Listings"
                value={stats?.total_active_listings || listings.length}
                subtitle="From verified Gujarat farmers"
                icon="🌾"
                accent="cyan"
              />
              <MetricCard
                title="Total Crop Volume"
                value={`${stats?.total_listed_quantity_quintal || 0} Qtl`}
                subtitle="Available for direct purchase"
                icon="📦"
                accent="emerald"
              />
              <MetricCard
                title="My Sent Inquiries"
                value={inquiries.length}
                subtitle={`${inquiries.filter((i) => i.status === 'ACCEPTED').length} accepted deals`}
                icon="💬"
                accent="amber"
              />
              <MetricCard
                title="Avg Cotton Rate"
                value={`₹${stats?.average_prices?.cotton_per_quintal || '7,200'}`}
                subtitle="Gujarat Mandi Average"
                icon="📈"
                accent="purple"
              />
            </div>

            {/* Featured Crop Listings for Buyers */}
            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>⚡ Live Farmer Listings</h2>
                <Link to="/marketplace" className={styles.sectionAction}>View all marketplace →</Link>
              </div>

              {listings.length === 0 ? (
                <div className={styles.emptyState}>
                  <span className={styles.emptyIcon}>🌾</span>
                  <h3 className={styles.emptyTitle}>No active crop listings at the moment</h3>
                  <p className={styles.emptySub}>Check back shortly as farmers publish new lots.</p>
                </div>
              ) : (
                <div className={styles.gridCards}>
                  {listings.slice(0, 6).map((item) => (
                    <div key={item.id} className={styles.lotCard}>
                      <div className={styles.lotCardHeader}>
                        <span className={styles.lotCommodity}>
                          {item.commodity?.toLowerCase() === 'cotton' ? '⚪' : '🥜'} {item.commodity}
                        </span>
                        <StatusBadge status={item.quality_grade || 'Grade A'} />
                      </div>

                      <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: '0.25rem 0' }}>
                        {item.title}
                      </h3>

                      <div className={styles.lotDetails}>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>Lot Size</span>
                          <span className={styles.detailValue}>{item.quantity_quintal} Qtl</span>
                        </div>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>Asking Price</span>
                          <span className={styles.detailValue} style={{ color: '#38bdf8' }}>₹{item.expected_price_per_quintal}/Qtl</span>
                        </div>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>District</span>
                          <span className={styles.detailValue}>{item.location_district}</span>
                        </div>
                        <div className={styles.detailItem}>
                          <span className={styles.detailLabel}>Total Value</span>
                          <span className={styles.detailValue}>₹{(Number(item.total_expected_value) || 0).toLocaleString('en-IN')}</span>
                        </div>
                      </div>

                      <div className={styles.lotActions}>
                        <Link to={`/marketplace`} className="btn btn-cyan" style={{ flex: 1 }}>
                          Express Purchase Interest
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}

        {/* ── Role: ADMIN DASHBOARD ── */}
        {role === 'admin' && (
          <>
            <div className={styles.kpiGrid}>
              <MetricCard
                title="Registered Users"
                value={adminUsers.length || '—'}
                subtitle="Farmers & Buyers"
                icon="👥"
                accent="purple"
              />
              <MetricCard
                title="Active Listings"
                value={stats?.total_active_listings || listings.length}
                subtitle="Live on marketplace"
                icon="🌾"
                accent="cyan"
              />
              <MetricCard
                title="Districts Active"
                value={stats?.districts_covered || 28}
                subtitle="Across Gujarat State"
                icon="🗺️"
                accent="emerald"
              />
              <MetricCard
                title="Monitored Mandis"
                value="80 APMCs"
                subtitle="AGMARKNET sync active"
                icon="🏛️"
                accent="amber"
              />
            </div>

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>👥 User Management Directory</h2>
                <Link to="/admin/users" className={styles.sectionAction}>View all users →</Link>
              </div>

              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Email</th>
                      <th>Username</th>
                      <th>Role</th>
                      <th>Phone</th>
                      <th>Joined Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminUsers.slice(0, 6).map((u) => (
                      <tr key={u.id}>
                        <td>#{u.id}</td>
                        <td style={{ fontWeight: 600, color: '#ffffff' }}>{u.email}</td>
                        <td>{u.username}</td>
                        <td><StatusBadge status={u.role} /></td>
                        <td>{u.phone || '—'}</td>
                        <td>{new Date(u.date_joined).toLocaleDateString('en-IN')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
