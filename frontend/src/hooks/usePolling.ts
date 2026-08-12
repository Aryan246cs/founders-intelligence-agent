import { useEffect, useRef } from "react";

/**
 * Runs `fn` immediately and then every `intervalMs` milliseconds.
 * Stops when the component unmounts or `enabled` becomes false.
 *
 * Polling pauses while the tab is hidden and resumes with an immediate refresh
 * on return. Several panels poll on 10-30s timers; left running, a backgrounded
 * dashboard would keep hammering Supabase all day and still show stale data the
 * moment the user looks at it again.
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
    let timer: ReturnType<typeof setInterval> | null = null;

    const run = async () => {
      if (!cancelled && !document.hidden) await fnRef.current();
    };

    const start = () => {
      if (timer !== null) return;
      timer = setInterval(run, intervalMs);
    };

    const stop = () => {
      if (timer !== null) clearInterval(timer);
      timer = null;
    };

    const onVisibilityChange = () => {
      if (document.hidden) {
        stop();
      } else {
        run();
        start();
      }
    };

    run();
    start();
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      cancelled = true;
      stop();
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [intervalMs, enabled]);
}
