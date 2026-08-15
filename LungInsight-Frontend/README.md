# LungInsight AI — Frontend

React + TypeScript frontend for LungInsight AI. Consumes the backend,
AI model, and chatbot/RAG modules as APIs -- none of that logic lives here.

## Quick Start

```bash
npm install
cp .env.example .env
npm run dev
```

Opens at `http://localhost:5173`, fully explorable against mock data with
no backend running.

## Documentation

- [`FRONTEND.md`](FRONTEND.md) -- architecture, tech stack, mock-mode/live-backend toggle, routing, design system
- [`COMPONENTS.md`](COMPONENTS.md) -- per-component reference and test coverage

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Start the dev server |
| `npm run build` | Type-check + production build |
| `npm run preview` | Preview the production build locally |
| `npm run test` | Run the test suite once |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | Lint the codebase |

## Connecting to a Live Backend

Set in `.env`:
```
VITE_MOCK_MODE=false
VITE_API_BASE_URL=http://localhost:8000
```

See `FRONTEND.md` -> "Mock Mode vs. Live Backend" for details on how this
works under the hood.
