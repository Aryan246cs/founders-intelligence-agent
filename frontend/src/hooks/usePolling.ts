import { useEffect, useRef, useCallback } from "react";

/**
 * Runs `fn` immediately and then every `intervalMs` milliseconds.
 * Stops when the component unmounts or `enabled` becomes false.
 */
export function usePolling(
  fn: () => void | Promise<void>,
  intervalMs: number,
  enabled = true
) {
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;

    const run = async () => {
      if (!cancelled) await fnRef.current();
    };

    run();
    const id = setInterval(run, intervalMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [intervalMs, enabled]);
}
