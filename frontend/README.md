# Breaking Bread frontend

Next.js app (UI only). See the [root README](../README.md) for setup and `../CLAUDE.md` for conventions.

- `npm run dev`: dev server on http://localhost:3000. Requests to `/api/*` are forwarded to the backend at `BACKEND_URL` (default http://localhost:8000).
- `npm run gen:api`: regenerate `src/lib/api-types.ts` from `../backend/openapi.json`. Don't edit that file by hand.
- Screens live in `src/app/`, and the components they use live in `src/components/`.
