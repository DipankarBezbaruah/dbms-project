import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import SubNav from '../components/SubNav';
import { api } from '../api';
import { useAuth } from '../AuthContext';
import './WardenDashboard.css';

const IconQueue = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/>
    <line x1="9" y1="21" x2="9" y2="9"/>
  </svg>
);
const IconHistory = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
  </svg>
);
const IconChart = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="7" width="4" height="14" rx="1"/>
    <rect x="17" y="3" width="4" height="18" rx="1"/>
  </svg>
);

function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}
function fmtDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) +
    ', ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
}

function statusBadge(status) {
  if (status === 'Approved') return 'badge--approved';
  if (status === 'Rejected') return 'badge--rejected';
  return 'badge--pending';
}

/* ── Mentee Pending Requests (with Approve/Reject) ──────────── */
function MenteePending({ mentorId, userId, onActionComplete }) {
  const [outpasses, setOutpasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [remarks, setRemarks] = useState({});
  const [actionLoading, setActionLoading] = useState({});
  const [actionMsg, setActionMsg] = useState({});

  const fetchPending = useCallback(() => {
    if (!mentorId) return;
    setLoading(true);
    api.getMentorPending(mentorId)
      .then((data) => {
        setOutpasses(data);
        if (onActionComplete) onActionComplete(data.length);
      })
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [mentorId, onActionComplete]);

  useEffect(() => { fetchPending(); }, [fetchPending]);

  const handleAction = async (outpassId, action) => {
    setActionLoading(prev => ({ ...prev, [outpassId]: action }));
    setActionMsg(prev => ({ ...prev, [outpassId]: null }));
    try {
      const remark = remarks[outpassId] || '';
      if (action === 'approve') {
        await api.approveOutpass(outpassId, userId, remark);
        setActionMsg(prev => ({ ...prev, [outpassId]: { type: 'success', text: 'Approved by Mentor!' } }));
      } else {
        await api.rejectOutpass(outpassId, userId, remark);
        setActionMsg(prev => ({ ...prev, [outpassId]: { type: 'success', text: 'Rejected by Mentor.' } }));
      }
      setTimeout(fetchPending, 600);
    } catch (e) {
      setActionMsg(prev => ({ ...prev, [outpassId]: { type: 'error', text: e.message } }));
    } finally {
      setActionLoading(prev => ({ ...prev, [outpassId]: null }));
    }
  };

  return (
    <div className="warden-content">
      <div className="warden-queue">
        <div className="warden-queue__header">
          <span className="warden-queue__title">MENTEE PENDING REQUESTS</span>
          <span className="warden-queue__count">{outpasses.length} awaiting</span>
        </div>
        {loading && <div className="loading">Loading...</div>}
        {err && <div className="alert alert--error">{err}</div>}
        <div className="warden-queue__list">
          {outpasses.map((op) => (
            <div key={op.outpass_id} className="request-card">
              <div className="request-card__header">
                <div className="request-card__avatar">{getInitials(op.student_name)}</div>
                <div className="request-card__info">
                  <div className="request-card__name">{op.student_name}</div>
                  <div className="request-card__meta">{op.roll_no} &middot; OP-{String(op.outpass_id).padStart(4, '0')}</div>
                </div>
                <span className={`badge ${statusBadge(op.status)}`}>{op.status}</span>
              </div>
              <div className="request-card__reason">{op.reason}</div>
              <div className="request-card__dest">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="var(--terracotta)" stroke="none">
                  <circle cx="12" cy="10" r="3"/><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                </svg>
                {op.destination}
              </div>
              <div className="request-card__time">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                </svg>
                {fmtDate(op.requested_departure)} &rarr; {fmtDate(op.requested_return)}
              </div>

              {/* Remark input */}
              <input
                className="request-card__remark-input"
                type="text"
                placeholder="Optional mentor remark..."
                value={remarks[op.outpass_id] || ''}
                onChange={(e) => setRemarks(prev => ({ ...prev, [op.outpass_id]: e.target.value }))}
              />

              {/* Action message */}
              {actionMsg[op.outpass_id] && (
                <div className={`alert alert--${actionMsg[op.outpass_id].type}`} style={{ marginBottom: 8 }}>
                  {actionMsg[op.outpass_id].text}
                </div>
              )}

              {/* Action buttons */}
              <div className="request-card__actions">
                <button
                  className="btn btn--approve"
                  disabled={!!actionLoading[op.outpass_id]}
                  onClick={() => handleAction(op.outpass_id, 'approve')}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  {actionLoading[op.outpass_id] === 'approve' ? 'Approving...' : 'Approve'}
                </button>
                <button
                  className="btn btn--reject"
                  disabled={!!actionLoading[op.outpass_id]}
                  onClick={() => handleAction(op.outpass_id, 'reject')}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                  {actionLoading[op.outpass_id] === 'reject' ? 'Rejecting...' : 'Reject'}
                </button>
              </div>
            </div>
          ))}
          {!loading && outpasses.length === 0 && <div className="empty-state">No pending mentee requests.</div>}
        </div>
      </div>
      <div className="warden-detail">
        <div className="warden-detail__empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--brown-200)" strokeWidth="1.5">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
          </svg>
          <p>Mentors can review and approve or reject their mentees&apos; outpasses.</p>
        </div>
      </div>
    </div>
  );
}

/* ── Mentee History (all outpasses) ────────────────── */
function MenteeHistory({ mentorId }) {
  const [outpasses, setOutpasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!mentorId) return;
    api.getMentorAllOutpasses(mentorId)
      .then(setOutpasses).catch((e) => setErr(e.message)).finally(() => setLoading(false));
  }, [mentorId]);

  return (
    <div className="warden-content">
      <div className="warden-queue" style={{ flex: 1 }}>
        <div className="warden-queue__header">
          <span className="warden-queue__title">MENTEE OUTPASS HISTORY</span>
          <span className="warden-queue__count">{outpasses.length} total</span>
        </div>
        {loading && <div className="loading">Loading...</div>}
        {err && <div className="alert alert--error">{err}</div>}
        <div className="warden-queue__list">
          {outpasses.map((op) => (
            <div key={op.outpass_id} className="request-card">
              <div className="request-card__header">
                <div className="request-card__avatar">{getInitials(op.student_name)}</div>
                <div className="request-card__info">
                  <div className="request-card__name">{op.student_name}</div>
                  <div className="request-card__meta">{op.roll_no} &middot; OP-{String(op.outpass_id).padStart(4, '0')}</div>
                </div>
                <span className={`badge ${statusBadge(op.status)}`}>
                  {op.is_overdue ? (op.overdue_by_minutes > 0 ? `Overdue ${op.overdue_by_minutes}m` : 'Overdue') : op.status}
                </span>
              </div>
              <div className="request-card__reason">{op.reason}</div>
              <div className="request-card__dest">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="var(--terracotta)" stroke="none">
                  <circle cx="12" cy="10" r="3"/><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                </svg>
                {op.destination}
              </div>
              <div className="request-card__time">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                </svg>
                {fmtDate(op.requested_departure)} &rarr; {fmtDate(op.requested_return)}
              </div>
              {op.approval && (
                <div className="request-card__time" style={{ color: 'var(--brown-600, #5a4a3a)', fontWeight: 500 }}>
                  Decided by {op.approval.approver_name || op.approval.approver_role} ({op.approval.approver_role}): &ldquo;{op.warden_remark || op.approval.decision}&rdquo;
                </div>
              )}
            </div>
          ))}
          {!loading && outpasses.length === 0 && <div className="empty-state">No outpass history for your mentees.</div>}
        </div>
      </div>
    </div>
  );
}

/* ── Mentee Overdue Overview ───────────────────────── */
function MenteeOverdue({ mentorId }) {
  const [overdue, setOverdue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!mentorId) return;
    api.getMentorOverdueReport(mentorId)
      .then(setOverdue)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [mentorId]);

  return (
    <div className="warden-content">
      <div className="warden-queue" style={{ flex: 1 }}>
        <div className="warden-queue__header">
          <span className="warden-queue__title">OVERDUE MENTEES</span>
          <span className="warden-queue__count">{overdue.length} overdue</span>
        </div>

        {loading && <div className="loading">Loading...</div>}
        {err && <div className="alert alert--error">{err}</div>}

        <div className="warden-queue__list">
          {overdue.map((op) => (
            <div key={op.outpass_id} className="request-card request-card--overdue">
              <div className="request-card__header">
                <div className="request-card__avatar request-card__avatar--overdue">
                  {getInitials(op.student_name)}
                </div>
                <div className="request-card__info">
                  <div className="request-card__name">{op.student_name}</div>
                  <div className="request-card__meta">
                    {op.roll_no} &middot; OP-{String(op.outpass_id).padStart(4, '0')}
                  </div>
                </div>
                <span className="badge badge--overdue">
                  Overdue {op.overdue_by_minutes}m
                </span>
              </div>
              <div className="request-card__reason">{op.reason}</div>
              <div className="request-card__dest">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="var(--terracotta)" stroke="none">
                  <circle cx="12" cy="10" r="3"/><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                </svg>
                {op.destination}
              </div>
              <div className="request-card__time">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                </svg>
                Expected return: {fmtDate(op.requested_return)}
              </div>
              {op.gate_log && (
                <div className="request-card__time">
                  Exit logged: {fmtDate(op.gate_log.actual_exit_time)}
                </div>
              )}
            </div>
          ))}
          {!loading && overdue.length === 0 && (
            <div className="empty-state">No overdue mentees. All clear!</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function MentorDashboard() {
  const { user, logout } = useAuth();

  const mentorId = user?.mentor_id;
  const userId = user?.user_id;
  const department = user?.department || 'Dept';

  const [pendingCount, setPendingCount] = useState(0);
  const [overdueCount, setOverdueCount] = useState(0);

  useEffect(() => {
    if (mentorId) {
      api.getMentorPending(mentorId).then(d => setPendingCount(d.length)).catch(() => {});
      api.getMentorOverdueReport(mentorId).then(d => setOverdueCount(d.length)).catch(() => {});
    }
  }, [mentorId]);

  const sidebarNav = [
    { path: '', label: 'Mentee Requests', icon: IconQueue, badge: pendingCount },
    { path: '/history', label: 'Mentee History', icon: IconHistory },
    { path: '/overview', label: 'Overdue', icon: IconChart, badge: overdueCount },
  ];
  const subNavItems = [
    { path: '', label: 'Pending', badge: pendingCount, icon: IconQueue },
    { path: '/history', label: 'History', icon: IconHistory },
    { path: '/overview', label: 'Overdue', badge: overdueCount, icon: IconChart },
  ];

  return (
    <div className="dashboard">
      <Sidebar role="Mentor" userName={`${user?.name || 'Mentor'} · ${department}`} navItems={sidebarNav} basePath="/mentor" onSignOut={logout} />
      <div className="dashboard__main">
        <TopBar title="Mentor View" subtitle={`${user?.name || 'Mentor'} · ${department} Dept · ${pendingCount} pending · ${overdueCount} overdue`} />
        <div className="dashboard__body">
          <SubNav items={subNavItems} basePath="/mentor" />
          <div className="dashboard__content dashboard__content--no-pad">
            <Routes>
              <Route path="/" element={<MenteePending mentorId={mentorId} userId={userId} onActionComplete={setPendingCount} />} />
              <Route path="/history" element={<MenteeHistory mentorId={mentorId} />} />
              <Route path="/overview" element={<MenteeOverdue mentorId={mentorId} />} />
              <Route path="*" element={<Navigate to="/mentor" replace />} />
            </Routes>
          </div>
        </div>
      </div>
    </div>
  );
}
