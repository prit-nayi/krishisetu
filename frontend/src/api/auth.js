/**
 * api/auth.js — Authentication and FarmerProfile API calls.
 */
import axiosClient from './axiosClient'

export async function registerUser(payload) {
  const { data } = await axiosClient.post('/auth/register/', payload)
  return data
}

export async function loginUser(email, password) {
  const { data } = await axiosClient.post('/auth/login/', { email, password })
  return data
}

export async function refreshToken(refresh) {
  const { data } = await axiosClient.post('/auth/refresh/', { refresh })
  return data
}

export async function fetchMe() {
  const { data } = await axiosClient.get('/auth/me/')
  return data
}

export async function fetchFarmerProfile() {
  const { data } = await axiosClient.get('/farmer/profile/')
  return data
}

export async function updateFarmerProfile(payload) {
  const { data } = await axiosClient.patch('/farmer/profile/', payload)
  return data
}

export async function fetchBuyerProfile() {
  const { data } = await axiosClient.get('/buyer/profile/')
  return data
}

export async function updateBuyerProfile(payload) {
  const { data } = await axiosClient.patch('/buyer/profile/', payload)
  return data
}

export async function fetchAdminUsers() {
  const { data } = await axiosClient.get('/admin/users/')
  return data
}

/**
 * Extract a human-readable error message from an Axios error response.
 */
export function parseApiError(err) {
  const responseData = err?.response?.data
  if (!responseData) return 'Network error. Please check your connection.'
  if (typeof responseData === 'string') return responseData
  if (responseData.detail) return responseData.detail

  const messages = []
  Object.entries(responseData).forEach(([field, errors]) => {
    if (Array.isArray(errors)) {
      errors.forEach((msg) => {
        const label = field === 'non_field_errors' ? '' : `${field}: `
        messages.push(`${label}${msg}`)
      })
    } else if (typeof errors === 'string') {
      messages.push(`${field}: ${errors}`)
    }
  })
  return messages.length ? messages.join('\n') : 'An unexpected error occurred.'
}
