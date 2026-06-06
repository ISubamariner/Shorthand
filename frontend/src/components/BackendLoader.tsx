import { useBackendStatus } from "../hooks/useBackendStatus";

export function BackendLoader({ children }: { children: React.ReactNode }) {
  const ready = useBackendStatus();

  if (!ready) {
    return (
      <div className="backend-loader">
        <div className="backend-loader__content">
          <div className="backend-loader__pen" aria-hidden="true">
            ✒
          </div>
          <p className="backend-loader__text">Waking up the server&hellip;</p>
          <div className="backend-loader__dots">
            <span className="backend-loader__dot" />
            <span className="backend-loader__dot" />
            <span className="backend-loader__dot" />
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
