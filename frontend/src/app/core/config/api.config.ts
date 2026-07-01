/**
 * Resolves the backend API base URL dynamically based on the current frontend environment.
 * - In local development via `ng serve` (port 4200), points to `http://localhost:8000`.
 * - In production deployment (port 80, 443, or custom Nginx port), returns empty string `''`
 *   so that API requests use relative paths (`/api/v1/...`) proxied by Nginx.
 */
export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined' && window.location.port === '4200') {
    return 'http://localhost:8000';
  }
  return '';
}

/**
 * Resolves the static assets base URL dynamically (e.g. for user avatars and item icons).
 */
export function getStaticBaseUrl(): string {
  if (typeof window !== 'undefined' && window.location.port === '4200') {
    return 'http://localhost:8000';
  }
  return '';
}
