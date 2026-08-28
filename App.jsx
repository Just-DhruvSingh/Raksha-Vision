import { BrowserRouter, Routes, Route } from "react-router-dom";

import DashboardLayout from "./layouts/dashboardlayout";

import Dashboard from "./pages/dashboard";
import LiveMonitoring from "./pages/liveMonitoring";
import Alerts from "./pages/Alerts";
import Incidents from "./pages/Incidents";
import Analytics from "./pages/Analytics";
import Cameras from "./pages/Cameras";
import Settings from "./pages/Settings";
function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route element={<DashboardLayout />}>

          <Route path="/" element={<Dashboard />} />

          <Route path="/live" element={<LiveMonitoring />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;