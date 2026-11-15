import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../AuthContext';
import './SecurityDesk.css';

export default function SecurityDesk() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const staffId = user?.staff_id;

  const [outpassId, setOutpassId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleAction = async (action) => {
    if (!outpassId.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      let res;
      if (action === 'exit') {
        res = await api.logExit(Number(outpassId), staffId);
      } else {
        res = await api.logReturn(Number(outpassId), staffId);
      }
      setResult({
        type: 'success',
        text: action === 'exit'
          ? `Exit logged at ${new Date(res.actual_exit_time).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}`
          : `Return logged at ${new Date(res.actual_return_time).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}`,
      });
    } catch (e) {
      setResult({ type: 'error', text: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="security">
      {/* Header */}
      <div className="security__header">
        <button className="security__back" onClick={handleSignOut}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Sign Out
        </button>
        <div className="security__brand">
          <div className="security__logo">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L3 7v10l9 5 9-5V7l-9-5z" fill="#fff" opacity="0.9"/>
              <path d="M12 2L3 7l9 5 9-5-9-5z" fill="#fff"/>
              <circle cx="12" cy="12" r="3" fill="var(--terracotta)" opacity="0.8"/>
            </svg>
          </div>
          <span className="security__brand-name">HostelOut</span>
          <span className="security__brand-sub">&middot; Security Desk &middot; {user?.name || 'Guard'}</span>
        </div>
      </div>

      {/* Main panel */}
      <div className="security__panel">
        <div className="security__icon-badge">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0110 0v4"/>
          </svg>
        </div>
        <h1 className="security__title">Gate Log</h1>
        <p className="security__subtitle">Record student exits and returns against approved passes.</p>

        <div className="security__input-group">
          <label className="security__input-label">Outpass ID</label>
          <input
            className="security__input"
            type="number"
            placeholder="Enter outpass ID (e.g. 2)"
            value={outpassId}
            onChange={(e) => { setOutpassId(e.target.value); setResult(null); }}
            min="1"
          />
        </div>

        {result && (
          <div className={`security__alert security__alert--${result.type}`}>
            {result.type === 'success' ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            )}
            {result.text}
          </div>
        )}

        <div className="security__buttons">
          <button
            className="security__btn security__btn--exit"
            onClick={() => handleAction('exit')}
            disabled={loading || !outpassId.trim()}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            {loading ? 'Processing...' : 'Log Exit'}
          </button>
          <button
            className="security__btn security__btn--return"
            onClick={() => handleAction('return')}
            disabled={loading || !outpassId.trim()}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4"/>
              <polyline points="10 17 15 12 10 7"/>
              <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
            {loading ? 'Processing...' : 'Log Return'}
          </button>
        </div>

        <p className="security__help">
          Enter the outpass ID printed on the student's pass. Only approved outpasses can be logged.
        </p>
      </div>
    </div>
  );
}
