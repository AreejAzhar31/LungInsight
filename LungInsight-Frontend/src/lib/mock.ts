/** Simulates realistic network latency for mock API responses. */
export function mockDelay(ms = 600): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** True when the app is running against mock data instead of a live backend.
 *  Flip VITE_MOCK_MODE=false once LungInsight-Backend is deployed and
 *  VITE_API_BASE_URL points at it -- every api/*.ts function already has
 *  the real Axios call written and ready, gated behind this flag. */
export const MOCK_MODE = import.meta.env.VITE_MOCK_MODE !== 'false';
