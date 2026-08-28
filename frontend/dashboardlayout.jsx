import { Outlet } from "react-router-dom";
import Sidebar from "../components/sidebar";
import Navbar from "../components/navbar";

function DashboardLayout() {
  return (
    <div className="app-layout">

      <Sidebar />

      <div className="main-area">

        <Navbar />

        <main className="page-content">
          <Outlet />
        </main>

      </div>

    </div>
  );
}

export default DashboardLayout;