import { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { api, getAccessToken } from "../api/client";

export function Header() {
  const isLoggedIn = getAccessToken() !== null;
  const [username, setUsername] = useState<string | null>(null);
  const [isStaff, setIsStaff] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (isLoggedIn) {
      api.auth.me().then((u) => {
        setUsername(u.username);
        setIsStaff(u.is_staff);
      }).catch(() => {});
    }
  }, [isLoggedIn]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [dropdownOpen]);

  return (
    <div className="header">
      <div className="header-top">
        <div className="logo">
          Teeline <span className="accent">ML</span>
        </div>
        <div className="user-info">
          {isLoggedIn && username ? (
            <div className="user-dropdown" ref={dropdownRef}>
              <button
                className="user-dropdown-toggle"
                onClick={() => setDropdownOpen((v) => !v)}
              >
                {username} <span className="user-dropdown-caret">&#9662;</span>
              </button>
              {dropdownOpen && (
                <div className="user-dropdown-menu">
                  <button
                    className="user-dropdown-item"
                    onClick={() => { setDropdownOpen(false); navigate("/settings"); }}
                  >
                    Settings
                  </button>
                  <button
                    className="user-dropdown-item"
                    onClick={async () => {
                      setDropdownOpen(false);
                      await api.auth.logout();
                      window.location.href = "/";
                    }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
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
        <NavLink
          to="/about"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          About
        </NavLink>
        <NavLink
          to="/credits"
          className={({ isActive }) => `tab ${isActive ? "active" : ""}`}
        >
          Credits
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
