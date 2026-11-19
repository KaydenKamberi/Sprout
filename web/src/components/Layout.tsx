import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import Vine from "./Vine";
import "./Layout.css";

type Theme = "light" | "dark";

// Matches the six menu items in the D4 mockups; the vine marks the active one.
const NAV_ITEMS = [
  { label: "Home", to: "/", match: (p: string) => p === "/" },
  { label: "Plants", to: "/plants/1", match: (p: string) => /^\/plants\/\d+$/.test(p) || /^\/plants\/\d+\/diagnoses$/.test(p) },
  { label: "Devices", to: "/devices", match: (p: string) => p.startsWith("/devices") },
  { label: "History", to: "/plants/1/history", match: (p: string) => p.endsWith("/history") },
  { label: "Account", to: "/account", match: (p: string) => p === "/account" },
  { label: "Help", to: "/help", match: (p: string) => p === "/help" },
];

function initialTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

export default function Layout() {
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const { pathname } = useLocation();

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("sprout-theme", theme);
  }, [theme]);
  const activeIndex = NAV_ITEMS.findIndex((item) => item.match(pathname));

  return (
    <div className="app-frame">
      <header className="app-header">
        <span className="logo">Sprout</span>
        <div className="header-actions">
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? "Dark" : "Light"}
          </button>
          <nav className="auth-links">
            <Link to="/login" className="auth-link">
              Log in
            </Link>
            <Link to="/signup" className="auth-link auth-link-primary">
              Sign up
            </Link>
          </nav>
        </div>
      </header>
      <div className="frame">
        <aside className="sidebar">
          <Vine activeItem={activeIndex} />
          <nav className="menu">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={item.match(pathname) ? "current" : undefined}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="main-area">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
