import "../styles/settings.css";
import { useState } from "react";

function Settings() {
  const [darkMode, setDarkMode] = useState(true);
  const [soundAlerts, setSoundAlerts] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [twoFactor, setTwoFactor] = useState(false);

  return (
    <div className="settings-page">

      <div className="settings-header">
        <div>
          <h1>Settings</h1>
          <p>Configure your RakshaVision AI system preferences</p>
        </div>
      </div>

      {/* Profile */}
      <section className="settings-section">
        <div className="section-title">
          <h2>Profile</h2>
          <p>Manage your officer profile information</p>
        </div>

        <div className="profile-card">
          <div className="profile-avatar">RV</div>

          <div className="profile-info">
            <h3>Security Officer</h3>
            <p>Border Surveillance Command</p>
            <span className="status-badge">ACTIVE</span>
          </div>

          <button className="outline-btn">Edit Profile</button>
        </div>
      </section>

      {/* System Preferences */}
      <section className="settings-section">
        <div className="section-title">
          <h2>System Preferences</h2>
          <p>Control dashboard behaviour and display settings</p>
        </div>

        <div className="settings-card">

          <div className="setting-row">
            <div>
              <h3>Dark Mode</h3>
              <p>Use dark interface for low-light environments</p>
            </div>

            <label className="switch">
              <input
                type="checkbox"
                checked={darkMode}
                onChange={() => setDarkMode(!darkMode)}
              />
              <span className="slider"></span>
            </label>
          </div>

          <div className="setting-row">
            <div>
              <h3>Auto Refresh</h3>
              <p>Automatically refresh surveillance data</p>
            </div>

            <label className="switch">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={() => setAutoRefresh(!autoRefresh)}
              />
              <span className="slider"></span>
            </label>
          </div>

          <div className="setting-row">
            <div>
              <h3>Alert Sound</h3>
              <p>Play sound when a critical alert is detected</p>
            </div>

            <label className="switch">
              <input
                type="checkbox"
                checked={soundAlerts}
                onChange={() => setSoundAlerts(!soundAlerts)}
              />
              <span className="slider"></span>
            </label>
          </div>

        </div>
      </section>

      {/* Security */}
      <section className="settings-section">
        <div className="section-title">
          <h2>Security</h2>
          <p>Manage account and authentication preferences</p>
        </div>

        <div className="settings-card">

          <div className="setting-row">
            <div>
              <h3>Two-Factor Authentication</h3>
              <p>Add an additional security layer to your account</p>
            </div>

            <label className="switch">
              <input
                type="checkbox"
                checked={twoFactor}
                onChange={() => setTwoFactor(!twoFactor)}
              />
              <span className="slider"></span>
            </label>
          </div>

          <div className="setting-row">
            <div>
              <h3>Password</h3>
              <p>Last changed 30 days ago</p>
            </div>

            <button className="outline-btn">
              Change Password
            </button>
          </div>

        </div>
      </section>

      {/* Camera Configuration */}
      <section className="settings-section">
        <div className="section-title">
          <h2>Camera Configuration</h2>
          <p>Configure surveillance camera preferences</p>
        </div>

        <div className="camera-settings-grid">

          <div className="select-card">
            <label>Video Quality</label>
            <select defaultValue="1080p">
              <option value="720p">720p HD</option>
              <option value="1080p">1080p Full HD</option>
              <option value="4k">4K Ultra HD</option>
            </select>
          </div>

          <div className="select-card">
            <label>Refresh Interval</label>
            <select defaultValue="5">
              <option value="1">1 second</option>
              <option value="5">5 seconds</option>
              <option value="10">10 seconds</option>
              <option value="30">30 seconds</option>
            </select>
          </div>

          <div className="select-card">
            <label>Recording Mode</label>
            <select defaultValue="continuous">
              <option value="continuous">Continuous</option>
              <option value="motion">Motion Detection</option>
              <option value="manual">Manual</option>
            </select>
          </div>

        </div>
      </section>

      {/* About */}
      <section className="settings-section">
        <div className="section-title">
          <h2>About</h2>
          <p>System information</p>
        </div>

        <div className="about-card">
          <div>
            <h3>RakshaVision AI</h3>
            <p>AI-Based Intelligent Video Analytics Platform</p>
          </div>

          <div className="version">
            <span>VERSION</span>
            <strong>1.0.0</strong>
          </div>
        </div>
      </section>

      <div className="settings-actions">
        <button className="reset-btn">Reset</button>
        <button className="save-btn">Save Changes</button>
      </div>

    </div>
  );
}

export default Settings;

