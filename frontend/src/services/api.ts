/**
 * Base API client — all requests go through here.
 * Handles base URL, default headers, retries and error normalization.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Pull a human-readable message out of a FastAPI error body.
 *
 * FastAPI puts the message in `detail`, which is a string for HTTPException,
 * a list of field errors for validation failures, and occasionally a nested
 * object (the workflow endpoints return the whole execution envelope). Losing
 * it and showing "API error 503" would hide the one line that says what to fix.
 */
function extractMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const parts = detail
      .map((d) => {
        const item = d as { loc?: unknown[]; msg?: string };
        const field = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .filter(Boolean);
    if (parts.length) return parts.join("; ");
  }

  if (detail && typeof detail === "object") {
    const message = (detail as { message?: string }).message;
    if (message) return message;
  }

  return `Request failed with status ${status}`;
}

/** 4xx responses mean the request itself is wrong — repeating it cannot help. */
function isRetryable(status: number): boolean {
  return status >= 500 || status === 429;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retries = 2
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers ?? {}),
  };

  let lastError: unknown;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, { ...options, headers });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const error = new ApiError(res.status, extractMessage(res.status, body), body);
        if (!isRetryable(res.status) || attempt === retries) throw error;
        lastError = error;
      } else {
        return (await res.json()) as T;
      }
    } catch (err) {
      // A thrown ApiError for a non-retryable status is final.
      if (err instanceof ApiError && !isRetryable(err.status)) throw err;
      lastError = err;
      if (attempt === retries) throw err;
    }

    // Exponential backoff: 300ms, 600ms
    await new Promise((r) => setTimeout(r, 300 * (attempt + 1)));
  }

  throw lastError ?? new Error("Request failed after retries");
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
};
