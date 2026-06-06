import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { api, getAccessToken } from "../api/client";

export function Header() {
  const isLoggedIn = getAccessToken() !== null;
  const [isStaff, setIsStaff] = useState(false);

  useEffect(() => {
    if (isLoggedIn) {
      api.auth.me().then((u) => setIsStaff(u.is_staff)).catch(() => {});
    }
  }, [isLoggedIn]);

  return (
    <div className="header">
      <div className="header-top">
        <div className="logo">
          Teeline <span className="accent">ML</span>
        </div>
        <div className="user-info">
          {isLoggedIn ? (
            <a
              href="#"
              onClick={async (e) => {
                e.preventDefault();
                await api.auth.logout();
                window.location.href = "/";
              }}
            >
              logout
            </a>
          ) : (
            <NavLink to="/login">login</NavLink>
          )}
        </div>
      </div>
      <div className="tabs">
        <NavLink
          to="/"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
          end
        >
          Practice
        </NavLink>
        <NavLink
          to="/words"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          Words
        </NavLink>
        <NavLink
          to="/progress"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          Progress
        </NavLink>
        <NavLink
          to="/leaderboard"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          Leaderboard
        </NavLink>
        {isStaff && (
          <NavLink
            to="/admin"
            className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
          >
            Admin
          </NavLink>
        )}
      </div>
    </div>
  );
}
