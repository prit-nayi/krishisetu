/**
 * api/markets.js — Market Intelligence API functions (Phase 3).
 *
 * All requests go through the KrishiLink backend (axiosClient).
 * The frontend never calls data.gov.in directly.
 */
import axiosClient from './axiosClient'

/**
 * Fetch list of active markets.
 * @param {Object} params — optional { district, market_type, commodity }
 */
export async function fetchMarkets(params = {}) {
  const { data } = await axiosClient.get('/markets/', { params })
  // Handle paginated or flat list
  return data.results ?? data
}

/**
 * Fetch a single market by ID.
 * @param {number} id
 */
export async function fetchMarket(id) {
  const { data } = await axiosClient.get(`/markets/${id}/`)
  return data
}

/**
 * Fetch latest market prices.
 * @param {Object} params — optional { market, commodity, district, date }
 */
export async function fetchMarketPrices(params = {}) {
  const { data } = await axiosClient.get('/markets/prices/', { params })
  return data.results ?? data
}

/**
 * Fetch market price history for charting.
 * @param {Object} params — { market?, commodity?, days? }
 */
export async function fetchMarketPriceHistory(params = {}) {
  const { data } = await axiosClient.get('/markets/history/', { params })
  return data.results ?? data
}

/**
 * Fetch nearby markets.
 * @param {Object} params — { lat, lon, radius_km?, commodity? }
 */
export async function fetchNearbyMarkets(params = {}) {
  const { data } = await axiosClient.get('/markets/nearby/', { params })
  return data
}

/** Helper: format INR price string */
export function formatPrice(value) {
  if (value == null) return '—'
  return `₹${parseFloat(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}
