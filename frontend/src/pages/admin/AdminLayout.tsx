import { NavLink, Outlet } from "react-router-dom";
import { api } from "../../api/client";

const NAV_ITEMS = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/content", label: "Content" },
  { to: "/admin/analytics", label: "Analytics" },
  { to: "/admin/jobs", label: "Jobs" },
  { to: "/admin/audit-log", label: "Audit Log" },
  { to: "/admin/settings", label: "Settings" },
];

export function AdminLayout() {
  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-logo">
          Teeline <span className="accent">ML</span>
          <div style={{ fontSize: 10, opacity: 0.5, marginTop: 4 }}>Admin</div>
        </div>
        <nav className="admin-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="admin-main">
        <div className="admin-topbar">
          <a href="/">Back to app</a>
          <a
            href="#"
            onClick={async (e) => {
              e.preventDefault();
              await api.auth.logout();
              window.location.href = "/";
            }}
          >
            Logout
          </a>
        </div>
        <div className="admin-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
