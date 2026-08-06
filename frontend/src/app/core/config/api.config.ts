/** Central API origin: separate backend locally, same origin in deployments. */
const locationRef = globalThis.location;

export const API_ORIGIN = locationRef?.hostname === 'localhost'
  ? 'http://localhost:8000'
  : (locationRef?.origin ?? '');

export const API_V1 = `${API_ORIGIN}/api/v1`;

export function backendAssetUrl(path: string): string {
  return path.startsWith('http') ? path : `${API_ORIGIN}${path}`;
}

/** Backwards-compatible helpers used by production-oriented UI components. */
export function getApiBaseUrl(): string {
  return API_ORIGIN;
}

export function getStaticBaseUrl(): string {
  return API_ORIGIN;
}
