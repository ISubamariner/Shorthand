import { useEffect, useState } from "react";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";
const MAX_RETRIES = 20;
const INITIAL_DELAY = 1500;
const MAX_DELAY = 5000;

export function useBackendStatus() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let attempt = 0;

    async function ping() {
      while (!cancelled && attempt < MAX_RETRIES) {
        try {
          const res = await fetch(`${BASE_URL}/health/`, {
            method: "GET",
            signal: AbortSignal.timeout(5000),
          });
          if (res.ok) {
            if (!cancelled) setReady(true);
            return;
          }
        } catch {
          // network error or timeout — backend still waking up
        }
        attempt++;
        const delay = Math.min(INITIAL_DELAY * Math.pow(1.3, attempt), MAX_DELAY);
        await new Promise((r) => setTimeout(r, delay));
      }
      if (!cancelled) setReady(true);
    }

    ping();
    return () => { cancelled = true; };
  }, []);

  return ready;
}
