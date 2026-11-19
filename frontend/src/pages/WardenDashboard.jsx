import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import SubNav from '../components/SubNav';
import { api } from '../api';
import { useAuth } from '../AuthContext';
import './WardenDashboard.css';

/* ── icons ──────────────────────────────────────── */
const IconQueue = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/>
    <line x1="9" y1="21" x2="9" y2="9"/>
  </svg>
);
const IconChart = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="7" width="4" height="14" rx="1"/>
    <rect x="17" y="3" width="4" height="18" rx="1"/>
  </svg>
);
const IconUserPlus = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/>
    <line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>
  </svg>
);
const IconList = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
    <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
    <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
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

/* ── Pending Queue ──────────────────────────────── */
function PendingQueue({ userId, hostelId }) {
  const [outpasses, setOutpasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [remarks, setRemarks] = useState({});
  const [actionLoading, setActionLoading] = useState({});
  const [actionMsg, setActionMsg] = useState({});

  const fetchPending = useCallback(() => {
    setLoading(true);
    api.getPendingOutpasses(hostelId)
      .then(setOutpasses)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [hostelId]);

  useEffect(() => { fetchPending(); }, [fetchPending]);

  const handleAction = async (outpassId, action) => {
    setActionLoading(prev => ({ ...prev, [outpassId]: action }));
    setActionMsg(prev => ({ ...prev, [outpassId]: null }));
    try {
      const remark = remarks[outpassId] || '';
      if (action === 'approve') {
        await api.approveOutpass(outpassId, userId, remark);
        setActionMsg(prev => ({ ...prev, [outpassId]: { type: 'success', text: 'Approved!' } }));
      } else {
        await api.rejectOutpass(outpassId, userId, remark);
        setActionMsg(prev => ({ ...prev, [outpassId]: { type: 'success', text: 'Rejected.' } }));
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
          <span className="warden-queue__title">PENDING REQUESTS</span>
          <span className="warden-queue__count">{outpasses.length} awaiting</span>
        </div>

        {loading && <div className="loading">Loading...</div>}
        {err && <div className="alert alert--error">{err}</div>}

        <div className="warden-queue__list">
          {outpasses.map((op) => (
            <div key={op.outpass_id} className="request-card">
              {/* Header */}
              <div className="request-card__header">
                <div className="request-card__avatar">{getInitials(op.student_name)}</div>
                <div className="request-card__info">
                  <div className="request-card__name">{op.student_name}</div>
                  <div className="request-card__meta">
                    {op.roll_no} &middot; OP-{String(op.outpass_id).padStart(4, '0')}
                  </div>
                </div>
              </div>

              {/* Body */}
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
                placeholder="Optional remark..."
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
          {!loading && outpasses.length === 0 && (
            <div className="empty-state">No pending requests.</div>
          )}
        </div>
      </div>

      {/* Right panel placeholder */}
      <div className="warden-detail">
        <div className="warden-detail__empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--brown-200)" strokeWidth="1.5">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          <p>Select a request to view student history</p>
        </div>
      </div>
    </div>
  );
}

/* ── Overdue Overview ───────────────────────────── */
function Overview({ hostelId }) {
  const [overdue, setOverdue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.getOverdueReport(hostelId)
      .then(setOverdue)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  }, [hostelId]);

  return (
    <div className="warden-content">
      <div className="warden-queue" style={{ flex: 1 }}>
        <div className="warden-queue__header">
          <span className="warden-queue__title">OVERDUE STUDENTS</span>
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
            <div className="empty-state">No overdue students. All clear!</div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Register Student Form ──────────────────────── */
function RegisterStudent({ userId, hostelId }) {
  const [hostels, setHostels] = useState([]);
  const [mentors, setMentors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState(null);

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    roll_no: '',
    department: 'CSE',
    hostel_id: hostelId || '',
    room_no: '',
    contact_no: '',
    mentor_id: '',
  });

  useEffect(() => {
    Promise.all([api.getHostels(), api.getMentors()])
      .then(([h, m]) => {
        setHostels(h);
        setMentors(m);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [hostelId]);

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMsg(null);
    try {
      const body = {
        ...form,
        hostel_id: parseInt(form.hostel_id),
        room_no: form.room_no,
        mentor_id: parseInt(form.mentor_id),
        caller_user_id: userId,
      };
      const res = await api.registerStudent(body);
      setMsg({ type: 'success', text: `✅ Student "${form.name}" registered successfully! (ID: ${res.student_id})` });
      setForm({
        name: '', email: '', password: '', roll_no: '',
        department: 'CSE', hostel_id: hostelId || '', room_no: '',
        contact_no: '', mentor_id: '',
      });
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="warden-content">
      <div className="register-form-container">
        <div className="warden-queue__header">
          <span className="warden-queue__title">REGISTER NEW STUDENT</span>
        </div>

        {msg && (
          <div className={`alert alert--${msg.type}`} style={{ marginBottom: 16 }}>
            {msg.text}
          </div>
        )}

        <form className="register-form" onSubmit={handleSubmit}>
          <div className="register-form__row">
            <label className="register-form__label">
              Full Name *
              <input className="register-form__input" name="name" value={form.name}
                onChange={handleChange} placeholder="Enter student full name" required />
            </label>
            <label className="register-form__label">
              Email *
              <input className="register-form__input" name="email" type="email" value={form.email}
                onChange={handleChange} placeholder="Enter student email" required />
            </label>
          </div>

          <div className="register-form__row">
            <label className="register-form__label">
              Password *
              <input className="register-form__input" name="password" type="password" value={form.password}
                onChange={handleChange} placeholder="Set a password" required />
            </label>
            <label className="register-form__label">
              Roll Number *
              <input className="register-form__input" name="roll_no" value={form.roll_no}
                onChange={handleChange} placeholder="Enter roll number" required />
            </label>
          </div>

          <div className="register-form__row">
            <label className="register-form__label">
              Department *
              <select className="register-form__input" name="department" value={form.department}
                onChange={handleChange} required>
                <option value="CSE">CSE</option>
                <option value="ECE">ECE</option>
                <option value="ME">ME</option>
                <option value="CE">CE</option>
                <option value="FET">FET</option>
              </select>
            </label>
            <label className="register-form__label">
              Contact Number *
              <input className="register-form__input" name="contact_no" value={form.contact_no}
                onChange={handleChange} placeholder="Enter contact number" required />
            </label>
          </div>

          <div className="register-form__row">
            <label className="register-form__label">
              Hostel *
              <select className="register-form__input" name="hostel_id" value={form.hostel_id}
                onChange={handleChange} required>
                <option value="">Select Hostel</option>
                {hostels.map(h => (
                  <option key={h.hostel_id} value={h.hostel_id}>{h.hostel_name}</option>
                ))}
              </select>
            </label>
            <label className="register-form__label">
              Room No *
              <input className="register-form__input" name="room_no" value={form.room_no}
                onChange={handleChange} placeholder="Enter room number" required />
            </label>
          </div>

          <div className="register-form__row">
            <label className="register-form__label">
              Mentor *
              <select className="register-form__input" name="mentor_id" value={form.mentor_id}
                onChange={handleChange} required>
                <option value="">Select Mentor</option>
                {mentors.map(m => (
                  <option key={m.mentor_id} value={m.mentor_id}>{m.name} ({m.department})</option>
                ))}
              </select>
            </label>
            <div className="register-form__label" />
          </div>

          <button className="btn btn--register" type="submit" disabled={submitting}>
            {submitting ? 'Registering...' : '➕ Register Student'}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ── Manage Students (Warden) ───────────────────── */
function ManageStudents({ userId }) {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [removing, setRemoving] = useState({});
  const [msg, setMsg] = useState(null);
  const [search, setSearch] = useState('');

  const fetchStudents = () => {
    setLoading(true);
    api.getStudents()
      .then(setStudents)
      .catch((e) => setErr(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchStudents(); }, []);

  const handleRemove = async (studentId, studentName) => {
    if (!window.confirm(`Remove "${studentName}"? This deletes all their outpass records too.`)) return;
    setRemoving(prev => ({ ...prev, [studentId]: true }));
    setMsg(null);
    try {
      await api.removeStudent(studentId, userId);
      setMsg({ type: 'success', text: `✅ "${studentName}" removed.` });
      fetchStudents();
    } catch (e) {
      setMsg({ type: 'error', text: e.message });
    } finally {
      setRemoving(prev => ({ ...prev, [studentId]: false }));
    }
  };

  const filtered = students.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.roll_no.toLowerCase().includes(search.toLowerCase()) ||
    (s.department || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="warden-content">
      <div className="register-form-container">
        <div className="warden-queue__header">
          <span className="warden-queue__title">MANAGE STUDENTS</span>
          <span className="warden-queue__count">{students.length} total</span>
        </div>

        {msg && (
          <div className={`alert alert--${msg.type}`} style={{ marginBottom: 16 }}>{msg.text}</div>
        )}

        <input
          type="text"
          placeholder="Search by name, roll no, or department..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%', padding: '10px 14px', marginBottom: 16,
            border: '1px solid var(--brown-200, #d4c5b0)', borderRadius: 8,
            fontSize: 14, boxSizing: 'border-box',
          }}
        />

        {loading && <div className="loading">Loading...</div>}
        {err && <div className="alert alert--error">{err}</div>}

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--brown-200, #d4c5b0)', textAlign: 'left' }}>
                <th style={{ padding: '8px 12px' }}>Name</th>
                <th style={{ padding: '8px 12px' }}>Roll No</th>
                <th style={{ padding: '8px 12px' }}>Dept</th>
                <th style={{ padding: '8px 12px' }}>Hostel</th>
                <th style={{ padding: '8px 12px' }}>Room</th>
                <th style={{ padding: '8px 12px' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(s => (
                <tr key={s.student_id} style={{ borderBottom: '1px solid var(--brown-100, #ede4d8)' }}>
                  <td style={{ padding: '8px 12px', fontWeight: 500 }}>{s.name}</td>
                  <td style={{ padding: '8px 12px' }}>{s.roll_no}</td>
                  <td style={{ padding: '8px 12px' }}>{s.department}</td>
                  <td style={{ padding: '8px 12px' }}>{s.hostel_name}</td>
                  <td style={{ padding: '8px 12px' }}>{s.room_no}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <button
                      onClick={() => handleRemove(s.student_id, s.name)}
                      disabled={removing[s.student_id]}
                      style={{
                        padding: '4px 12px', fontSize: 13, cursor: 'pointer',
                        background: '#d32f2f', color: '#fff', border: 'none',
                        borderRadius: 6, opacity: removing[s.student_id] ? 0.5 : 1,
                      }}
                    >
                      {removing[s.student_id] ? 'Removing...' : 'Remove'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && filtered.length === 0 && (
            <div style={{ textAlign: 'center', padding: 24, color: '#999' }}>
              {search ? 'No students match.' : 'No students registered.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Dashboard shell ────────────────────────────── */
export default function WardenDashboard() {
  const { user, logout } = useAuth();

  const wardenId = user?.warden_id;
  const hostelId = user?.hostel_id;
  const hostelName = user?.hostel_name || 'Hostel';

  const [pendingCount, setPendingCount] = useState(0);
  const [overdueCount, setOverdueCount] = useState(0);

  useEffect(() => {
    if (hostelId) {
      api.getPendingOutpasses(hostelId)
        .then(data => setPendingCount(data.length))
        .catch(() => {});
      api.getOverdueReport(hostelId)
        .then(data => setOverdueCount(data.length))
        .catch(() => {});
    }
  }, [hostelId]);

  const sidebarNav = [
    { path: '', label: 'Pending Queue', icon: IconQueue, badge: pendingCount },
    { path: '/overview', label: 'Overdue', icon: IconChart, badge: overdueCount },
    { path: '/register', label: 'Register Student', icon: IconUserPlus },
    { path: '/manage', label: 'Manage Students', icon: IconList },
  ];

  const subNavItems = [
    {
      path: '',
      label: 'Pending Queue',
      badge: pendingCount,
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/>
          <line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
      ),
    },
    {
      path: '/overview',
      label: 'Overdue',
      badge: overdueCount,
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="12" width="4" height="9" rx="1"/><rect x="10" y="7" width="4" height="14" rx="1"/>
          <rect x="17" y="3" width="4" height="18" rx="1"/>
        </svg>
      ),
    },
    {
      path: '/register',
      label: 'Register Student',
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/>
          <line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>
        </svg>
      ),
    },
    {
      path: '/manage',
      label: 'Manage Students',
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
      ),
    },
  ];

  return (
    <div className="dashboard">
      <Sidebar
        role="Warden"
        userName={`${user?.name || 'Warden'} · ${hostelName}`}
        userDetail={[
          user?.email,
          user?.contact_no ? `Contact: ${user.contact_no}` : null,
        ].filter(Boolean)}
        navItems={sidebarNav}
        basePath="/warden"
        onSignOut={logout}
      />
      <div className="dashboard__main">
        <TopBar
          title="Warden Console"
          subtitle={`${hostelName} · Pending: ${pendingCount} · Overdue: ${overdueCount}`}
        />
        <div className="dashboard__body">
          <SubNav items={subNavItems} basePath="/warden" />
          <div className="dashboard__content dashboard__content--no-pad">
            <Routes>
              <Route path="/" element={<PendingQueue userId={user?.user_id} hostelId={hostelId} />} />
              <Route path="/overview" element={<Overview hostelId={hostelId} />} />
              <Route path="/register" element={<RegisterStudent userId={user?.user_id} hostelId={hostelId} />} />
              <Route path="/manage" element={<ManageStudents userId={user?.user_id} />} />
              <Route path="*" element={<Navigate to="/warden" replace />} />
            </Routes>
          </div>
        </div>
      </div>
    </div>
  );
}
