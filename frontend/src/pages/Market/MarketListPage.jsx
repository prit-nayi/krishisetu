/**
 * MarketListPage.jsx — Phase 3 Market Intelligence page.
 *
 * Displays Gujarat market prices for Cotton and Groundnut.
 * Reads from the KrishiLink backend (PostgreSQL) — never directly from data.gov.in.
 */
import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import Navbar from '../../components/Navigation/Navbar'
import {
  fetchMarketPrices,
  fetchMarketPriceHistory,
  formatPrice,
} from '../../api/markets'
import styles from './Market.module.css'

const COMMODITIES = [
  { value: '',           label: 'All Commodities' },
  { value: 'GROUNDNUT',  label: 'Groundnut' },
  { value: 'COTTON',     label: 'Cotton' },
]

const DISTRICTS = [
  '', 'Ahmedabad', 'Amreli', 'Anand', 'Banaskantha', 'Bharuch',
  'Bhavnagar', 'Botad', 'Dahod', 'Gandhinagar', 'Gir Somnath',
  'Jamnagar', 'Junagadh', 'Kutch', 'Mehsana', 'Morbi', 'Narmada',
  'Navsari', 'Patan', 'Porbandar', 'Rajkot', 'Sabarkantha',
  'Surat', 'Surendranagar', 'Vadodara', 'Valsad',
]

function CommodityBadge({ commodity }) {
  const lower = (commodity || '').toLowerCase()
  const cls = lower === 'groundnut' ? styles.badgeGroundnut : styles.badgeCotton
  return <span className={`${styles.badge} ${cls}`}>{commodity}</span>
}

function SourceTag({ source }) {
  const label = source === 'agmarknet' ? 'Agmarknet / data.gov.in' : source
  return <span className={styles.sourceTag}>{label}</span>
}

export default function MarketListPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const [commodity, setCommodity] = useState('')
  const [district,  setDistrict]  = useState('')
  const [prices,    setPrices]    = useState([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState('')

  const loadPrices = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (commodity) params.commodity = commodity
      if (district)  params.district  = district
      const data = await fetchMarketPrices(params)
      setPrices(data)
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        'Unable to load market prices. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }, [commodity, district])

  useEffect(() => { loadPrices() }, [loadPrices])

  return (
    <div className={styles.page}>
      <Navbar />

      {/* Header */}
      <header className={styles.header}>
        <h1>Market Prices</h1>
        <p>Gujarat APMC daily prices — Cotton &amp; Groundnut</p>
      </header>

      <main className={styles.main}>
        {/* Filter bar */}
        <div className={styles.filterBar}>
          <div className={styles.filterGroup}>
            <label htmlFor="commodity-filter">Commodity</label>
            <select
              id="commodity-filter"
              className={styles.filterSelect}
              value={commodity}
              onChange={(e) => setCommodity(e.target.value)}
            >
              {COMMODITIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div className={styles.filterGroup}>
            <label htmlFor="district-filter">District</label>
            <select
              id="district-filter"
              className={styles.filterSelect}
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
            >
              {DISTRICTS.map((d) => (
                <option key={d} value={d}>{d || 'All Districts'}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Content */}
        {error && <div className={styles.error}>{error}</div>}

        {loading ? (
          <div className={styles.loading}>Loading market prices…</div>
        ) : prices.length === 0 ? (
          <div className={styles.empty}>
            {commodity || district
              ? 'No prices found for the selected filters. Run sync_market_prices to populate data.'
              : 'No market price data yet. Run: python manage.py sync_market_prices'}
          </div>
        ) : (
          <>
            <p className={styles.resultCount}>{prices.length} record{prices.length !== 1 ? 's' : ''}</p>
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Market</th>
                    <th>District</th>
                    <th>Commodity</th>
                    <th>Variety</th>
                    <th>Min Price</th>
                    <th>Max Price</th>
                    <th>Modal Price</th>
                    <th>Date</th>
                    <th>Source</th>
                  </tr>
                </thead>
                <tbody>
                  {prices.map((price) => (
                    <tr key={price.id}>
                      <td>{price.market_name}</td>
                      <td>{price.market_district}</td>
                      <td><CommodityBadge commodity={price.commodity} /></td>
                      <td>{price.variety || '—'}</td>
                      <td className={styles.priceMin}>{formatPrice(price.min_price)}</td>
                      <td className={styles.priceMax}>{formatPrice(price.max_price)}</td>
                      <td className={styles.priceModal}>{formatPrice(price.modal_price)}</td>
                      <td>{price.price_date}</td>
                      <td><SourceTag source={price.source} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
