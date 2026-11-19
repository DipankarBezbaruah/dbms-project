import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopBar from '../components/TopBar';
import SubNav from '../components/SubNav';
import { api } from '../api';
import { useAuth } from '../AuthContext';
import './AdminDashboard.css';

/* ── icons ──────────────────────────────────────── */
const IconUserPlus = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/>
    <line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>
  </svg>
);
const IconStudent = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 3 3 6 3s6-1 6-3v-5"/>
  </svg>
);

const STAFF_ROLES = ['Warden', 'Mentor', 'HOD', 'Security', 'Admin'];
const DEPARTMENTS = ['CSE', 'ECE', 'ME', 'CE', 'FET'];

const IconList = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/>
    <line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/>
    <line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
  </svg>
);

/* ── Register Staff Form ────────────────────────── */
function RegisterStaff({ userId }) {
  const [hostels, setHostels] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [msg, setMsg] = useState(null);

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Warden',
    department: 'CSE',
    contact_no: '',
    hostel_id: '',
    shift: 'General',
  });

  useEffect(() => {
    api.getHostels().then(setHostels).catch(() => {});
  }, []);

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMsg(null);
    try {
      const body = {
        caller_user_id: userId,
        name: form.name,
        email: form.email,
        password: form.password,
        role: form.role,
      };

      // Add role-specific fields
      if (form.role === 'Warden') {
        body.contact_no = form.contact_no;
        if (form.hostel_id) body.hostel_id = parseInt(form.hostel_id);
      } else if (form.role === 'Mentor' || form.role === 'HOD') {
        body.department = form.department;
      } else if (form.role === 'Security') {
        body.shift = 'General';
      }

      const res = await api.registerStaff(body);
      setMsg({ type: 'success', text: `✅ ${form.role} "${form.name}" registered successfully! (User ID: ${res.user_id})` });
      setForm({
        name: '', email: '', password: '', role: form.role,
        department: 'CSE', contact_no: '', hostel_id: '', shift: 'General',
      });
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const needsDepartment = form.role === 'Mentor' || form.role === 'HOD';
  const needsContact = form.role === 'Warden';
  const needsHostel = form.role === 'Warden';

  return (
    <div className="admin-content">
      <div className="admin-form-container">
        <div className="admin-section-header">
          <span className="admin-section-title">REGISTER STAFF / ADMIN</span>
          <span className="admin-section-hint">Create accounts for Wardens, Mentors, HODs, Security, or other Admins</span>
        </div>

        {msg && (
          <div className={`alert alert--${msg.type}`} style={{ marginBottom: 16 }}>
            {msg.text}
          </div>
        )}

        <form className="admin-form" onSubmit={handleSubmit}>
          <div className="admin-form__row">
            <label className="admin-form__label">
              Role *
              <select className="admin-form__input" name="role" value={form.role}
                onChange={handleChange} required>
                {STAFF_ROLES.map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </label>
            <label className="admin-form__label">
              Full Name *
              <input className="admin-form__input" name="name" value={form.name}
                onChange={handleChange} placeholder="Enter full name" required />
            </label>
          </div>

          <div className="admin-form__row">
            <label className="admin-form__label">
              Email *
              <input className="admin-form__input" name="email" type="email" value={form.email}
                onChange={handleChange} placeholder="Enter email address" required />
            </label>
            <label className="admin-form__label">
              Password *
              <input className="admin-form__input" name="password" type="password" value={form.password}
                onChange={handleChange} placeholder="Set a password" required />
            </label>
          </div>

          {/* Conditional fields based on role */}
          {needsDepartment && (
            <div className="admin-form__row">
              <label className="admin-form__label">
                Department *
                <select className="admin-form__input" name="department" value={form.department}
                  onChange={handleChange} required>
                  {DEPARTMENTS.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
              </label>
              <div className="admin-form__label" />
            </div>
          )}

          {needsContact && (
            <div className="admin-form__row">
              <label className="admin-form__label">
                Contact Number *
                <input className="admin-form__input" name="contact_no" value={form.contact_no}
                  onChange={handleChange} placeholder="Enter contact number" required />
              </label>
              {needsHostel && (
                <label className="admin-form__label">
                  Assign to Hostel (optional)
                  <select className="admin-form__input" name="hostel_id" value={form.hostel_id}
                    onChange={handleChange}>
                    <option value="">Not assigned yet</option>
                    {hostels.map(h => (
                      <option key={h.hostel_id} value={h.hostel_id}>{h.hostel_name}</option>
                    ))}
                  </select>
                </label>
              )}
            </div>
          )}


          <button className="btn btn--admin-register" type="submit" disabled={submitting}>
            {submitting ? 'Registering...' : `➕ Register ${form.role}`}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ── Register Student (reuse from Warden) ──────── */
function RegisterStudent({ userId }) {
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
    hostel_id: '',
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
  }, []);

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
        department: 'CSE', hostel_id: '', room_no: '',
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
    <div className="admin-content">
      <div className="admin-form-container">
        <div className="admin-section-header">
          <span className="admin-section-title">REGISTER NEW STUDENT</span>
          <span className="admin-section-hint">Create student account with hostel and mentor assignment</span>
        </div>

        {msg && (
          <div className={`alert alert--${msg.type}`} style={{ marginBottom: 16 }}>
            {msg.text}
          </div>
        )}

        <form className="admin-form" onSubmit={handleSubmit}>
          <div className="admin-form__row">
            <label className="admin-form__label">
              Full Name *
              <input className="admin-form__input" name="name" value={form.name}
                onChange={handleChange} placeholder="Enter student full name" required />
            </label>
            <label className="admin-form__label">
              Email *
              <input className="admin-form__input" name="email" type="email" value={form.email}
                onChange={handleChange} placeholder="Enter student email" required />
            </label>
          </div>

          <div className="admin-form__row">
            <label className="admin-form__label">
              Password *
              <input className="admin-form__input" name="password" type="password" value={form.password}
                onChange={handleChange} placeholder="Set a password" required />
            </label>
            <label className="admin-form__label">
              Roll Number *
              <input className="admin-form__input" name="roll_no" value={form.roll_no}
                onChange={handleChange} placeholder="Enter roll number" required />
            </label>
          </div>

          <div className="admin-form__row">
            <label className="admin-form__label">
              Department *
              <select className="admin-form__input" name="department" value={form.department}
                onChange={handleChange} required>
                {DEPARTMENTS.map(d => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </label>
            <label className="admin-form__label">
              Contact Number *
              <input className="admin-form__input" name="contact_no" value={form.contact_no}
                onChange={handleChange} placeholder="Enter contact number" required />
            </label>
          </div>

          <div className="admin-form__row">
            <label className="admin-form__label">
              Hostel *
              <select className="admin-form__input" name="hostel_id" value={form.hostel_id}
                onChange={handleChange} required>
                <option value="">Select Hostel</option>
                {hostels.map(h => (
                  <option key={h.hostel_id} value={h.hostel_id}>{h.hostel_name}</option>
                ))}
              </select>
            </label>
            <label className="admin-form__label">
              Room No *
              <input className="admin-form__input" name="room_no" value={form.room_no}
                onChange={handleChange} placeholder="Enter room number" required />
            </label>
          </div>

          <div className="admin-form__row">
            <label className="admin-form__label">
              Mentor *
              <select className="admin-form__input" name="mentor_id" value={form.mentor_id}
                onChange={handleChange} required>
                <option value="">Select Mentor</option>
                {mentors.map(m => (
                  <option key={m.mentor_id} value={m.mentor_id}>{m.name} ({m.department})</option>
                ))}
              </select>
            </label>
            <div className="admin-form__label" />
          </div>

          <button className="btn btn--admin-register" type="submit" disabled={submitting}>
            {submitting ? 'Registering...' : '➕ Register Student'}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ── Manage Students (list + remove) ────────────── */
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
    if (!window.confirm(`Are you sure you want to remove "${studentName}"? This will delete all their outpass records too.`)) return;
    setRemoving(prev => ({ ...prev, [studentId]: true }));
    setMsg(null);
    try {
      await api.removeStudent(studentId, userId);
      setMsg({ type: 'success', text: `✅ "${studentName}" removed successfully.` });
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
    s.email.toLowerCase().includes(search.toLowerCase()) ||
    (s.department || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="admin-content">
      <div className="admin-form-container">
        <div className="admin-section-header">
          <span className="admin-section-title">MANAGE STUDENTS</span>
          <span className="admin-section-hint">{students.length} students registered</span>
        </div>

        {msg && (
          <div className={`alert alert--${msg.type}`} style={{ marginBottom: 16 }}>
            {msg.text}
          </div>
        )}

        <input
          type="text"
          placeholder="Search by name, roll no, email, or department..."
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
                <th style={{ padding: '8px 12px' }}>Email</th>
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
                  <td style={{ padding: '8px 12px', fontSize: 13, color: '#666' }}>{s.email}</td>
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
              {search ? 'No students match your search.' : 'No students registered yet.'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ── Dashboard shell ────────────────────────────── */
export default function AdminDashboard() {
  const { user, logout } = useAuth();

  const sidebarNav = [
    { path: '', label: 'Register Staff', icon: IconUserPlus },
    { path: '/student', label: 'Register Student', icon: IconStudent },
    { path: '/manage', label: 'Manage Students', icon: IconList },
  ];

  const subNavItems = [
    {
      path: '',
      label: 'Register Staff',
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/>
          <line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>
        </svg>
      ),
    },
    {
      path: '/student',
      label: 'Register Student',
      icon: (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 3 3 6 3s6-1 6-3v-5"/>
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
        role="Admin"
        userName={user?.name || 'Admin'}
        userDetail={[user?.email].filter(Boolean)}
        navItems={sidebarNav}
        basePath="/admin"
        onSignOut={logout}
      />
      <div className="dashboard__main">
        <TopBar
          title="Admin Console"
          subtitle="Manage all users and system configuration"
        />
        <div className="dashboard__body">
          <SubNav items={subNavItems} basePath="/admin" />
          <div className="dashboard__content dashboard__content--no-pad">
            <Routes>
              <Route path="/" element={<RegisterStaff userId={user?.user_id} />} />
              <Route path="/student" element={<RegisterStudent userId={user?.user_id} />} />
              <Route path="/manage" element={<ManageStudents userId={user?.user_id} />} />
              <Route path="*" element={<Navigate to="/admin" replace />} />
            </Routes>
          </div>
        </div>
      </div>
    </div>
  );
}
