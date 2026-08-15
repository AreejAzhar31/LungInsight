# FRONTEND.md — LungInsight AI Frontend

## Scope

This is the **frontend only**. It does not implement a backend, the AI
model, chatbot logic, Grad-CAM generation, or a database — it consumes
those as APIs. Every network call lives behind a thin API layer
(`src/api/*.ts`) shaped to match the real backend contract (see
`LungInsight-Backend/docs/API.md`) exactly, so connecting to a live
backend is a configuration change, not a rewrite.

## Tech Stack

| Layer | Choice |
|---|---|
| Build tool | Vite |
| Framework | React 19 + TypeScript |
| Styling | Tailwind CSS v4 (CSS-first `@theme`, no config file) |
| Data fetching | Axios + TanStack React Query |
| Global auth state | React Context API |
| Routing | React Router v7 |
| Animation | Framer Motion |
| Charts | Recharts |
| Icons | lucide-react |
| Testing | Vitest + React Testing Library |

## Getting Started

```bash
npm install
cp .env.example .env
npm run dev
```

Runs at `http://localhost:5173` by default, entirely against mock data —
no backend required to explore every page.

```bash
npm run build      # production build (runs tsc -b && vite build)
npm run test        # run once (add to package.json if not present: "test": "vitest run")
npx vitest           # watch mode
npx vitest run        # single run, used in CI
```

## Mock Mode vs. Live Backend

Every function in `src/api/*.ts` is written twice in one place: a mock
branch and a real Axios branch, gated by a single flag.

```ts
// src/api/predictions.ts
export async function createPrediction(file: File): Promise<Prediction> {
  if (MOCK_MODE) {
    await mockDelay(1200);
    return mockPredictionResult();
  }
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await apiClient.post<Prediction>('/api/v1/prediction', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
```

**To connect to a real backend:**
1. Set `VITE_MOCK_MODE=false` in `.env`
2. Set `VITE_API_BASE_URL` to point at your running `LungInsight-Backend` instance
3. Nothing else changes — every hook, component, and page already calls these same functions

**Endpoints not yet built anywhere** (chat/RAG, admin user management,
`GET /users/me`) stay mocked regardless of the flag, since there's no real
endpoint yet to call — see the comment at the top of `src/api/chat.ts` and
`src/api/admin.ts`.

## Project Structure

```
src/
  api/            One module per backend resource (auth, predictions, history,
                   feedback, health, chat, dashboard, admin) -- mock/real toggle lives here
  components/
    ui/            Generic building blocks: Button, Card, Badge, Input, Skeleton, States
    layout/         Sidebar, Navbar, AppShell, ProtectedRoute
    prediction/      Uploader, HeatmapViewer, PredictionCard
    dashboard/        Charts (confidence trend, distribution)
    chat/              ChatWindow, SourceCitationCard
    feedback/           FeedbackForm
  context/           AuthContext (Context API)
  hooks/              React Query hooks, one file per resource group
  pages/               One component per route
  types/                Shared TypeScript types, mirroring backend schemas
  mocks/                 Mock data generators
  lib/                    Axios instance, mock-mode helpers
  test/                    Vitest setup + shared render-with-providers utility
```

## Routing & Auth

All routes are defined in `src/App.tsx`. Authenticated pages are wrapped in
`<ProtectedRoute>`, which redirects to `/login` if `AuthContext.isAuthenticated`
is false. Auth state itself lives in `AuthContext` (Context API), backed by
`localStorage` for token persistence across reloads and React Query-free
by design — auth is app-wide singleton state, not server cache, so Context
is the right tool here (React Query handles everything that *is* server
cache: predictions, history, chat, etc.).

| Route | Protected | Page |
|---|---|---|
| `/` | No | Landing |
| `/login` | No | Login |
| `/register` | No | Register |
| `/dashboard` | Yes | Dashboard |
| `/upload` | Yes | Upload |
| `/prediction/:id` | Yes | Prediction detail |
| `/history` | Yes | History |
| `/chat` | Yes | Chat |
| `/settings` | Yes | Settings |
| `/admin` | Yes | Admin |
| `*` | No | 404 |

## Upload Flow

Implements the exact flow from the project spec:

```
Image Upload -> Preview -> API Call Placeholder -> Display Mock Response
```

See `src/pages/UploadPage.tsx` + `src/components/prediction/Uploader.tsx`.
The "API Call Placeholder" is `useCreatePrediction()` (React Query mutation
wrapping `createPrediction()` from `src/api/predictions.ts`), which returns
mock data today and a real backend response with zero code changes once
`VITE_MOCK_MODE=false`.

## Design System

See the `@theme` block in `src/index.css` for the full token set. Summary:
a light "clinical lightbox" palette (grounded in how radiologists actually
view film — a lit panel, not a dark dashboard), with a signature
`.viewbox-frame` treatment (corner-tick border, evoking a film mount) used
on the Uploader, HeatmapViewer, PredictionCard, and auth forms. Brick-red
is reserved exclusively for Pneumonia-positive flags and never used as a
generic UI accent, so it keeps its meaning at a glance.

## Testing

```bash
npx vitest run
```

57 tests across 14 files: UI components, feature components (Uploader,
HeatmapViewer, ChatWindow, FeedbackForm), AuthContext, ProtectedRoute
redirect behavior, the mock API layer, mock data generators, and full
page-level flows (Login, and the entire Upload -> Preview -> Analyze ->
Result cycle). See `COMPONENTS.md` for a per-component breakdown.

Two real jsdom gaps were hit and fixed during development (documented in
`src/test/setup.ts`): jsdom doesn't implement `URL.createObjectURL` or
`Element.prototype.scrollIntoView`, both of which real components in this
app call — both are polyfilled with no-op mocks in the test setup file.

## Known Limitations / Handoff Notes

- **No `GET /users/me` endpoint exists on the backend yet** — `getCurrentUser()` is fully mocked in `src/api/auth.ts` regardless of `MOCK_MODE`.
- **Chat/RAG and Admin have no backend module yet** — `src/api/chat.ts` and `src/api/admin.ts` are fully mocked; shapes are designed for an easy swap once those modules exist.
- **Heatmap images**: the backend's `Prediction.heatmap_path` is a server-side file path, not a servable URL, in the current Module 2 implementation. `HeatmapViewer` expects a fetchable URL — this will need either a static-file route added to the backend or a signed-URL scheme before real heatmaps can render.
- **Bundle size**: the production JS bundle is ~876KB (266KB gzipped), flagged by Vite's build warning. Not addressed here since it doesn't block functionality, but code-splitting by route (`React.lazy`) would be the first lever if this becomes a real concern.
