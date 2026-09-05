# CreditTech Web App

Borrower + Bank Sakhi web frontend for the CreditTech rural credit-scoring MVP.
Replaces the previously-planned Android app per the 2026-09-03 project decision.

## Stack
- **Vite + React 18 + TypeScript** — modern build tooling, fast HMR
- **Tailwind CSS** with shadcn-inspired design tokens for consistent, accessible styling
- **Radix UI primitives** (`@radix-ui/react-label`, `-slot`) for a11y-first components
- **React Router** for routing
- **TanStack Query** for server state
- **react-hook-form + zod** for form validation
- **lucide-react** for icons
- **Vitest + @testing-library/react** for tests

## Scripts
```
npm install
npm run dev       # http://localhost:5173, proxies /api → http://localhost:8000
npm run build
npm run test
npm run lint
```

The FastAPI backend must be running on `:8000` for API calls to succeed
(`uvicorn services.core.main:app --reload` from the project root).

## Pages
- `/` — home / entry tiles
- `/sakhi` — Bank Sakhi SHG/FPO manual entry (offline-queue on network failure)
- `/borrower` — trigger four-rail aggregation, inspect result
- `/consent` — look up & verify hash-chained consent records

## Offline behaviour
The Sakhi entry form queues submissions in `localStorage` (`credittech.sakhi.queue.v1`)
when the API is unreachable. A background sync worker (P5 finalization) will drain the
queue when connectivity returns. For P2 the queue is inspectable via DevTools.
