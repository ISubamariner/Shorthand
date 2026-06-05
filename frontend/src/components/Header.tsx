import { NavLink } from "react-router-dom";
import { api, getAccessToken } from "../api/client";

const API_BASE = import.meta.env.VITE_API_URL || "/api";
const ADMIN_URL = API_BASE.replace(/\/api\/?$/, "/admin/");

export function Header() {
  const isLoggedIn = getAccessToken() !== null;

  return (
    <div className="header">
      <div className="header-top">
        <div className="logo">
          Teeline <span className="accent">ML</span>
        </div>
        {isLoggedIn && (
          <div className="user-info">
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                api.auth.logout();
                window.location.href = "/login";
              }}
            >
              logout
            </a>
          </div>
        )}
      </div>
      {isLoggedIn && (
        <div className="tabs">
          <NavLink
            to="/"
            className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
            end
          >
            Practice
          </NavLink>
          <NavLink
            to="/progress"
            className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
          >
            Progress
          </NavLink>
          <a
            href={ADMIN_URL}
            className="tab"
            target="_blank"
            rel="noopener noreferrer"
          >
            Admin
          </a>
        </div>
      )}
    </div>
  );
}
