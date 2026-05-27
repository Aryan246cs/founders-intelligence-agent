/**
 * Base API client — all requests go through here.
 * Handles base URL, default headers, and error normalization.
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

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, { ...options, headers });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new ApiError(res.status, `API error ${res.status}`, data);
      }

      return res.json() as Promise<T>;
    } catch (err) {
      if (err instanceof ApiError) throw err;
      if (attempt === retries) throw err;
      // Exponential backoff: 300ms, 600ms
      await new Promise((r) => setTimeout(r, 300 * (attempt + 1)));
    }
  }

  throw new Error("Request failed after retries");
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
};
