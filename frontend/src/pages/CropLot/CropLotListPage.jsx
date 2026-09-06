/**
 * CropLotListPage.jsx — List all active crop lots with edit and delete.
 */
import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Navbar from '../../components/Navigation/Navbar'
import StatusBadge from '../../components/UI/StatusBadge'
import { fetchCropLots, deleteCropLot, parseApiError } from '../../api/cropLots'
import styles from './CropLot.module.css'

/* ── Icons ────────────────────────────────────────────────────────────────── */
const IconPlus    = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
const IconChart   = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
const IconEdit    = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
const IconTrash   = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function storageLabel(status) {
  return { farm: 'At Farm', warehouse: 'Warehouse', cold_storage: 'Cold Storage' }[status] || status
}

/* ── Delete confirmation modal ────────────────────────────────────────────── */
function DeleteModal({ lot, onConfirm, onCancel, isDeleting }) {
  return (
    <div className={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="del-title">
      <div className={styles.modal}>
        <h2 id="del-title">Remove crop lot?</h2>
        <p>
          This will remove your <strong>{lot.commodity_display}</strong> lot of{' '}
          <strong>{lot.quantity} {lot.unit}</strong> from active listings.
          You can re-add it any time.
        </p>
        <div className={styles.modalActions}>
          <button className={styles.btnSecondary} onClick={onCancel} disabled={isDeleting}>
            Cancel
          </button>
          <button className={styles.btnDangerSolid} onClick={onConfirm} disabled={isDeleting}>
            {isDeleting ? <><span className={styles.spinner} aria-hidden="true" /> Removing…</> : 'Remove lot'}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── Main page ────────────────────────────────────────────────────────────── */
export default function CropLotListPage() {
  const queryClient = useQueryClient()

  const [deletingLot, setDeletingLot] = useState(null)
  const [deleteError, setDeleteError] = useState('')

  /* fetch */
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['cropLots'],
    queryFn: fetchCropLots,
  })

  const lots = data?.results ?? []

  /* delete mutation */
  const deleteMutation = useMutation({
    mutationFn: (id) => deleteCropLot(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cropLots'] })
      setDeletingLot(null)
    },
    onError: (err) => {
      setDeleteError(parseApiError(err))
    },
  })

  function handleDeleteClick(lot) {
    setDeleteError('')
    setDeletingLot(lot)
  }

  function handleDeleteConfirm() {
    deleteMutation.mutate(deletingLot.id)
  }

  return (
    <div className={styles.page}>
      <Navbar />

      <main className={styles.main}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerText}>
            <h1>My Crop Lots</h1>
            <p>Manage your cotton and groundnut lots registered for AI market intelligence</p>
          </div>
          <Link to="/crop-lots/new" className={styles.btnPrimary}>
            <IconPlus /> Add new lot
          </Link>
        </div>

        {/* Server delete error */}
        {deleteError && (
          <div className={`${styles.alert} ${styles.alertError}`} role="alert">
            {deleteError}
          </div>
        )}

        {/* Loading */}
        {isLoading && <div className={styles.loadingCenter}><div className={styles.spinnerDark} aria-label="Loading…" /></div>}

        {/* Error */}
        {isError && (
          <div className={styles.errorBox} role="alert">
            Failed to load crop lots: {parseApiError(error)}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && lots.length === 0 && (
          <div className={styles.empty}>
            <div className={styles.emptyIcon} aria-hidden="true">🌱</div>
            <h2>No crop lots yet</h2>
            <p>Add your first cotton or groundnut lot to get market analysis and sell/hold recommendations.</p>
            <Link to="/crop-lots/new" className={styles.btnPrimary}>
              <IconPlus /> Add first lot
            </Link>
          </div>
        )}

        {/* Lot cards */}
        {!isLoading && !isError && lots.length > 0 && (
          <div className={styles.lotList}>
            {lots.map((lot) => (
              <article key={lot.id} className={styles.lotCard}>
                <div className={styles.lotCardTop}>
                  <div className={styles.lotCardInfo}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span className={styles.lotCardTitle}>{lot.commodity_display || lot.commodity}</span>
                      <StatusBadge status={lot.commodity} />
                      {lot.quality_grade && (
                        <StatusBadge status={lot.quality_grade} label={`Grade ${lot.quality_grade}`} />
                      )}
                    </div>
                    <div className={styles.lotCardMeta}>
                      <span>{lot.quantity} {lot.unit_display || lot.unit}</span>
                      <span className={styles.metaDot}>·</span>
                      <span>{storageLabel(lot.storage_status)}</span>
                      <span className={styles.metaDot}>·</span>
                      <span>Harvested {formatDate(lot.harvest_date)}</span>
                      {lot.variety && (
                        <>
                          <span className={styles.metaDot}>·</span>
                          <span>{lot.variety}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className={styles.lotCardActions}>
                    <Link
                      to={`/analysis/${lot.id}`}
                      className={styles.btnPrimary}
                      style={{ padding: '6px 14px', fontSize: '0.8125rem' }}
                      aria-label={`Analyze market and price forecast for ${lot.commodity_display} lot`}
                    >
                      <IconChart /> AI Analyze
                    </Link>
                    <Link
                      to={`/crop-lots/${lot.id}/edit`}
                      className={styles.btnEdit}
                      aria-label={`Edit ${lot.commodity_display} lot`}
                    >
                      <IconEdit /> Edit
                    </Link>
                    <button
                      className={styles.btnDanger}
                      onClick={() => handleDeleteClick(lot)}
                      aria-label={`Remove ${lot.commodity_display} lot`}
                      disabled={deleteMutation.isPending && deletingLot?.id === lot.id}
                    >
                      <IconTrash /> Remove
                    </button>
                  </div>
                </div>

                {/* Extra detail row */}
                <div className={styles.lotCardDetails}>
                  {lot.moisture_percent != null && (
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>Moisture</span>
                      <span className={styles.detailValue}>{lot.moisture_percent}%</span>
                    </div>
                  )}
                  {lot.storage_start_date && (
                    <div className={styles.detailItem}>
                      <span className={styles.detailLabel}>In storage since</span>
                      <span className={styles.detailValue}>{formatDate(lot.storage_start_date)}</span>
                    </div>
                  )}
                  <div className={styles.detailItem}>
                    <span className={styles.detailLabel}>Added</span>
                    <span className={styles.detailValue}>{formatDate(lot.created_at)}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </main>

      {/* Delete modal */}
      {deletingLot && (
        <DeleteModal
          lot={deletingLot}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeletingLot(null)}
          isDeleting={deleteMutation.isPending}
        />
      )}
    </div>
  )
}
