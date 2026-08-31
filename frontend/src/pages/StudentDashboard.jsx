import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import SubNav from '../components/SubNav';
import { api } from '../api';
import { useAuth } from '../AuthContext';
import './StudentDashboard.css';

/* ── SVG icon fragments ────────────────────────── */
const IconPlus = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);
const IconList = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
  </svg>
);

function getTodayDateStr(offsetDays = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().split('T')[0];
}

function getCurrentTimeStr(offsetHours = 0) {
  const d = new Date();
  d.setHours(d.getHours() + offsetHours);
  const h = String(d.getHours()).padStart(2, '0');
  const m = String(d.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

/* ── New Request form ──────────────────────────── */
function NewRequest({ studentId }) {
  const [form, setForm] = useState({
    reason: '',
    destination: '',
    depDate: getTodayDateStr(0),
    depTime: getCurrentTimeStr(1),
    retDate: getTodayDateStr(1),
    retTime: '18:00',
  });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    setErr(null);
    try {
      const departureIso = `${form.depDate}T${form.depTime || '09:00'}`;
      const returnIso = `${form.retDate}T${form.retTime || '18:00'}`;

      const res = await api.createOutpass({
        student_id: studentId,
        reason: form.reason,
        destination: form.destination,
        requested_departure: departureIso,
        requested_return: returnIso,
      });
      setMsg(`Outpass #${res.outpass_id} submitted successfully!`);
      setForm({
        reason: '',
        destination: '',
        depDate: getTodayDateStr(0),
        depTime: getCurrentTimeStr(1),
        retDate: getTodayDateStr(1),
        retTime: '18:00',
      });
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="student-page">
      <h2 className="student-page__heading">New Outpass Request</h2>
      <p className="student-page__subheading">Submit a request to leave the hostel premises.</p>

      {msg && <div className="alert alert--success">{msg}</div>}
      {err && <div className="alert alert--error">{err}</div>}

      <form className="outpass-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Reason for leaving</label>
          <textarea
            className="form-textarea"
            placeholder="e.g. Medical appointment, family function, interview..."
            value={form.reason}
            onChange={(e) => setForm({ ...form, reason: e.target.value })}
            required
            rows={3}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Destination</label>
          <input
            className="form-input"
            type="text"
            placeholder="Full address or location name"
            value={form.destination}
            onChange={(e) => setForm({ ...form, destination: e.target.value })}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group form-group--half">
            <label className="form-label">Departure Date &amp; Time</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                className="form-input"
                type="date"
                style={{ flex: 1.4 }}
                value={form.depDate}
                onChange={(e) => setForm({ ...form, depDate: e.target.value })}
                required
              />
              <input
                className="form-input"
                type="time"
                style={{ flex: 1 }}
                value={form.depTime}
                onChange={(e) => setForm({ ...form, depTime: e.target.value })}
                required
              />
            </div>
          </div>
          <div className="form-group form-group--half">
            <label className="form-label">Expected Return Date &amp; Time</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                className="form-input"
                type="date"
                style={{ flex: 1.4 }}
                value={form.retDate}
                onChange={(e) => setForm({ ...form, retDate: e.target.value })}
                required
              />
              <input
                className="form-input"
                type="time"
                style={{ flex: 1 }}
                value={form.retTime}
                onChange={(e) => setForm({ ...form, retTime: e.target.value })}
                required
              />
            </div>
          </div>
        </div>

        <button className="btn btn--primary btn--full" type="submit" disabled={loading}>
          {loading ? 'Submitting...' : '+ Submit Outpass Request'}
        </button>
      </form>
    </div>
  );
}

/* ── My Outpasses list ─────────────────────────── */
function MyOutpasses({ studentId }) {
  const [outpasses, setOutpasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.getStudentOutpasses(studentId)
      .then(setOutpasses)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [studentId]);

  const statusClass = (s) => {
    if (s === 'Approved') return 'badge--approved';
    if (s === 'Rejected') return 'badge--rejected';
    return 'badge--pending';
  };

  const fmtDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) +
      ', ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
  };

  return (
    <div className="student-page">
      <h2 className="student-page__heading">My Outpasses</h2>
      <p className="student-page__subheading">View your outpass request history.</p>

      {loading && <div className="loading">Loading...</div>}
      {err && <div className="alert alert--error">{err}</div>}

      <div className="outpass-list">
        {outpasses.map((op) => (
          <div key={op.outpass_id} className="outpass-card">
            <div className="outpass-card__header">
              <div className="outpass-card__id">OP-{String(op.outpass_id).padStart(4, '0')}</div>
              <span className={`badge ${statusClass(op.status)}`}>
                {op.is_overdue ? 'Overdue' : op.status}
              </span>
            </div>
            <div className="outpass-card__reason">{op.reason}</div>
            <div className="outpass-card__meta">
              <span className="outpass-card__dest">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="var(--terracotta)" stroke="none">
                  <circle cx="12" cy="10" r="3"/><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                </svg>
                {op.destination}
              </span>
            </div>
            {(op.hostel_name || op.warden_name) && (
              <div className="outpass-card__meta" style={{ fontSize: '0.85em', color: 'var(--brown-500, #6b5a4a)' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><polyline points="9 22 9 12 15 12 15 22"/>
                </svg>
                {op.hostel_name}{op.warden_name ? ` · Warden: ${op.warden_name}` : ''}
              </div>
            )}
            <div className="outpass-card__times">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
              {fmtDate(op.requested_departure)} &rarr; {fmtDate(op.requested_return)}
            </div>

            {op.approvals && op.approvals.length > 0 && op.approvals.filter(a => a.remark).map(a => (
              <div key={a.approval_id} className="outpass-card__remark" style={{ marginTop: '4px', fontStyle: 'italic', color: 'var(--brown-600, #5a4a3a)' }}>
                {a.approver_role}: &ldquo;{a.remark}&rdquo;
              </div>
            ))}
          </div>
        ))}
        {!loading && outpasses.length === 0 && (
          <div className="empty-state">No outpass requests yet.</div>
        )}
      </div>
    </div>
  );
}

/* ── Dashboard shell ───────────────────────────── */
export default function StudentDashboard() {
  const { user, logout } = useAuth();

  const studentId = user?.student_id;
  const hostelName = user?.hostel_name || 'Hostel';
  const wardenName = user?.warden_name || '';
  const roomNo = user?.room_no ? `Room ${user.room_no}` : '';

  const sidebarNav = [
    { path: '', label: '+ New Request', icon: IconPlus },
    { path: '/history', label: 'My Outpasses', icon: IconList },
  ];

  const subNavItems = [
    {
      path: '',
      label: '+ New Request',
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
      ),
    },
    {
      path: '/history',
      label: 'My Outpasses',
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
      ),
    },
  ];

  return (
    <div className="dashboard">
      <Sidebar
        role="Student"
        userName={user?.name || 'Student'}
        userDetail={[
          user?.email,
          user?.roll_no ? `Roll No: ${user.roll_no}` : null,
          user?.department ? `Dept: ${user.department}` : null,
          user?.room_no ? `Room: ${user.room_no}` : null,
        ].filter(Boolean)}
        navItems={sidebarNav}
        basePath="/student"
        onSignOut={logout}
      />
      <div className="dashboard__main">
        <TopBar title="Student Portal" subtitle={`${hostelName}${wardenName ? ` · Warden: ${wardenName}` : ''} · ${roomNo}`} />
        <div className="dashboard__body">
          <SubNav items={subNavItems} basePath="/student" />
          <div className="dashboard__content">
            <Routes>
              <Route path="/" element={<NewRequest studentId={studentId} />} />
              <Route path="/history" element={<MyOutpasses studentId={studentId} />} />
              <Route path="*" element={<Navigate to="/student" replace />} />
            </Routes>
          </div>
        </div>
      </div>
    </div>
  );
}
