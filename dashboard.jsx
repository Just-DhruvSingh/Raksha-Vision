function Dashboard() {
  return (
    <div className="dashboard-page">

      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>Surveillance Dashboard</h1>
          <p>
            Real-time overview of border surveillance operations.
          </p>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          System Operational
        </div>
      </div>


      {/* Statistics */}
      <div className="stats-grid">

        <div className="stat-card">
          <div className="stat-icon">📹</div>
          <div>
            <p>Total Cameras</p>
            <h2>48</h2>
            <span className="positive">45 online</span>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">⚠️</div>
          <div>
            <p>Active Alerts</p>
            <h2>03</h2>
            <span className="warning">Requires attention</span>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">👤</div>
          <div>
            <p>People Detected</p>
            <h2>127</h2>
            <span>Today</span>
          </div>
        </div>


        <div className="stat-card">
          <div className="stat-icon">🚗</div>
          <div>
            <p>Vehicles Detected</p>
            <h2>86</h2>
            <span>Today</span>
          </div>
        </div>

      </div>


      {/* Main Dashboard Grid */}
      <div className="dashboard-grid">

        {/* Activity */}
        <div className="dashboard-card activity-card">

          <div className="card-header">
            <div>
              <h3>Surveillance Activity</h3>
              <p>Detection activity over the last 24 hours</p>
            </div>

            <select>
              <option>Last 24 hours</option>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
            </select>
          </div>

          <div className="activity-chart">

            <div className="chart-bars">
              <div style={{ height: "35%" }}></div>
              <div style={{ height: "55%" }}></div>
              <div style={{ height: "40%" }}></div>
              <div style={{ height: "70%" }}></div>
              <div style={{ height: "50%" }}></div>
              <div style={{ height: "85%" }}></div>
              <div style={{ height: "65%" }}></div>
              <div style={{ height: "90%" }}></div>
              <div style={{ height: "60%" }}></div>
              <div style={{ height: "75%" }}></div>
              <div style={{ height: "45%" }}></div>
              <div style={{ height: "80%" }}></div>
            </div>

          </div>

        </div>


        {/* Camera Status */}
        <div className="dashboard-card">

          <div className="card-header">
            <div>
              <h3>Camera Status</h3>
              <p>Current infrastructure health</p>
            </div>
          </div>

          <div className="camera-status-list">

            <div className="camera-status-item">
              <span className="status-dot online"></span>
              <span>Online</span>
              <strong>45</strong>
            </div>

            <div className="camera-status-item">
              <span className="status-dot warning-dot"></span>
              <span>Warning</span>
              <strong>2</strong>
            </div>

            <div className="camera-status-item">
              <span className="status-dot offline"></span>
              <span>Offline</span>
              <strong>1</strong>
            </div>

          </div>

        </div>

      </div>


      {/* Recent Alerts */}
      <div className="dashboard-card alerts-card">

        <div className="card-header">
          <div>
            <h3>Recent Alerts</h3>
            <p>Latest security events detected by AI</p>
          </div>

          <button className="view-all">
            View all
          </button>
        </div>


        <div className="alert-list">

          <div className="alert-item critical">

            <div className="alert-icon">
              🚨
            </div>

            <div className="alert-content">
              <h4>Virtual Fence Breach</h4>
              <p>Camera CAM-07 • 2 min ago</p>
            </div>

            <span className="severity critical-label">
              Critical
            </span>

          </div>


          <div className="alert-item warning-alert">

            <div className="alert-icon">
              🚗
            </div>

            <div className="alert-content">
              <h4>Unknown Vehicle Detected</h4>
              <p>Camera CAM-12 • 8 min ago</p>
            </div>

            <span className="severity warning-label">
              Warning
            </span>

          </div>


          <div className="alert-item">

            <div className="alert-icon">
              🌙
            </div>

            <div className="alert-content">
              <h4>Night Movement Detected</h4>
              <p>Camera CAM-03 • 14 min ago</p>
            </div>

            <span className="severity info-label">
              Info
            </span>

          </div>

        </div>

      </div>

    </div>
  );
}

export default Dashboard;