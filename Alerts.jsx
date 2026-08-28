
import { useState } from "react";
import "../styles/alerts.css";

function Alerts() {
  const [alerts, setAlerts] = useState([
    {
      id: "ALT-001",
      type: "Intrusion Detected",
      camera: "CAM-02",
      location: "Perimeter Zone B",
      time: "2 min ago",
      severity: "CRITICAL",
      description:
        "Unauthorized movement detected in restricted border area.",
      status: "ACTIVE",
    },
    {
      id: "ALT-002",
      type: "Unknown Vehicle",
      camera: "CAM-07",
      location: "Border Gate Alpha",
      time: "14 min ago",
      severity: "HIGH",
      description:
        "Vehicle detected with an unrecognized license plate.",
      status: "ACTIVE",
    },
    {
      id: "ALT-003",
      type: "Face Recognition Alert",
      camera: "CAM-11",
      location: "Checkpoint North",
      time: "32 min ago",
      severity: "HIGH",
      description:
        "Face matched with a watchlist entry.",
      status: "ACTIVE",
    },
    {
      id: "ALT-004",
      type: "Object Detected",
      camera: "CAM-04",
      location: "Watch Tower 02",
      time: "1 hr ago",
      severity: "MEDIUM",
      description:
        "Suspicious object detected near surveillance perimeter.",
      status: "ACTIVE",
    },
    {
      id: "ALT-005",
      type: "Unusual Movement",
      camera: "CAM-03",
      location: "Border Road 04",
      time: "2 hrs ago",
      severity: "LOW",
      description:
        "Unusual movement pattern detected by AI engine.",
      status: "ACTIVE",
    },
  ]);

  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  const acknowledgeAlert = (id) => {
    setAlerts((currentAlerts) =>
      currentAlerts.map((alert) =>
        alert.id === id
          ? { ...alert, status: "ACKNOWLEDGED" }
          : alert
      )
    );
  };

  const filteredAlerts = alerts.filter((alert) => {
    const matchesFilter =
      filter === "ALL" || alert.severity === filter;

    const searchText = search.toLowerCase();

    const matchesSearch =
      alert.type.toLowerCase().includes(searchText) ||
      alert.location.toLowerCase().includes(searchText) ||
      alert.camera.toLowerCase().includes(searchText) ||
      alert.id.toLowerCase().includes(searchText);

    return matchesFilter && matchesSearch;
  });

  const activeAlerts = alerts.filter(
    (alert) => alert.status === "ACTIVE"
  ).length;

  return (
    <div className="alerts-page">

      {/* HEADER */}
      <div className="alerts-header">

        <div>
          <h1>Security Alerts</h1>
          <p>
            AI-generated alerts requiring monitoring and response
          </p>
        </div>

        <div className="alert-summary">
          <span className="alert-summary-dot"></span>
          {String(activeAlerts).padStart(2, "0")} ACTIVE ALERTS
        </div>

      </div>

      {/* STATS */}
      <div className="alert-stats">

        <div className="alert-stat">
          <span>ACTIVE</span>
          <strong>{String(activeAlerts).padStart(2, "0")}</strong>
          <small>Requires attention</small>
        </div>

        <div className="alert-stat critical-stat">
          <span>CRITICAL</span>
          <strong>
            {
              alerts.filter(
                (alert) =>
                  alert.severity === "CRITICAL" &&
                  alert.status === "ACTIVE"
              ).length
            }
          </strong>
          <small>Immediate response</small>
        </div>

        <div className="alert-stat">
          <span>HIGH PRIORITY</span>
          <strong>
            {
              alerts.filter(
                (alert) =>
                  alert.severity === "HIGH" &&
                  alert.status === "ACTIVE"
              ).length
            }
          </strong>
          <small>Investigate soon</small>
        </div>

        <div className="alert-stat">
          <span>RESOLVED TODAY</span>
          <strong>18</strong>
          <small>Successfully handled</small>
        </div>

      </div>

      {/* ALERT PANEL */}
      <div className="alerts-panel">

        <div className="alerts-panel-header">

          <div>
            <h2>Recent Alerts</h2>
            <p>
              Latest events detected by the AI surveillance engine
            </p>
          </div>

          {/* SEARCH */}
          <input
            type="text"
            className="alert-search"
            placeholder="Search alerts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

        </div>

        {/* FILTERS */}
        <div className="alert-filter-bar">

          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map(
            (level) => (
              <button
                key={level}
                className={
                  filter === level
                    ? "alert-filter-active"
                    : ""
                }
                onClick={() => setFilter(level)}
              >
                {level}
              </button>
            )
          )}

        </div>

        {/* ALERT LIST */}
        <div className="alerts-list">

          {filteredAlerts.length === 0 ? (
            <div className="no-alerts">
              No alerts found.
            </div>
          ) : (
            filteredAlerts.map((alert) => (

              <div
                className={`alert-row ${
                  alert.status === "ACKNOWLEDGED"
                    ? "alert-acknowledged"
                    : ""
                }`}
                key={alert.id}
              >

                {/* ICON */}
                <div className="alert-type-icon">
                  ⚠
                </div>

                {/* MAIN */}
                <div className="alert-main">

                  <div className="alert-title-row">

                    <h3>{alert.type}</h3>

                    <span
                      className={`alert-severity ${alert.severity.toLowerCase()}`}
                    >
                      {alert.severity}
                    </span>

                    {alert.status === "ACKNOWLEDGED" && (
                      <span className="acknowledged-badge">
                        ACKNOWLEDGED
                      </span>
                    )}

                  </div>

                  <p>{alert.description}</p>

                  <div className="alert-meta">
                    <span>📹 {alert.camera}</span>
                    <span>📍 {alert.location}</span>
                    <span>◷ {alert.time}</span>
                  </div>

                </div>

                {/* ID + ACTION */}
                <div className="alert-actions">

                  <span className="alert-id">
                    {alert.id}
                  </span>

                  {alert.status === "ACTIVE" && (
                    <button
                      className="acknowledge-btn"
                      onClick={() =>
                        acknowledgeAlert(alert.id)
                      }
                    >
                      Acknowledge
                    </button>
                  )}

                </div>

              </div>

            ))
          )}

        </div>

      </div>

    </div>
  );
}

export default Alerts;

