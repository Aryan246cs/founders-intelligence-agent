/**
 * Product mark: a tracking reticle — two opposing arcs closing on a fixed
 * point. It reads as "lock onto a signal", which is what the platform does,
 * and it stays legible down to 16px where a detailed glyph would turn to mud.
 *
 * Monochrome and driven by `currentColor` so it inherits its surface's colour
 * rather than carrying a gradient of its own.
 */
export function Logomark({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M12 3.75A8.25 8.25 0 0 1 20.25 12"
        stroke="currentColor"
        strokeWidth="2.1"
        strokeLinecap="round"
      />
      <path
        d="M12 20.25A8.25 8.25 0 0 1 3.75 12"
        stroke="currentColor"
        strokeWidth="2.1"
        strokeLinecap="round"
      />
      <circle cx="12" cy="12" r="2.75" fill="currentColor" />
    </svg>
  );
}
