# Breaking Bread

AI-powered cooking companion (web app) for college students early in off-campus apartment life who are new to cooking. A user pastes a TikTok or reel link and gets a meal they can shop for, afford, and cook.

Full context: `docs/product-brief.md`. Decisions and open questions: `docs/decisions.md`.

## Sprint MVP (three weeks): one end-to-end flow
Pasted TikTok/reel link -> ingredients identified -> grocery list -> estimated meal cost -> per-meal macros -> step-by-step beginner cooking guidance. Delivered as a web app.

Success = this flow works reliably end to end. Prioritize work that completes the flow over polishing any one step.

## Scope rules
- Stretch goal only: nearby stores where the user can buy ingredients. Don't start it until the core flow works.
- Out of scope: built-in recipe library, fridge/pantry "what can I make" workflow, recommendations based on goals/likes/dislikes, weekly spend tracking, direct ordering or checkout, native mobile app.
- If a request drifts into an out-of-scope item, say so before doing the work.

## Product principles
- Differentiator is integrated budgeting plus beginner guidance. Macros are supporting value.
- When design choices conflict, favor cost clarity and simplicity.
- All user-facing copy and guidance must be beginner-friendly: plain words, no assumed kitchen knowledge, short steps.
- Cost is always an estimate. Show it as approximate and never present it as exact.

## Open decisions: do not assume answers
These are unresolved (see `docs/decisions.md`). Propose options with tradeoffs and ask before committing:
- Grocery price data source, and how accurate cost estimates can be
- Macronutrient data source
- Reliability of ingredient extraction from links (captions may lack ingredients; platform access may be restricted)
When a decision is made, record it in `docs/decisions.md`.

## Tech stack and commands
TODO: fill in once chosen (framework, language, hosting, how to run dev server, tests, lint).

## Team
Sarah Fattah, Sahil Saboo, Brendan Schemer (AI Builder Space Proseminar).
