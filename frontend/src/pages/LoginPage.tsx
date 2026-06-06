import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";

export function LoginPage() {
  const navigate = useNavigate();
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [welcomeUser, setWelcomeUser] = useState<string | null>(null);

  function clearErrors() {
    setFieldErrors({});
    setGeneralError(null);
  }

  function parseErrors(body: Record<string, unknown>) {
    if (typeof body.fields === "object" && body.fields !== null) {
      const fields = body.fields as Record<string, string | string[]>;
      const parsed: Record<string, string> = {};
      for (const [key, val] of Object.entries(fields)) {
        parsed[key] = Array.isArray(val) ? (val[0] ?? val.join(", ")) : val;
      }
      setFieldErrors(parsed);
    } else if (typeof body.error === "string") {
      setGeneralError(body.error);
    } else {
      setGeneralError("Something went wrong");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();
    setLoading(true);

    try {
      if (isRegistering) {
        await api.auth.register({ username, email, password });
      }
      await api.auth.login({ username, password });
      setWelcomeUser(username);
      setTimeout(() => navigate("/"), 800);
    } catch (err) {
      if (err instanceof ApiError) {
        parseErrors(err.body as Record<string, unknown>);
      } else {
        setGeneralError("Connection failed");
      }
    } finally {
      setLoading(false);
    }
  }

  if (welcomeUser) {
    return (
      <div className="auth-container auth-centered">
        <div className="auth-card" style={{ textAlign: "center", padding: "48px 28px" }}>
          <div className="section-title">
            Welcome, <span className="accent">{welcomeUser}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container auth-centered">
      <div className="auth-card">
        <div className="logo" style={{ textAlign: "center", fontSize: 24, marginBottom: 24 }}>
          Teeline <span className="accent">ML</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              className={`input ${fieldErrors.username ? "input-error" : ""}`}
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="your username"
              required
            />
            {fieldErrors.username && (
              <div className="field-error">{fieldErrors.username}</div>
            )}
          </div>

          {isRegistering && (
            <div className="form-group">
              <label>Email <span style={{ fontWeight: 400, opacity: 0.5 }}>(optional)</span></label>
              <input
                className={`input ${fieldErrors.email ? "input-error" : ""}`}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
              {fieldErrors.email && (
                <div className="field-error">{fieldErrors.email}</div>
              )}
            </div>
          )}

          <div className="form-group">
            <label>Password</label>
            <input
              className={`input ${fieldErrors.password ? "input-error" : ""}`}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="your password"
              required
              minLength={10}
            />
            {isRegistering && !fieldErrors.password && (
              <div className="field-hint">Minimum 10 characters</div>
            )}
            {fieldErrors.password && (
              <div className="field-error">{fieldErrors.password}</div>
            )}
          </div>

          {generalError && <div className="form-error">{generalError}</div>}

          <div className="form-actions">
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading
                ? "Please wait..."
                : isRegistering
                  ? "Create Account"
                  : "Login"}
            </button>
          </div>

          <div className="form-footer">
            {isRegistering ? (
              <>
                Already have an account?{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); setIsRegistering(false); clearErrors(); }}>
                  Login
                </a>
              </>
            ) : (
              <>
                Need an account?{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); setIsRegistering(true); clearErrors(); }}>
                  Register
                </a>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
