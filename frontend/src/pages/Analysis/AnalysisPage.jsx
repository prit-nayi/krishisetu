/**
 * AnalysisPage.jsx — Futuristic Market Intelligence, Decision Engine & AI Synthesis.
 */
import React, { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { fetchMarketAnalysis, formatCurrency, formatPercent, parseApiError } from '../../api/analysis'
import Navbar from '../../components/Navigation/Navbar'
import StatusBadge from '../../components/UI/StatusBadge'
import styles from './Analysis.module.css'

const IconSparkles = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 3l1.912 5.813a2 2 0 001.275 1.275L21 12l-5.813 1.912a2 2 0 00-1.275 1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L12 21l-1.912-5.813a2 2 0 00-1.275-1.275L3 12l5.813-1.912a2 2 0 001.275-1.275L12 3z" />
  </svg>
)

const IconTrendingUp = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
)

const IconTrendingDown = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
    <polyline points="17 18 23 18 23 12" />
  </svg>
)

const IconMinus = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
)

const IconCheckCircle = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
    <polyline points="22 4 12 14.01 9 11.01" />
  </svg>
)

const IconAlert = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
)

export default function AnalysisPage() {
  const { cropLotId } = useParams()
  const [forecastDays, setForecastDays] = useState(7)
  const navigate = useNavigate()

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['marketAnalysis', cropLotId, forecastDays],
    queryFn: () => fetchMarketAnalysis(cropLotId, forecastDays),
    enabled: Boolean(cropLotId),
  })

  const bestMarket = data?.best_market
  const markets = data?.markets || []
  const aiExplanation = data?.ai_explanation
  const decision = data?.decision

  // Chart data
  const chartData = []
  if (bestMarket?.modal_price) {
    chartData.push({
      day: 'Today',
      price: bestMarket.modal_price,
      lower: bestMarket.modal_price,
      upper: bestMarket.modal_price,
    })

    if (Array.isArray(bestMarket.predicted_prices) && bestMarket.predicted_prices.length > 0) {
      bestMarket.predicted_prices.forEach((pred, idx) => {
        const dayNumber = idx + 1
        const lower = bestMarket.lower_band?.[idx] ?? pred * 0.95
        const upper = bestMarket.upper_band?.[idx] ?? pred * 1.05
        chartData.push({
          day: `Day ${dayNumber}`,
          price: pred,
          lower: Math.round(lower),
          upper: Math.round(upper),
        })
      })
    }
  }

  function getTrendIcon(trend) {
    if (trend === 'up') return <IconTrendingUp />
    if (trend === 'down') return <IconTrendingDown />
    return <IconMinus />
  }

  function getDecisionClass(rec) {
    if (rec === 'SELL_NOW') return styles.decisionSell
    if (rec === 'HOLD') return styles.decisionHold
    return styles.decisionPartial
  }

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        {/* Loading State */}
        {isLoading && (
          <div className={styles.loadingState} role="status" aria-live="polite">
            <div className={styles.spinner} />
            <p>Evaluating 80 Gujarat APMC mandis &amp; generating AI decision models…</p>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className={styles.errorBox} role="alert">
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>Analysis Error</h3>
            <p>{parseApiError(error)}</p>
            <div style={{ marginTop: '1rem' }}>
              <Link to="/crop-lots" className="btn btn-glass">
                ← Return to Crop Lots
              </Link>
            </div>
          </div>
        )}

        {/* Loaded Content */}
        {!isLoading && !isError && data && (
          <>
            {/* Top Bar with Horizon Controls */}
            <div className={styles.topBar}>
              <div className={styles.titleArea}>
                <h1>AI Market Intelligence &amp; Decision</h1>
                <p className={styles.subTitle}>
                  Commodity: <strong style={{ color: '#ffffff' }}>{data.commodity}</strong> · Quantity: <strong style={{ color: '#ffffff' }}>{data.quantity_quintal} Quintals</strong> · Evaluated: <strong style={{ color: '#10b981' }}>{data.market_count} Gujarat Mandis</strong>
                </p>
              </div>

              <div className={styles.horizonControls}>
                <span className={styles.horizonLabel}>Forecast Horizon:</span>
                {[7, 14, 30].map((days) => (
                  <button
                    key={days}
                    className={`${styles.horizonBtn} ${forecastDays === days ? styles.horizonBtnActive : ''}`}
                    onClick={() => setForecastDays(days)}
                  >
                    {days} Days
                  </button>
                ))}
              </div>
            </div>

            {/* ── FLAGSHIP DECISION HERO BANNER ── */}
            {decision && (
              <section className={styles.decisionBanner}>
                <div className={styles.decisionHeader}>
                  <div className={styles.decisionTitleGroup}>
                    <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                      ⚡ AI Decision Engine Recommendation
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '4px' }}>
                      <span className={`${styles.decisionPill} ${getDecisionClass(decision.recommendation)}`}>
                        {decision.recommendation === 'SELL_NOW' && '🟢 SELL NOW'}
                        {decision.recommendation === 'HOLD' && '🟡 HOLD IN STORAGE'}
                        {decision.recommendation === 'PARTIAL_SELL' && '🔵 PARTIAL SELL'}
                      </span>
                      <span style={{ fontSize: '0.9rem', color: '#cbd5e1' }}>
                        Confidence: <strong style={{ color: '#34d399' }}>{Math.round(decision.confidence * 100)}%</strong>
                      </span>
                    </div>
                  </div>

                  <div className={styles.decisionActions}>
                    <Link
                      to="/marketplace/my-listings"
                      className="btn btn-primary"
                    >
                      <span>🌾</span> List on Marketplace
                    </Link>
                  </div>
                </div>

                <div className={styles.decisionGrid}>
                  <div className={styles.decisionMetric}>
                    <span className={styles.decisionMetricLabel}>Optimal Market</span>
                    <span className={styles.decisionMetricValue} style={{ color: '#38bdf8' }}>
                      {bestMarket?.market_name || 'Best APMC'}
                    </span>
                  </div>

                  <div className={styles.decisionMetric}>
                    <span className={styles.decisionMetricLabel}>Current Net Value</span>
                    <span className={styles.decisionMetricValue} style={{ color: '#34d399' }}>
                      {formatCurrency(decision.current_net_value)}
                    </span>
                  </div>

                  <div className={styles.decisionMetric}>
                    <span className={styles.decisionMetricLabel}>Expected Future Value</span>
                    <span className={styles.decisionMetricValue}>
                      {formatCurrency(decision.expected_future_net_value)}
                    </span>
                  </div>

                  <div className={styles.decisionMetric}>
                    <span className={styles.decisionMetricLabel}>Suggested Quantity</span>
                    <span className={styles.decisionMetricValue} style={{ color: '#fbbf24' }}>
                      {decision.sell_now_quantity_quintal != null ? `${decision.sell_now_quantity_quintal} Qtl` : `${data.quantity_quintal} Qtl`}
                    </span>
                  </div>
                </div>
              </section>
            )}

            {/* ── 2-Column Grid: Price Forecast Curve + IBM Granite AI Synthesis ── */}
            <div className={styles.contentGrid}>
              {/* Forecast Chart */}
              <div className={styles.card}>
                <div className={styles.cardHeader}>
                  <h3 className={styles.cardTitle}>
                    <span>📈</span> Price Forecast Curve ({forecastDays} Days)
                  </h3>
                  {bestMarket && (
                    <StatusBadge status={bestMarket.forecast_confidence_level} />
                  )}
                </div>

                {chartData.length > 0 ? (
                  <>
                    <div className={styles.chartContainer}>
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                          <XAxis dataKey="day" stroke="#94a3b8" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                          <YAxis domain={['auto', 'auto']} stroke="#94a3b8" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: 'rgba(15, 23, 42, 0.95)',
                              border: '1px solid rgba(255, 255, 255, 0.15)',
                              borderRadius: '8px',
                              color: '#ffffff',
                            }}
                            formatter={(val, name) => [
                              `₹${Number(val).toLocaleString('en-IN')}/q`,
                              name === 'price' ? 'Predicted Price' : name === 'upper' ? 'Upper Band' : 'Lower Band',
                            ]}
                          />
                          <Legend wrapperStyle={{ color: '#94a3b8' }} />
                          <Area type="monotone" dataKey="upper" fill="#10b981" stroke="none" fillOpacity={0.15} name="Upper Band" />
                          <Area type="monotone" dataKey="lower" fill="#0b1320" stroke="none" fillOpacity={0.8} name="Lower Bound" />
                          <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={3} dot={{ r: 4, fill: '#34d399' }} activeDot={{ r: 6 }} name="Price (₹/Qtl)" />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>

                    <div className={styles.forecastSummary}>
                      <span>
                        Predicted Rate: <strong style={{ color: '#34d399' }}>{formatCurrency(bestMarket?.predicted_price)}/Qtl</strong>
                      </span>
                      <span>
                        Method: <strong style={{ color: '#ffffff' }}>{(bestMarket?.forecast_method || bestMarket?.forecast_model || 'Regression').replace('_', ' ')}</strong>
                      </span>
                    </div>
                  </>
                ) : (
                  <p style={{ color: 'var(--clr-text-muted)', padding: '2rem 0', textAlign: 'center' }}>
                    Historical arrival data is currently insufficient to chart price forecasts.
                  </p>
                )}
              </div>

              {/* IBM Granite AI Demo Card */}
              <div className={styles.aiDemoCard}>
                <div className={styles.cardHeader} style={{ borderBottom: 'none', paddingBottom: 0 }}>
                  <h3 className={styles.cardTitle}>
                    <IconSparkles /> IBM Granite AI Synthesis
                  </h3>
                  <span className={styles.aiBadge}>
                    ⚡ IBM Granite 13B Demo/Mock
                  </span>
                </div>

                {aiExplanation ? (
                  <>
                    <p className={styles.aiExplanationText}>
                      {aiExplanation.explanation}
                    </p>

                    {aiExplanation.key_factors?.length > 0 && (
                      <div className={styles.aiSection}>
                        <span className={styles.aiSectionTitle}>Key Financial Drivers:</span>
                        <ul className={styles.factorsList}>
                          {aiExplanation.key_factors.map((factor, idx) => (
                            <li key={idx} className={styles.factorItem}>
                              <span className={styles.factorIcon}><IconCheckCircle /></span>
                              <span>{factor}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {aiExplanation.risk_notes?.length > 0 && (
                      <div className={styles.aiSection}>
                        <span className={styles.aiSectionTitle}>Logistics &amp; Transport Analysis:</span>
                        <div className={styles.riskList}>
                          {aiExplanation.risk_notes.map((risk, idx) => (
                            <div key={idx} className={styles.riskItem}>
                              <span style={{ color: '#f59e0b', flexShrink: 0 }}><IconAlert /></span>
                              <span>{risk}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <p style={{ color: 'var(--clr-text-muted)', padding: '2rem 0', textAlign: 'center' }}>
                    Generating IBM Granite explanation based on real data…
                  </p>
                )}
              </div>
            </div>

            {/* ── APMC Mandis Ranked Comparison Table ── */}
            <section className={styles.tableCard}>
              <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>
                  <span>🏛️</span> Gujarat APMC Mandi Comparison ({markets.length} Mandis Evaluated)
                </h3>
              </div>

              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Market Name</th>
                      <th>District</th>
                      <th>Distance</th>
                      <th>Modal Price</th>
                      <th>Gross Revenue</th>
                      <th>Transport Cost</th>
                      <th>Other Costs</th>
                      <th>Total Cost</th>
                      <th>Net Revenue</th>
                      <th>Forecast Outlook</th>
                    </tr>
                  </thead>
                  <tbody>
                    {markets.map((m) => {
                      const isRank1 = m.rank === 1
                      return (
                        <tr key={m.market_id} className={isRank1 ? styles.tableRowRank1 : ''}>
                          <td>
                            <span className={`${styles.rankBadge} ${isRank1 ? styles.rank1Badge : ''}`}>
                              {m.rank}
                            </span>
                          </td>
                          <td>
                            <strong>{m.market_name}</strong>
                            {isRank1 && <span style={{ marginLeft: '6px', fontSize: '0.75rem', color: '#10b981' }}>★ Best Net Profit</span>}
                          </td>
                          <td>{m.district}</td>
                          <td>{m.distance_km != null ? `${m.distance_km} km` : 'Local APMC'}</td>
                          <td>₹{m.modal_price.toLocaleString('en-IN')}/Qtl</td>
                          <td>{formatCurrency(m.gross_revenue)}</td>
                          <td>{formatCurrency(m.transport_cost)}</td>
                          <td>{formatCurrency(m.other_costs || 0)}</td>
                          <td>{formatCurrency(m.total_cost || m.transport_cost)}</td>
                          <td className={styles.netHighlight}>{formatCurrency(m.net_revenue)}</td>
                          <td>
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: m.trend_direction === 'up' ? '#34d399' : m.trend_direction === 'down' ? '#fb7185' : '#cbd5e1' }}>
                              {getTrendIcon(m.trend_direction)}
                              {m.trend_direction.toUpperCase()} ({formatPercent(m.price_change_pct)})
                            </span>
                          </td>
                        </tr>
                      )
                    })}
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
