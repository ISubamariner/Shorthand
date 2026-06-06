import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, getAccessToken } from "../../api/client";
import type { User } from "../../types";

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<"loading" | "allowed" | "denied">("loading");

  useEffect(() => {
    if (!getAccessToken()) {
      setState("denied");
      return;
    }
    api.auth
      .me()
      .then((user: User) => setState(user.is_staff ? "allowed" : "denied"))
      .catch(() => setState("denied"));
  }, []);

  if (state === "loading") {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <p style={{ color: "var(--muted)", fontSize: 12 }}>Loading...</p>
      </div>
    );
  }

  if (state === "denied") {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
