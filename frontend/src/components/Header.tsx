import { NavLink } from "react-router-dom";
import { api, getAccessToken } from "../api/client";

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
        </div>
      )}
    </div>
  );
}
