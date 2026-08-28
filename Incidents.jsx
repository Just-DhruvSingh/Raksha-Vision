import "../styles/incidents.css";
function Incidents() {
  const incidents = [
    {
      id: "INC-001",
      title: "Perimeter Intrusion",
      location: "Perimeter Zone B",
      camera: "CAM-02",
      time: "Today, 00:42",
      severity: "CRITICAL",
      status: "Investigating",
      description: "Unauthorized movement detected near restricted border perimeter.",
    },
    {
      id: "INC-002",
      title: "Unknown Vehicle Detected",
      location: "Border Gate Alpha",
      camera: "CAM-07",
      time: "Today, 00:28",
      severity: "HIGH",
      status: "Under Review",
      description: "Vehicle with an unrecognized number plate detected at checkpoint.",
    },
    {
      id: "INC-003",
      title: "Watchlist Face Match",
      location: "Checkpoint North",
      camera: "CAM-11",
      time: "Yesterday, 23:56",
      severity: "HIGH",
      status: "Investigating",
      description: "Facial recognition system generated a watchlist match.",
    },
    {
      id: "INC-004",
      title: "Suspicious Object",
      location: "Watch Tower 02",
      camera: "CAM-04",
      time: "Yesterday, 22:14",
      severity: "MEDIUM",
      status: "Resolved",
      description: "AI object detection identified an unattended object.",
    },
  ];

  return (
    <div className="incidents-page">

      {/* HEADER */}
      <div className="incidents-header">
        <div>
          <h1>Security Incidents</h1>
          <p>Track, investigate and manage detected security incidents</p>
        </div>

        <button className="incident-btn">
          + Create Incident
        </button>
      </div>

      {/* STATS */}
      <div className="incident-stats">

        <div className="incident-stat">
          <span>TOTAL INCIDENTS</span>
          <strong>24</strong>
          <small>Last 30 days</small>
        </div>

        <div className="incident-stat critical-incident">
          <span>CRITICAL</span>
          <strong>02</strong>
          <small>Immediate attention</small>
        </div>

        <div className="incident-stat">
          <span>UNDER INVESTIGATION</span>
          <strong>07</strong>
          <small>Currently active</small>
        </div>

        <div className="incident-stat resolved-incident">
          <span>RESOLVED</span>
          <strong>15</strong>
          <small>Successfully closed</small>
        </div>

      </div>

      {/* INCIDENT PANEL */}
      <div className="incidents-panel">

        <div className="incidents-panel-header">
          <div>
            <h2>Recent Incidents</h2>
            <p>Security events generated from AI detections and alerts</p>
          </div>

          <div className="incident-filters">
            <button className="filter-active">All</button>
            <button>Active</button>
            <button>Resolved</button>
          </div>
        </div>

        {/* TABLE HEADER */}
        <div className="incident-table-header">
          <span>INCIDENT</span>
          <span>LOCATION</span>
          <span>SEVERITY</span>
          <span>STATUS</span>
          <span>TIME</span>
        </div>

        {/* INCIDENT ROWS */}
        <div className="incident-list">

          {incidents.map((incident) => (

            <div className="incident-row" key={incident.id}>

              <div className="incident-title">

                <div className="incident-icon">
                  ⚠
                </div>

                <div>
                  <h3>{incident.title}</h3>
                  <p>{incident.id} • {incident.camera}</p>
                </div>

              </div>

              <div className="incident-location">
                📍 {incident.location}
              </div>

              <div>
                <span
                  className={`incident-severity ${incident.severity.toLowerCase()}`}
                >
                  {incident.severity}
                </span>
              </div>

              <div>
                <span
                  className={`incident-status ${incident.status
                    .toLowerCase()
                    .replace(" ", "-")}`}
                >
                  {incident.status}
                </span>
              </div>

              <div className="incident-time">
                {incident.time}
              </div>

            </div>

          ))}

        </div>

      </div>

    </div>
  );
}

export default Incidents;