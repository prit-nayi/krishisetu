/**
 * api/axiosClient.js — Axios instance with JWT header injection and auto-refresh.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const axiosClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT access token from localStorage
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-refresh on 401
axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          })
          localStorage.setItem('access_token', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return axiosClient(original)
        } catch (_err) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  },
)

export default axiosClient
