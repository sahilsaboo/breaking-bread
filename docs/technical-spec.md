# Breaking Bread: Technical Spec

Detailed build spec for the sprint. Product context and scope live in `docs/product-brief.md`; decision history lives in `docs/decisions.md`. If this spec and the decision log disagree, the decision log wins and this file should be updated.

## What we're building

Breaking Bread is a web app that turns a pasted TikTok or Instagram Reel link into a meal a beginner cook can shop for, afford, and make. The audience is college students new to apartment life. This sprint (three weeks) builds exactly one end-to-end flow:

**Paste link → extract recipe → user checks off what they already own → grocery list with prices → per-meal macros → beginner-friendly step-by-step guidance.**

There are no accounts. The user-facing flow is stateless: paste and go. The backend keeps a cache (see Caching).

## Stack

- **Frontend:** Next.js (React, TypeScript), deployed on Vercel.
- **Backend:** Python with FastAPI, deployed on a host that supports long-running requests and system packages (Render, Railway, or Fly.io; specific host still open).
- **Media tooling:** `yt-dlp` for metadata and video download, `ffmpeg` for audio extraction and frame sampling.
- **Transcription:** `faster-whisper` (local, free).
- **LLM:** Claude API with vision, for structuring recipes, reading on-screen text in frames, normalizing quantities, and writing beginner guidance.
- **Nutrition:** USDA FoodData Central API (free key from api.data.gov).
- **Pricing:** Open. See Pricing below.
- **Cache:** SQLite, plus committed JSON fixtures for demo reels.

## User flow

1. **Paste link.** The user pastes a TikTok or Instagram Reel URL. Validate the URL format before doing any work.
2. **Extraction.** Show a progress state. Extraction can take 30–90 seconds, so the UI should show which stage is running.
3. **Location.** Prompt for a ZIP code, with optional browser geolocation. Use it to find nearby stores and prices where the pricing source supports it.
4. **Pantry checkoff.** Show the extracted ingredient list. The user checks off items they already own. This screen is also where the user can spot an ingredient that was extracted incorrectly.
5. **Results.** A single page shows:
   - the grocery list (items not checked off), with the store and price for each item
   - **trip cost** and **per-meal cost**, side by side
   - macronutrients per serving
   - step-by-step cooking guidance

**Fallback:** If extraction fails or finds no usable ingredients, show a clear error that says why, and offer a text box where the user can paste the caption, ingredient list, or recipe text. Pasted text enters the pipeline at the merge step and the flow continues from there.

## Platforms

TikTok is the primary platform and must work for the demo. Instagram Reels is best effort: attempt it, but the demo must not depend on it (Instagram often requires login). Review both platforms' terms of service before relying on content download.

## Extraction pipeline

Run the stages in order and stop early once the recipe is confidently complete.

1. **Metadata.** Use `yt-dlp` to fetch the caption, description, title, and creator. If the caption contains a full ingredient list, structure it with the LLM and skip to the merge step.
2. **Audio.** Download the video, extract the audio with `ffmpeg`, and transcribe it with `faster-whisper`.
3. **Frames.** Sample frames, for example 1 frame every 2 seconds with a cap of about 20. Send them to Claude vision to capture on-screen text (ingredient overlays, measurements) and visibly used ingredients.
4. **Merge.** Combine caption, transcript, frame findings, and any user-pasted text into one structured recipe (schema below). Each ingredient gets a `source` and a `confidence` value. Quantities that were never stated are estimated and flagged.

Rules:
- Always return structured JSON from LLM calls and validate it against the Pydantic schema. Retry once on a validation failure.
- Delete downloaded video and audio files after processing.
- Platform access is fragile. On failure, show the error and the paste-text fallback rather than an empty or invented recipe. Never fabricate ingredients that are not supported by the caption, transcript, frames, or pasted text.

## Caching

- SQLite stores extraction results keyed by canonical URL, so repeated pastes return instantly, and ingredient-to-`fdcId` mappings.
- Demo reels' full results are also committed as JSON fixtures and loaded into the cache at startup. The demo must work even if the host wipes its disk on redeploy and even if TikTok or Instagram is unreachable.
- No user data is stored. There are still no accounts or saved recipes.

## Pricing

**Status: open.** The demo runs in Boston/Cambridge. Kroger's Developer API (Locations by ZIP, Products with per-store prices) was the original candidate, but Kroger has no stores in New England, so it cannot give local prices for the demo. Candidate sources need to be researched and verified for Boston-area coverage and access terms before one is chosen (see `docs/decisions.md` #1). Until then, pricing sits behind an adapter with a stub.

Requirements for whatever source is chosen:
- **Ingredient-to-product matching:** Map each ingredient to a purchasable product with a package size. For example, "2 cloves garlic" maps to "1 garlic bulb." Prefer the cheapest reasonable match and the smallest package that covers the needed amount.
- **Labels:** Each item's price carries a source tag, either `store price` or `estimate`. Totals (trip cost, per-meal cost) are always shown as approximate (e.g. "~$8.40"), because prices vary by store and change over time.
- If the source has no coverage for the user's location, fall back to clearly labeled estimated prices.

### Cost rules

- **Trip cost** is the sum of full package prices for items the user did *not* check off. It answers "what will I spend at the store?"
- **Per-meal cost** is the sum over *all* ingredients, including owned ones, of (amount used ÷ package size) × package price, divided by the number of servings. It answers "what does this meal actually cost?"
- Unit conversion (cups ↔ grams, cloves ↔ bulbs, and so on) lives in one shared utility module with tests.

## Nutrition

- Use USDA FoodData Central. Prefer the Foundation and SR Legacy data types for generic ingredients. Use Branded data only when the recipe names a specific product.
- Map each ingredient to an `fdcId` and cache the mapping.
- Convert every quantity to grams before calculating. Vague amounts ("a splash," "some garlic") get an LLM-estimated gram value with `estimated: true`.
- Report calories, protein, carbohydrates, and fat **per serving**. Use the reel's serving count if one is stated. Otherwise default to 2 and show that assumption in the UI.
- Mark macros as approximate whenever any input quantity is estimated.

## Beginner-friendly guidance

Every recipe's steps include all four of the following:

1. **Inline term definitions.** Jargon such as "deglaze," "fold," or "al dente" gets a short tooltip or parenthetical explanation.
2. **Doneness cues and timers.** Each cooking step says what "done" looks, smells, or feels like. Timed steps have a tappable timer.
3. **Food-safety callouts.** These cover safe internal temperatures for meat, poultry, and eggs, cross-contamination warnings, and leftover storage.
4. **Equipment swaps.** Assume a basic student kitchen: one skillet, one pot, a sheet pan, a knife, a cutting board, and a microwave. If a recipe calls for anything else (blender, stand mixer, air fryer, wok), offer a workaround using the basic kit.

Keep each step to one action. Use plain language and short sentences.

## Data schema

```json
{
  "source_url": "string",
  "title": "string",
  "servings": { "value": 2, "estimated": true },
  "ingredients": [
    {
      "id": "string",
      "name": "garlic",
      "quantity": 2,
      "unit": "clove",
      "grams": 6,
      "estimated": false,
      "source": "caption | transcript | frames | pasted | inferred",
      "confidence": 0.9,
      "owned": false,
      "product": {
        "store_id": "string",
        "product_name": "Garlic Bulb",
        "package_size_grams": 50,
        "package_price": 0.79,
        "price_type": "store price | estimate"
      },
      "fdc_id": 1104647
    }
  ],
  "steps": [
    {
      "order": 1,
      "instruction": "string",
      "timer_seconds": null,
      "doneness_cue": "string | null",
      "safety_note": "string | null",
      "equipment_swap": "string | null",
      "terms": [{ "term": "deglaze", "definition": "string" }]
    }
  ],
  "costs": { "trip_total": 0.0, "per_meal": 0.0, "currency": "USD", "approximate": true },
  "macros_per_serving": {
    "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0,
    "approximate": true
  }
}
```

## Definition of done for this sprint

The flow works end to end on the reels used in the live demo. Because "reliable" here means "works on whatever we demo live," do the following:

- Choose the demo reels (TikTok) in advance and run them through the full pipeline several times before demo day.
- Commit their results as fixtures. The demo should not depend on TikTok or Instagram being reachable that day.
- Include at least one reel whose caption lacks ingredients, so the audio and frame stages are shown working.

## Out of scope: do not build

- Built-in recipe library
- Fridge or pantry "what can I make" workflow
- Recommendations based on goals, likes, or dislikes
- Weekly spend tracking
- Direct ordering or checkout
- Native mobile app
- User accounts, login, or saved recipes

**Stretch goal (only after the core flow works):** show nearby stores on a map using store locations from the pricing source, if it provides them.

## Conventions

- Keep API keys in environment variables. Commit a `.env.example` and never commit real keys.
- Each external service (video platform, transcription, LLM, pricing, USDA) sits behind its own adapter module so it can be swapped or mocked.
- Write tests for unit conversion, cost math, and macro math, since these are deterministic and easy to get wrong.
- Log which extraction stage produced each ingredient, to make debugging bad extractions easier.
