/**
 * api/analysis.js — KrishiLink AI Market Analysis API client.
 */
import axiosClient from './axiosClient'

/**
 * Fetch combined market financial analysis, price forecast, and AI explanation
 * for a specific crop lot.
 *
 * @param {number|string} cropLotId
 * @param {number} [forecastDays=7]
 * @returns {Promise<Object>}
 */
export async function fetchMarketAnalysis(cropLotId, forecastDays = 7) {
  const response = await axiosClient.post('/analysis/market-analysis/', {
    crop_lot_id: Number(cropLotId),
    forecast_days: Number(forecastDays),
  })
  return response.data
}

export async function runFullDecisionAndPersist(cropLotId, forecastDays = 7) {
  const response = await axiosClient.post(`/decisions/analyze/${cropLotId}/`, {
    forecast_days: Number(forecastDays),
  })
  return response.data
}

export async function fetchRecommendations() {
  const response = await axiosClient.get('/decisions/')
  return response.data
}

/**
 * Format an INR currency value with rupee sign and Indian thousand separators.
 * e.g., 50700 -> "₹50,700"
 */
export function formatCurrency(value) {
  if (value === null || value === undefined || isNaN(value)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

/**
 * Format a percentage change with sign and 1 decimal place.
 * e.g., 2.5 -> "+2.5%"
 */
export function formatPercent(value) {
  if (value === null || value === undefined || isNaN(value)) return '—'
  const sign = value > 0 ? '+' : ''
  return `${sign}${Number(value).toFixed(1)}%`
}

/**
 * Parse any server error message safely.
 */
export function parseApiError(error) {
  if (error?.response?.data) {
    const d = error.response.data
    if (d.error) return d.error
    if (d.detail) return d.detail
    if (Array.isArray(d.details) && d.details.length > 0) return d.details[0]
    if (typeof d === 'string') return d
  }
  return error?.message || 'An unexpected error occurred. Please try again.'
}
