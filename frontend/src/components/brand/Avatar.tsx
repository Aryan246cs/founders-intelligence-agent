import { cn } from "@/lib/utils";

/**
 * Initials avatar. Flat surface with a hairline ring — deliberately not a
 * gradient chip, which is the first thing that makes an interface look
 * generated rather than built.
 */
export function Avatar({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-md bg-zinc-800 ring-1 ring-inset ring-zinc-700 text-zinc-300 font-medium select-none",
        className
      )}
    >
      {initials}
    </span>
  );
}
