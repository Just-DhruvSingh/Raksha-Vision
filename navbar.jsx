function Navbar() {
  return (
    <header className="navbar">

      <div className="navbar-left">
        <div>
          <h1>Surveillance Command Center</h1>
          <p>Real-time border security intelligence</p>
        </div>
      </div>

      <div className="navbar-right">

        <div className="search-box">
          <span>⌕</span>
          <input
            type="text"
            placeholder="Search cameras, alerts..."
          />
        </div>

        <button className="notification-button">
          🔔
          <span>3</span>
        </button>

        <div className="profile">
          <div className="profile-avatar">
            SO
          </div>

          <div className="profile-info">
            <strong>Operator</strong>
            <small>Security Control</small>
          </div>
        </div>

      </div>

    </header>
  );
}

export default Navbar;