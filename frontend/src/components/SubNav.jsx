import { useNavigate, useLocation } from 'react-router-dom';
import './SubNav.css';

export default function SubNav({ items, basePath }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <nav className="subnav">
      {items.map((item) => {
        const fullPath = `${basePath}${item.path}`;
        const isActive =
          location.pathname === fullPath ||
          (item.path === '' && (location.pathname === basePath || location.pathname === basePath + '/'));
        return (
          <button
            key={item.path}
            className={`subnav__item ${isActive ? 'subnav__item--active' : ''}`}
            onClick={() => navigate(fullPath)}
          >
            <span className="subnav__icon">{item.icon}</span>
            <span className="subnav__label">{item.label}</span>
            {item.badge != null && item.badge > 0 && (
              <span className="subnav__badge">{item.badge}</span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
