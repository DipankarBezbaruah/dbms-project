import { useNavigate, useLocation } from 'react-router-dom';
import './Sidebar.css';

export default function Sidebar({ role, userName, userDetail, navItems, basePath }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar__brand" onClick={() => navigate('/')}>
        <div className="sidebar__logo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 7v10l9 5 9-5V7l-9-5z" fill="#fff" opacity="0.9"/>
            <path d="M12 2L3 7l9 5 9-5-9-5z" fill="#fff"/>
            <circle cx="12" cy="12" r="3" fill="var(--terracotta)" opacity="0.8"/>
          </svg>
        </div>
        <div>
          <div className="sidebar__brand-name">HostelOut</div>
          <div className="sidebar__brand-sub">Digital Outpass System</div>
        </div>
      </div>

      {/* User info */}
      <div className="sidebar__user">
        <div className="sidebar__user-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <div className="sidebar__user-info">
          <div className="sidebar__user-role">{role}</div>
          <div className="sidebar__user-name">{userName}</div>
        </div>
        <svg className="sidebar__user-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>

      {/* Nav */}
      <nav className="sidebar__nav">
        {navItems.map((item) => {
          const fullPath = `${basePath}${item.path}`;
          const isActive =
            location.pathname === fullPath ||
            (item.path === '' && location.pathname === basePath) ||
            (item.path === '' && location.pathname === basePath + '/');
          return (
            <button
              key={item.path}
              className={`sidebar__nav-item ${isActive ? 'sidebar__nav-item--active' : ''}`}
              onClick={() => navigate(fullPath)}
            >
              <span className="sidebar__nav-icon">{item.icon}</span>
              <span className="sidebar__nav-label">{item.label}</span>
              {item.badge != null && item.badge > 0 && (
                <span className="sidebar__nav-badge">{item.badge}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Sign out */}
      <button className="sidebar__signout" onClick={() => navigate('/')}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
          <polyline points="16 17 21 12 16 7"/>
          <line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        Sign Out
      </button>
    </aside>
  );
}
