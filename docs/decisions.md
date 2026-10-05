# Decision Log

Record each decision when it is made: what was decided, why, who decided, and the date. Until a row says "Decided", treat the item as open and propose options rather than assuming.

| # | Question | Status | Decision | Rationale | Owner | Date |
|---|----------|--------|----------|-----------|-------|------|
| 1 | Grocery price data source | Open | | | | |
| 2 | Cost estimate accuracy target and how to show uncertainty to users | Open | | | | |
| 3 | Macronutrient data source | Open | | | | |
| 4 | Ingredient extraction approach from a pasted link | Open | | | | |
| 5 | Fallback when a link has no usable ingredient info or platform access fails | Open | | | | |
| 6 | Web app tech stack | Decided | Next.js (TypeScript) frontend + Python FastAPI backend; Claude API for structuring; no DB/auth this sprint | Extraction pipeline is the main risk and fits Python tooling; team has Python experience; MVP flow is stateless | | 2026-10-05 |
| 7 | Verify established alternatives (Samsung Food, Paprika, AnyList, Plan to Eat) | Open | | | | |
| 8 | Hosting for frontend and backend | Open | | | | |

## Notes on open items

- **1-2 Prices:** Prices vary by store and location, so any estimate is approximate. Whatever source is chosen, the UI should show cost as an estimate (favor cost clarity).
- **4-5 Extraction:** Some reels do not list ingredients in captions or descriptions, and platform access may be restricted. Check platform terms of service before relying on content download. The flow needs a defined behavior for these cases.
- **8 Hosting:** Video download and transcription may exceed serverless time limits, which affects where the backend runs.
- Candidate options for each item should be researched and verified before they are written here. Do not record an option as fact without a source.
