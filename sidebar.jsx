import { NavLink } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">

      {/* LOGO */}
      <div className="sidebar-logo">
        <div className="logo-icon">🛡</div>

        <div>
          <h2>RakshaVision</h2>
          <span>AI SURVEILLANCE</span>
        </div>
      </div>

      {/* COMMAND CENTER */}
      <div className="sidebar-section">
        <p className="section-title">COMMAND CENTER</p>

        <NavLink
          to="/"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <span>▦</span>
          Dashboard
        </NavLink>

        <NavLink
          to="/live"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <span>◉</span>
          Live Monitoring
        </NavLink>

        <NavLink
          to="/alerts"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <span>⚠</span>
          Alerts
          <span className="badge">3</span>
        </NavLink>

        <NavLink
          to="/incidents"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <span>◈</span>
          Incidents
        </NavLink>
      </div>

      {/* INTELLIGENCE */}
      <div className="sidebar-section">
        <p className="section-title">INTELLIGENCE</p>

        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <span>▥</span>
          Analytics
        </NavLink>

        <NavLink
          to="/cameras"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <span>▣</span>
          Cameras
        </NavLink>
      </div>

      {/* SYSTEM */}
      <div className="sidebar-section">
        <p className="section-title">SYSTEM</p>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <span>⚙</span>
          Settings
        </NavLink>
      </div>

      {/* BOTTOM */}
      <div className="sidebar-bottom">

        <div className="system-status">
          <span className="status-dot"></span>

          <div>
            <strong>System Operational</strong>
            <small>AI Engine Online</small>
          </div>
        </div>

        <div className="operator">
          <div className="operator-avatar">SO</div>

          <div>
            <strong>Security Operator</strong>
            <small>Control Room</small>
          </div>
        </div>

      </div>

    </aside>
  );
}

export default Sidebar;