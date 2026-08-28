import React from "react";
import "../styles/cameras.css";

function Cameras() {
  const cameras = [
    {
      id: "CAM-01",
      name: "Main Gate Camera",
      location: "Main Entry Gate",
      status: "Online",
      detections: 42,
      type: "PTZ Camera",
    },
    {
      id: "CAM-02",
      name: "Perimeter Zone B",
      location: "Border Perimeter",
      status: "Online",
      detections: 68,
      type: "Fixed Camera",
    },
    {
      id: "CAM-04",
      name: "Watch Tower 02",
      location: "Watch Tower",
      status: "Online",
      detections: 31,
      type: "PTZ Camera",
    },
    {
      id: "CAM-07",
      name: "Border Gate Alpha",
      location: "Checkpoint Alpha",
      status: "Online",
      detections: 52,
      type: "ANPR Camera",
    },
    {
      id: "CAM-11",
      name: "Checkpoint North",
      location: "North Checkpoint",
      status: "Offline",
      detections: 34,
      type: "Face Recognition",
    },
    {
      id: "CAM-14",
      name: "Perimeter Zone C",
      location: "Border Perimeter",
      status: "Online",
      detections: 27,
      type: "Fixed Camera",
    },
  ];

  const [selectedCamera, setSelectedCamera] = React.useState(null);

  return (
    <div className="cameras-page">

      <div className="cameras-header">
        <div>
          <h1>Cameras</h1>
          <p>Monitor and manage connected surveillance cameras</p>
        </div>

        <button className="add-camera-btn">
          + Add Camera
        </button>
      </div>

      <div className="camera-stats">

        <div className="camera-stat">
          <span>TOTAL CAMERAS</span>
          <strong>24</strong>
          <small>Registered devices</small>
        </div>

        <div className="camera-stat online">
          <span>ONLINE</span>
          <strong>22</strong>
          <small>Currently active</small>
        </div>

        <div className="camera-stat offline">
          <span>OFFLINE</span>
          <strong>02</strong>
          <small>Requires attention</small>
        </div>

        <div className="camera-stat">
          <span>AI ENABLED</span>
          <strong>24</strong>
          <small>AI analytics active</small>
        </div>

      </div>

      <div className="cameras-panel">

        <div className="cameras-panel-header">
          <div>
            <h2>Connected Cameras</h2>
            <p>Live status and AI detection information</p>
          </div>

          <div className="camera-filters">
            <button className="camera-filter-active">All</button>
            <button>Online</button>
            <button>Offline</button>
          </div>
        </div>

        <div className="camera-list">

          {cameras.map((camera) => (
            <div className="camera-card" key={camera.id}>

              <div className="camera-preview">

                <div className="camera-preview-content">
                  <span className="camera-live-dot"></span>

                  <span className="camera-preview-text">
                    LIVE FEED
                  </span>

                  <strong>{camera.id}</strong>
                </div>

                <span className="camera-type">
                  {camera.type}
                </span>

              </div>

              <div className="camera-info">

                <div className="camera-info-top">
                  <div>
                    <h3>{camera.name}</h3>
                    <p>{camera.location}</p>
                  </div>

                  <span
                    className={`camera-status ${camera.status.toLowerCase()}`}
                  >
                    ● {camera.status}
                  </span>
                </div>

                <div className="camera-details">

                  <div>
                    <span>Camera ID</span>
                    <strong>{camera.id}</strong>
                  </div>

                  <div>
                    <span>Detections</span>
                    <strong>{camera.detections}</strong>
                  </div>

                  <button
                    className="view-camera-btn"
                    onClick={() => setSelectedCamera(camera)}
                  >
                    View Camera
                  </button>

                </div>

              </div>

            </div>
          ))}

        </div>

      </div>

      {/* CAMERA MODAL */}

      {selectedCamera && (
        <div
          className="camera-modal-overlay"
          onClick={() => setSelectedCamera(null)}
        >

          <div
            className="camera-modal"
            onClick={(e) => e.stopPropagation()}
          >

            <div className="camera-modal-header">
              <div>
                <h2>{selectedCamera.name}</h2>
                <p>
                  {selectedCamera.id} • {selectedCamera.location}
                </p>
              </div>

              <button
                className="camera-close"
                onClick={() => setSelectedCamera(null)}
              >
                ✕
              </button>
            </div>

            <div className="camera-live-view">

              <div className="camera-live-content">
                <span className="camera-live-dot"></span>
                <span>LIVE CAMERA FEED</span>
                <strong>{selectedCamera.id}</strong>
              </div>

              <div className="camera-live-label">
                ● LIVE
              </div>

            </div>

            <div className="camera-modal-details">

              <div>
                <span>STATUS</span>
                <strong>{selectedCamera.status}</strong>
              </div>

              <div>
                <span>CAMERA TYPE</span>
                <strong>{selectedCamera.type}</strong>
              </div>

              <div>
                <span>AI DETECTIONS</span>
                <strong>{selectedCamera.detections}</strong>
              </div>

            </div>

          </div>

        </div>
      )}

    </div>
  );
}

export default Cameras;

