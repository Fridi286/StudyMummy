/**
 * Resolves the backend API base URL dynamically based on the current frontend environment.
 * - In local development (localhost on any port), points to `http://localhost:8000`.
 * - In production deployment, returns empty string `''`
 *   so that API requests use relative paths (`/api/v1/...`) proxied by Nginx.
 */
export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  return '';
}

/**
 * Resolves the static assets base URL dynamically (e.g. for user avatars and item icons).
 */
export function getStaticBaseUrl(): string {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  return '';
}
