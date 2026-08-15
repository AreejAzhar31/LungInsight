# COMPONENTS.md — LungInsight AI Frontend Component Reference

## UI primitives (`src/components/ui/`)

### `Button`
`variant`: `primary | secondary | ghost | danger`. `size`: `sm | md | lg`.
Forwards a ref, spreads native `<button>` props. Danger variant uses the
flag-red token, reserved elsewhere for pneumonia-positive states, so use
it sparingly for genuinely destructive actions only.

### `Card`, `StatCard`
`Card` is a generic bordered/padded panel (`as="section"` for landmark
semantics where relevant). `StatCard` adds a label/value/hint/icon layout,
used for the Dashboard's Total Predictions and Average Confidence tiles.

### `PredictionBadge`
Renders a `Normal` or `Pneumonia` pill with an optional confidence
percentage. Color is driven entirely by `label` — this is the only place
label-to-color mapping is defined, so it stays consistent everywhere a
prediction result appears (Dashboard, History, PredictionCard, Upload
result, HeatmapViewer frame).

### `Input`, `Textarea`
Labeled form fields with built-in error display (`Input` only) and
`aria-invalid` wiring. Both forward refs.

### `Skeleton`, `StatCardSkeleton`, `CardSkeleton`, `TableRowSkeleton`, `ListSkeleton`
Loading-state placeholders. Every page that fetches data (`Dashboard`,
`History`, `Admin`) renders the matching skeleton while `isLoading` is
true, never a bare spinner.

### `ErrorState`, `EmptyState`
`ErrorState` takes a `message` and optional `onRetry` (renders a "Try
again" button that re-triggers the query). `EmptyState` takes
`title`/`message`/optional `icon`/`action`, used whenever a list is empty
without a request error.

## Layout (`src/components/layout/`)

### `Sidebar`
Fixed-width icon+label nav (`NAV_ITEMS` array), active-route highlighting
via `NavLink`'s `isActive`. Hidden below `md` breakpoint (mobile nav is a
known gap — see FRONTEND.md limitations).

### `Navbar`
Topbar showing the current user's name/email and a logout button. Reads
`user` from `AuthContext`.

### `AppShell`
Combines `Sidebar` + `Navbar` + a padded `<main>` — every authenticated
page wraps its content in `<AppShell>`.

### `ProtectedRoute`
Redirects to `/login` if `useAuth().isAuthenticated` is false. Wraps every
route except Landing/Login/Register/404 in `App.tsx`.

## Prediction feature components (`src/components/prediction/`)

### `Uploader`
Drag-and-drop + click-to-browse file picker with inline preview.
Validates file type client-side (`image/jpeg`, `image/png`, `image/jpg`)
before calling `onFileSelected`; shows an inline error otherwise. Note:
the browser's native file picker already filters by the input's `accept`
attribute, so the client-side validation primarily guards the drag-and-drop
path, which bypasses that filter.

Props: `onFileSelected(file)`, `selectedFile`, `onClear()`, `disabled?`.

### `HeatmapViewer`
Displays the original X-ray with an optional Grad-CAM overlay image, plus
a visibility toggle and an opacity slider (0–100%). Renders whatever
`heatmapUrl` it's given — **does not generate heatmaps itself**; that's
the AI module's job (see `LungInsight-AI/utils/gradcam.py`). Falls back to
a "no heatmap available" message when `heatmapUrl` is `null`.

Props: `originalImageUrl`, `heatmapUrl: string | null`, `label`.

### `PredictionCard`
Compact clickable summary card (filename, date, badge), links to
`/prediction/:id`. Used in list/grid contexts; the full detail view is the
`PredictionPage`, not this component.

## Dashboard components (`src/components/dashboard/`)

### `ConfidenceTrendChart`
Recharts line chart of average confidence over time, from
`DashboardSummary.confidenceTrend`.

### `DistributionChart`
Recharts donut chart of Normal vs. Pneumonia counts, from
`DashboardSummary.distribution`. Uses the same cyan/flag-red color mapping
as `PredictionBadge` for visual consistency.

## Chat components (`src/components/chat/`)

### `ChatWindow`
Message list (auto-scrolls to bottom on new messages) + input form.
Renders `SourceCitationCard`s inline under any assistant message that has
`citations`. Takes `messages`, `onSend(content)`, optional `isSending` (shows a
"Thinking…" bubble and disables the input).

### `SourceCitationCard`
Small bordered card for one RAG citation (`title` + `snippet`). Purely
presentational — no fetching, no click-through yet (citations don't carry
a resolvable link in the current mock shape beyond an optional `url` field).

## Feedback (`src/components/feedback/`)

### `FeedbackForm`
5-star rating (radiogroup, keyboard-accessible) + optional comment
textarea, submits via `useSubmitFeedback()`. Shows a success message
in place of the form after a successful submission rather than resetting
it, so the user gets clear confirmation.

## Testing Coverage Summary

| Component | Test file | Focus |
|---|---|---|
| Button | `ui/Button.test.tsx` | rendering, click handling, disabled state, variants |
| Badge | `ui/Badge.test.tsx` | label rendering, flag styling, confidence display |
| Input | `ui/Input.test.tsx` | label association, error/aria-invalid, onChange |
| ErrorState / EmptyState | `ui/States.test.tsx` | message rendering, retry callback, action slot |
| Uploader | `prediction/Uploader.test.tsx` | file selection, type validation (picker + drop paths), preview, clear |
| HeatmapViewer | `prediction/HeatmapViewer.test.tsx` | image rendering, overlay toggle, no-heatmap fallback |
| ChatWindow | `chat/ChatWindow.test.tsx` | empty state, message + citation rendering, send flow, sending state |
| FeedbackForm | `feedback/FeedbackForm.test.tsx` | disabled-until-rated, submit flow, success state |
| AuthContext | `context/AuthContext.test.tsx` | register/login/logout state transitions, token persistence, outside-provider error |
| ProtectedRoute | `layout/ProtectedRoute.test.tsx` | redirect when unauthenticated |
| LoginPage | `pages/LoginPage.test.tsx` | field rendering, required validation, submit flow |
| UploadPage | `pages/UploadPage.test.tsx` | full upload → preview → analyze → mock result flow, clear-before-analysis |
| predictions API | `api/predictions.test.ts` | mock CRUD behavior, not-found error, pagination |
| mock data generators | `mocks/data.test.ts` | count/shape correctness, dashboard aggregation, zero-division safety |

Run `npx vitest run` for the full suite (57 tests, all passing as of this
writing).
