import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '/src/main.jsx': path.resolve(__dirname, 'main.jsx'),
      './layouts/dashboardlayout': path.resolve(__dirname, 'dashboardlayout.jsx'),
      './pages/dashboard': path.resolve(__dirname, 'dashboard.jsx'),
      './pages/liveMonitoring': path.resolve(__dirname, 'liveMonitoring.jsx'),
      './pages/Alerts': path.resolve(__dirname, 'Alerts.jsx'),
      './pages/Incidents': path.resolve(__dirname, 'Incidents.jsx'),
      './pages/Analytics': path.resolve(__dirname, 'Analytics.jsx'),
      './pages/Cameras': path.resolve(__dirname, 'Cameras.jsx'),
      './pages/Settings': path.resolve(__dirname, 'Settings.jsx'),
      '../components/sidebar': path.resolve(__dirname, 'sidebar.jsx'),
      '../components/navbar': path.resolve(__dirname, 'navbar.jsx'),
      '../styles/incidents.css': path.resolve(__dirname, 'incidents.css'),
      '../styles/cameras.css': path.resolve(__dirname, 'cameras.css'),
      '../styles/alerts.css': path.resolve(__dirname, 'alerts.css'),
      '../styles/analytics.css': path.resolve(__dirname, 'analytics.css'),
      '../styles/settings.css': path.resolve(__dirname, 'settings.css'),
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/snapshots': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/sample_videos': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  }
})
