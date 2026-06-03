import { useCallback, useEffect, useRef, useState } from "react";

interface JobPollerState<T> {
  data: T | null;
  status: string;
  error: string | null;
  isComplete: boolean;
}

export function useJobPoller<T extends { status: string }>(
  fetcher: (id: string) => Promise<T>,
  terminalStates: string[] = ["completed", "failed"],
  pollInterval = 1000
) {
  const [state, setState] = useState<JobPollerState<T>>({
    data: null,
    status: "",
    error: null,
    isComplete: false,
  });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (id: string) => {
      stopPolling();
      setState({ data: null, status: "pending", error: null, isComplete: false });

      intervalRef.current = setInterval(async () => {
        try {
          const result = await fetcher(id);
          setState((prev) => ({
            ...prev,
            data: result,
            status: result.status,
          }));

          if (terminalStates.includes(result.status)) {
            stopPolling();
            setState((prev) => ({ ...prev, isComplete: true }));
          }
        } catch (err) {
          stopPolling();
          setState((prev) => ({
            ...prev,
            error: err instanceof Error ? err.message : "Failed to check status",
            isComplete: true,
          }));
        }
      }, pollInterval);
    },
    [fetcher, terminalStates, pollInterval, stopPolling]
  );

  useEffect(() => {
    return stopPolling;
  }, [stopPolling]);

  return { ...state, startPolling, stopPolling };
}
