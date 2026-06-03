import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";

export function LoginPage() {
  const navigate = useNavigate();
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegistering) {
        await api.auth.register({ username, email, password });
      }
      await api.auth.login({ username, password });
      navigate("/");
    } catch (err) {
      if (err instanceof ApiError) {
        const body = err.body as Record<string, unknown>;
        setError(
          typeof body?.error === "string"
            ? body.error
            : typeof body?.fields === "object"
              ? Object.values(body.fields as Record<string, string>).join(", ")
              : "Something went wrong"
        );
      } else {
        setError("Connection failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="logo" style={{ textAlign: "center", fontSize: 24, marginBottom: 24 }}>
          Teeline <span className="accent">ML</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              className="input"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="your username"
              required
            />
          </div>

          {isRegistering && (
            <div className="form-group">
              <label>Email</label>
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Password</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="your password"
              required
              minLength={10}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

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
                <a href="#" onClick={(e) => { e.preventDefault(); setIsRegistering(false); setError(null); }}>
                  Login
                </a>
              </>
            ) : (
              <>
                Need an account?{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); setIsRegistering(true); setError(null); }}>
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
