function LiveMonitoring() {
  const cameras = [
    {
      id: "CAM-01",
      location: "Border Gate Alpha",
      status: "LIVE",
      threat: "Normal",
    },
    {
      id: "CAM-02",
      location: "Perimeter Zone B",
      status: "LIVE",
      threat: "Alert",
    },
    {
      id: "CAM-03",
      location: "Border Road 04",
      status: "LIVE",
      threat: "Normal",
    },
    {
      id: "CAM-04",
      location: "Watch Tower 02",
      status: "LIVE",
      threat: "Normal",
    },
  ];

  return (
    <div className="live-page">

      {/* HEADER */}
      <div className="live-header">
        <div>
          <h1>Live Monitoring</h1>
          <p>Real-time AI powered border surveillance</p>
        </div>

        <div className="live-status">
          <span className="status-dot"></span>
          SYSTEM ONLINE
        </div>
      </div>

      {/* STATS */}
      <div className="monitor-stats">

        <div className="monitor-card">
          <span>ACTIVE CAMERAS</span>
          <strong>24</strong>
          <small>All systems operational</small>
        </div>

        <div className="monitor-card">
          <span>AI DETECTIONS</span>
          <strong>137</strong>
          <small>Last 24 hours</small>
        </div>

        <div className="monitor-card alert-card">
          <span>ACTIVE ALERTS</span>
          <strong>03</strong>
          <small>Requires attention</small>
        </div>

        <div className="monitor-card">
          <span>THREATS BLOCKED</span>
          <strong>18</strong>
          <small>Today</small>
        </div>

      </div>

      {/* CAMERA GRID */}
      <div className="camera-section">

        <div className="section-heading">
          <div>
            <h2>Camera Feeds</h2>
            <p>Live surveillance across deployed locations</p>
          </div>

          <button className="refresh-btn">↻ Refresh</button>
        </div>

        <div className="camera-grid">

          {cameras.map((camera) => (
            <div className="camera-card" key={camera.id}>

              <div className="camera-feed">

                <div className="scan-line"></div>

                <div className="camera-overlay">
                  <span className="live-badge">● LIVE</span>
                  <span>{camera.id}</span>
                </div>

                <div className="camera-center">
                  <div className="camera-icon">◉</div>
                  <span>AI CAMERA FEED</span>
                </div>

                <div className="camera-bottom">
                  <span>REC ●</span>
                  <span>1080p</span>
                </div>

              </div>

              <div className="camera-info">

                <div>
                  <h3>{camera.location}</h3>
                  <p>{camera.id}</p>
                </div>

                <div
                  className={
                    camera.threat === "Alert"
                      ? "threat alert"
                      : "threat"
                  }
                >
                  {camera.threat}
                </div>

              </div>

            </div>
          ))}

        </div>
      </div>

      {/* AI DETECTION BAR */}
      <div className="ai-panel">

        <div>
          <h2>AI Detection Engine</h2>
          <p>
            Facial recognition • ANPR • Intrusion detection • Object tracking
          </p>
        </div>

        <div className="engine-status">
          <span className="status-dot"></span>
          AI ENGINE ONLINE
        </div>

      </div>

    </div>
  );
}

export default LiveMonitoring;