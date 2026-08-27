/**
 * Identity shown in the chrome (wordmark, account row).
 *
 * Env-overridable so the app doesn't ship someone else's name hardcoded into
 * the sidebar — set NEXT_PUBLIC_USER_NAME / NEXT_PUBLIC_WORKSPACE_NAME in
 * frontend/.env to change what appears.
 */
export const WORKSPACE = {
  productName: "Founder Intel",
  version: "v1.1",
  userName: process.env.NEXT_PUBLIC_USER_NAME ?? "Aryan",
  workspaceName: process.env.NEXT_PUBLIC_WORKSPACE_NAME ?? "Personal workspace",
} as const;
