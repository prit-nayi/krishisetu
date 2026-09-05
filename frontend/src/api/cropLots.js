/**
 * api/cropLots.js — CropLot API calls.
 * All requests require authentication (JWT header injected by axiosClient).
 */
import axiosClient from './axiosClient'
import { parseApiError } from './auth'

const BASE = '/crops/lots/'

/**
 * List all active crop lots for the authenticated farmer.
 * @returns {Promise<{count, results}>}
 */
export async function fetchCropLots() {
  const { data } = await axiosClient.get(BASE)
  return data
}

/**
 * Get a single crop lot by id.
 * @param {number} id
 */
export async function fetchCropLot(id) {
  const { data } = await axiosClient.get(`${BASE}${id}/`)
  return data
}

/**
 * Create a new crop lot.
 * @param {object} payload
 * @returns {Promise<object>} created lot (full serializer with id)
 */
export async function createCropLot(payload) {
  const { data } = await axiosClient.post(BASE, payload)
  return data
}

/**
 * Partially update a crop lot (PATCH).
 * @param {number} id
 * @param {object} payload
 */
export async function updateCropLot(id, payload) {
  const { data } = await axiosClient.patch(`${BASE}${id}/`, payload)
  return data
}

/**
 * Soft-delete a crop lot (DELETE → 204).
 * @param {number} id
 */
export async function deleteCropLot(id) {
  await axiosClient.delete(`${BASE}${id}/`)
}

export { parseApiError }
