
import "../styles/analytics.css";

function Analytics() {
  const detectionData = [
    { name: "Intrusion", value: 68, count: 68 },
    { name: "Vehicle", value: 52, count: 52 },
    { name: "Face Match", value: 34, count: 34 },
    { name: "Object", value: 27, count: 27 },
  ];

  const cameras = [
    { camera: "CAM-01", location: "Main Gate", detections: 42 },
    { camera: "CAM-02", location: "Perimeter Zone B", detections: 68 },
    { camera: "CAM-04", location: "Watch Tower 02", detections: 31 },
    { camera: "CAM-07", location: "Border Gate Alpha", detections: 52 },
    { camera: "CAM-11", location: "Checkpoint North", detections: 34 },
  ];

  return (
    <div className="analytics-page">

      {/* HEADER */}
      <div className="analytics-header">
        <div>
          <h1>Analytics</h1>
          <p>
            AI-powered surveillance insights and detection analytics
          </p>
        </div>

        <button className="analytics-period">
          Last 7 Days ▾
        </button>
      </div>

      {/* STAT CARDS */}
      <div className="analytics-stats">

        <div className="analytics-card">
          <span>Total Detections</span>
          <strong>181</strong>
          <small>↑ 12.5% from last week</small>
        </div>

        <div className="analytics-card">
          <span>Intrusion Events</span>
          <strong>68</strong>
          <small>↑ 8.2% from last week</small>
        </div>

        <div className="analytics-card">
          <span>Vehicle Detections</span>
          <strong>52</strong>
          <small>↑ 5.4% from last week</small>
        </div>

        <div className="analytics-card">
          <span>Face Matches</span>
          <strong>34</strong>
          <small>3 watchlist matches</small>
        </div>

      </div>

      {/* MAIN GRID */}
      <div className="analytics-grid">

        {/* ACTIVITY CHART */}
        <div className="analytics-panel activity-panel">

          <div className="panel-title">
            <div>
              <h2>Detection Activity</h2>
              <p>AI detections recorded over the last 7 days</p>
            </div>
          </div>

          <div className="chart">
            <div className="chart-y">
              <span>80</span>
              <span>60</span>
              <span>40</span>
              <span>20</span>
              <span>0</span>
            </div>

            <div className="chart-area">

              <div className="chart-lines">
                <div></div>
                <div></div>
                <div></div>
                <div></div>
                <div></div>
              </div>

              <div className="bars">
                <div className="bar-wrap">
                  <div className="bar" style={{ height: "48%" }}></div>
                  <span>Mon</span>
                </div>

                <div className="bar-wrap">
                  <div className="bar" style={{ height: "63%" }}></div>
                  <span>Tue</span>
                </div>

                <div className="bar-wrap">
                  <div className="bar" style={{ height: "42%" }}></div>
                  <span>Wed</span>
                </div>

                <div className="bar-wrap">
                  <div className="bar" style={{ height: "76%" }}></div>
                  <span>Thu</span>
                </div>

                <div className="bar-wrap">
                  <div className="bar" style={{ height: "58%" }}></div>
                  <span>Fri</span>
                </div>

                <div className="bar-wrap">
                  <div className="bar" style={{ height: "84%" }}></div>
                  <span>Sat</span>
                </div>

                <div className="bar-wrap">
                  <div className="bar" style={{ height: "67%" }}></div>
                  <span>Sun</span>
                </div>
              </div>

            </div>
          </div>

        </div>

        {/* DETECTION TYPES */}
        <div className="analytics-panel">

          <div className="panel-title">
            <div>
              <h2>Detection Types</h2>
              <p>Distribution of AI detections</p>
            </div>
          </div>

          <div className="detection-list">

            {detectionData.map((item) => (
              <div className="detection-item" key={item.name}>

                <div className="detection-info">
                  <span>{item.name}</span>
                  <strong>{item.count}</strong>
                </div>

                <div className="progress">
                  <div
                    className="progress-fill"
                    style={{ width: `${item.value}%` }}
                  ></div>
                </div>

              </div>
            ))}

          </div>

        </div>

      </div>

      {/* CAMERA TABLE */}
      <div className="analytics-panel camera-panel">

        <div className="panel-title">
          <div>
            <h2>Camera Performance</h2>
            <p>Detection activity by surveillance camera</p>
          </div>
        </div>

        <div className="camera-table-header">
          <span>CAMERA</span>
          <span>LOCATION</span>
          <span>DETECTIONS</span>
          <span>STATUS</span>
        </div>

        {cameras.map((camera) => (
          <div className="camera-row" key={camera.camera}>

            <strong>{camera.camera}</strong>

            <span>{camera.location}</span>

            <span>{camera.detections}</span>

            <span className="camera-status">
              ● Online
            </span>

          </div>
        ))}

      </div>

    </div>
  );
}

export default Analytics;

