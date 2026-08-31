import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import './SignIn.css';

export default function SignIn() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const userData = await login(email, password);
      // Navigate to the dashboard matching the user's role
      navigate(`/${userData.role.toLowerCase()}`);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

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
      <p className="signin__subtitle">Digital Outpass &amp; Leave Register</p>

      {/* Login form */}
      <form className="signin__form" onSubmit={handleSubmit}>
        <p className="signin__label">SIGN IN</p>

        <div className="signin__field">
          <label className="signin__field-label" htmlFor="signin-email">Email</label>
          <input
            id="signin-email"
            className="signin__input"
            type="email"
            placeholder="your.id@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className="signin__field">
          <label className="signin__field-label" htmlFor="signin-password">Password</label>
          <input
            id="signin-password"
            className="signin__input"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {error && <div className="signin__error">{error}</div>}

        <button className="signin__submit" type="submit" disabled={loading}>
          {loading ? (
            <>
              <span className="signin__spinner" />
              Signing in...
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4"/>
                <polyline points="10 17 15 12 10 7"/>
                <line x1="15" y1="12" x2="3" y2="12"/>
              </svg>
              Sign In
            </>
          )}
        </button>
      </form>

      {/* Role info hint */}
      <div className="signin__roles-hint">
        <p className="signin__hint-title">Available roles</p>
        <div className="signin__hint-grid">
          <div className="signin__hint-chip" style={{ borderColor: 'var(--terracotta)' }}>
            <span className="signin__hint-dot" style={{ background: 'var(--terracotta)' }} />
            Student
          </div>
          <div className="signin__hint-chip" style={{ borderColor: 'var(--olive)' }}>
            <span className="signin__hint-dot" style={{ background: 'var(--olive)' }} />
            Mentor
          </div>
          <div className="signin__hint-chip" style={{ borderColor: 'var(--forest)' }}>
            <span className="signin__hint-dot" style={{ background: 'var(--forest)' }} />
            Warden
          </div>
          <div className="signin__hint-chip" style={{ borderColor: 'var(--plum)' }}>
            <span className="signin__hint-dot" style={{ background: 'var(--plum)' }} />
            HOD
          </div>
          <div className="signin__hint-chip" style={{ borderColor: 'var(--brown-400)' }}>
            <span className="signin__hint-dot" style={{ background: 'var(--brown-400)' }} />
            Security
          </div>
        </div>
      </div>

      <p className="signin__footer">Sign in with your registered email. Your role is determined automatically.</p>
    </div>
  );
}
