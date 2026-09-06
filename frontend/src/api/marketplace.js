/**
 * api/marketplace.js — API endpoints for KrishiLink AI marketplace (listings & inquiries).
 */
import axiosClient from './axiosClient'

export const fetchMarketplaceListings = async (params = {}) => {
  const response = await axiosClient.get('/marketplace/listings/', { params })
  return response.data
}

export const fetchMyListings = async () => {
  const response = await axiosClient.get('/marketplace/listings/my_listings/')
  return response.data
}

export const fetchListingDetail = async (id) => {
  const response = await axiosClient.get(`/marketplace/listings/${id}/`)
  return response.data
}

export const createCropListing = async (data) => {
  const response = await axiosClient.post('/marketplace/listings/', data)
  return response.data
}

export const updateCropListing = async (id, data) => {
  const response = await axiosClient.patch(`/marketplace/listings/${id}/`, data)
  return response.data
}

export const deleteCropListing = async (id) => {
  const response = await axiosClient.delete(`/marketplace/listings/${id}/`)
  return response.data
}

export const fetchMarketplaceStats = async () => {
  const response = await axiosClient.get('/marketplace/stats/')
  return response.data
}

export const fetchSentInquiries = async () => {
  const response = await axiosClient.get('/marketplace/inquiries/sent/')
  return response.data
}

export const fetchReceivedInquiries = async () => {
  const response = await axiosClient.get('/marketplace/inquiries/received/')
  return response.data
}

export const createBuyerInquiry = async (data) => {
  const response = await axiosClient.post('/marketplace/inquiries/', data)
  return response.data
}

export const respondToInquiry = async (id, status, farmerNotes = '') => {
  const response = await axiosClient.post(`/marketplace/inquiries/${id}/respond/`, {
    status,
    farmer_notes: farmerNotes,
  })
  return response.data
}
