import { useNavigate } from 'react-router-dom';
import './SignIn.css';

const roles = [
  {
    key: 'student',
    label: 'Student',
    desc: 'Submit outpass requests, track approvals, and view your leave history.',
    user: 'Rahul D. \u00b7 TU2023001',
    color: 'var(--terracotta)',
    colorBg: 'var(--terracotta-bg)',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
  {
    key: 'mentor',
    label: 'Mentor',
    desc: 'Monitor mentee outpass activity and flag concerns.',
    user: 'Dr. A. K. Sharma \u00b7 CSE Mentor',
    color: 'var(--olive)',
    colorBg: 'var(--olive-bg)',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    key: 'warden',
    label: 'Warden',
    desc: 'Review and approve student outpass requests.',
    user: 'Dr. A. K. Sharma \u00b7 Bhaskar Hostel',
    color: 'var(--forest)',
    colorBg: 'var(--forest-bg)',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
        <path d="M12 2L3 7v10l9 5 9-5V7l-9-5z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    key: 'hod',
    label: 'HOD',
    desc: 'Departmental oversight of outpass and leave records.',
    user: 'Prof. A. Bordoloi \u00b7 HOD, CSE',
    color: 'var(--plum)',
    colorBg: 'var(--plum-bg)',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
        <path d="M12 2L3 7v10l9 5 9-5V7l-9-5z" />
      </svg>
    ),
  },
];

export default function SignIn() {
  const navigate = useNavigate();

  return (
    <div className="signin">
      {/* Brand */}
      <div className="signin__brand">
        <div className="signin__logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 7v10l9 5 9-5V7l-9-5z" fill="#fff" opacity="0.9"/>
            <path d="M12 2L3 7l9 5 9-5-9-5z" fill="#fff"/>
            <circle cx="12" cy="12" r="3" fill="var(--terracotta)" opacity="0.8"/>
          </svg>
        </div>
        <h1 className="signin__title">HostelOut</h1>
      </div>
      <p className="signin__subtitle">Digital Outpass &amp; Leave Register &middot; Tezpur University</p>

      {/* Sign-in label */}
      <p className="signin__label">SIGN IN AS</p>

      {/* Role cards */}
      <div className="signin__roles">
        {roles.map((r) => (
          <button key={r.key} className="signin__card" onClick={() => navigate(`/${r.key}`)}>
            <div className="signin__card-icon" style={{ background: r.color }}>
              {r.icon}
            </div>
            <h3 className="signin__card-title">{r.label}</h3>
            <p className="signin__card-desc">{r.desc}</p>
            <div className="signin__card-user">
              <span className="signin__card-dot" style={{ background: 'var(--olive)' }} />
              {r.user}
            </div>
          </button>
        ))}
      </div>

      {/* Security Desk bar */}
      <button className="signin__security" onClick={() => navigate('/security')}>
        <div className="signin__security-left">
          <div className="signin__security-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--brown-800)" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
          </div>
          <div>
            <div className="signin__security-title">Security Desk</div>
            <div className="signin__security-desc">Gate log &mdash; record exits and returns against approved passes</div>
          </div>
        </div>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--brown-300)" strokeWidth="2">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>

      <p className="signin__footer">Select your role and sign in with your university ID to continue.</p>
    </div>
  );
}
