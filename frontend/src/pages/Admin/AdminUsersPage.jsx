/**
 * AdminUsersPage.jsx — Admin User Directory & Management.
 */
import React, { useState, useEffect } from 'react'
import Navbar from '../../components/Navigation/Navbar'
import StatusBadge from '../../components/UI/StatusBadge'
import { fetchAdminUsers } from '../../api/auth'
import styles from './Admin.module.css'

export default function AdminUsersPage() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')

  useEffect(() => {
    fetchAdminUsers()
      .then((data) => setUsers(data?.results || data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = users.filter((u) => {
    if (roleFilter && u.role !== roleFilter) return false
    if (search) {
      const term = search.toLowerCase()
      return u.email?.toLowerCase().includes(term) || u.username?.toLowerCase().includes(term)
    }
    return true
  })

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        <div className={styles.headerRow}>
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff' }}>
              🛡️ User Directory &amp; RBAC Control
            </h1>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
              Overview of all registered farmers, buyers, and platform administrators
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              type="text"
              placeholder="🔍 Search users…"
              className={styles.filterInput}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className={styles.filterSelect}
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="">All Roles</option>
              <option value="farmer">Farmers</option>
              <option value="buyer">Buyers</option>
              <option value="admin">Admins</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="kl-loading-screen">
            <div className="kl-spinner" />
            <p>Loading user directory…</p>
          </div>
        ) : (
          <div className="glass-panel" style={{ padding: 'var(--sp-6)' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className={styles.table} style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th>User ID</th>
                    <th>Email Address</th>
                    <th>Username</th>
                    <th>Role</th>
                    <th>Profile Info</th>
                    <th>Joined Date</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((u) => (
                    <tr key={u.id}>
                      <td style={{ fontWeight: 700, color: '#38bdf8' }}>#{u.id}</td>
                      <td style={{ fontWeight: 600, color: '#ffffff' }}>{u.email}</td>
                      <td>{u.username}</td>
                      <td><StatusBadge status={u.role} /></td>
                      <td style={{ fontSize: '0.85rem' }}>
                        {u.farmer_profile && (
                          <span style={{ color: '#34d399' }}>
                            📍 {u.farmer_profile.village || 'Village'}, {u.farmer_profile.district || 'District'}
                          </span>
                        )}
                        {u.buyer_profile && (
                          <span style={{ color: '#38bdf8' }}>
                            🏢 {u.buyer_profile.company_name || 'Independent Buyer'} ({u.buyer_profile.district || 'Gujarat'})
                          </span>
                        )}
                        {!u.farmer_profile && !u.buyer_profile && <span style={{ color: '#94a3b8' }}>System Account</span>}
                      </td>
                      <td>{new Date(u.date_joined).toLocaleDateString('en-IN')}</td>
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
