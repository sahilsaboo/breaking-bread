"""Guidance step: beginner-friendly cooking steps for a structured recipe.

Every recipe's steps follow the four rules in docs/technical-spec.md:
term definitions, doneness cues and timers, food-safety callouts, and
equipment swaps for a basic student kitchen.
"""

import json

from pydantic import BaseModel, Field

from app.adapters import claude
from app.adapters.transcribe import Segment
from app.models import Recipe, Step, Term


class DraftTerm(BaseModel):
    term: str = Field(description="Cooking word exactly as it appears in the instruction")
    definition: str = Field(description="Plain-language meaning, one short sentence")


class DraftStep(BaseModel):
    instruction: str
    timer_seconds: int | None = Field(description="Seconds to time this step, or null if it isn't timed")
    doneness_cue: str | None = Field(description="What 'done' looks, smells, or feels like; null if not a cooking step")
    safety_note: str | None
    equipment_swap: str | None
    terms: list[DraftTerm]
    video_start_seconds: float | None = Field(description="When this step starts in the video, from the transcript times; null if unknown")
    video_end_seconds: float | None


class DraftGuidance(BaseModel):
    steps: list[DraftStep]


SYSTEM = """You write cooking steps for college students who have never cooked before.

Write the steps to make the recipe you're given, from the start (washing and prepping) to serving.
Follow how the video makes the dish; fill gaps the video skips, but use only the listed ingredients.

Every step:
- Does one action. Plain words, short sentences, no assumed kitchen knowledge.
- Defines cooking jargon (deglaze, fold, al dente, simmer, ...) in `terms`. Each term must
  appear word for word in that step's instruction.
- If it cooks something: says what "done" looks, smells, or feels like (doneness_cue), and
  gives timer_seconds when the step takes a set time.
- Adds a safety_note for raw meat, poultry, eggs, or fish (safe internal temperatures in °F,
  washing hands and boards to avoid cross-contamination), hot oil, and sharp knives where it matters.
  The last step covers storing leftovers when the dish keeps.
- Assumes a basic student kitchen: one skillet, one pot, a sheet pan, a knife, a cutting board,
  and a microwave. If the recipe needs anything else (blender, stand mixer, air fryer, wok,
  colander, whisk, ...), give a workaround with the basic kit in equipment_swap.

Video timing: when a transcript with [start-end] times is given, set video_start_seconds and
video_end_seconds to the part of the video that shows each step. Leave them null for steps the
video doesn't show, and always null when there is no transcript."""


def _transcript_lines(segments: list[Segment]) -> str:
    return "\n".join(f"[{s.start:.1f}-{s.end:.1f}] {s.text}" for s in segments)


def build_prompt(recipe: Recipe, *, caption: str | None, segments: list[Segment] | None, pasted: str | None) -> str:
    recipe_json = json.dumps(
        {
            "title": recipe.title,
            "servings": recipe.servings.value,
            "ingredients": [
                {"name": i.name, "quantity": i.quantity, "unit": i.unit, "grams": i.grams} for i in recipe.ingredients
            ],
        },
        ensure_ascii=False,
    )
    parts = [f"<recipe>\n{recipe_json}\n</recipe>"]
    if caption:
        parts.append(f"<caption>\n{caption}\n</caption>")
    if segments:
        parts.append(f"<transcript>\n{_transcript_lines(segments)}\n</transcript>")
    if pasted:
        parts.append(f"<pasted_text>\n{pasted}\n</pasted_text>")
    return "\n\n".join(parts)


def write_steps(
    recipe: Recipe,
    *,
    caption: str | None = None,
    segments: list[Segment] | None = None,
    pasted: str | None = None,
    video_duration: float | None = None,
) -> list[Step]:
    draft = claude.ask(
        system=SYSTEM,
        prompt=build_prompt(recipe, caption=caption, segments=segments, pasted=pasted),
        output=DraftGuidance,
        effort="medium",
    )
    return to_steps(draft, has_timing=bool(segments), video_duration=video_duration)


def to_steps(draft: DraftGuidance, *, has_timing: bool, video_duration: float | None) -> list[Step]:
    steps = []
    for n, s in enumerate(draft.steps, start=1):
        start, end = (s.video_start_seconds, s.video_end_seconds) if has_timing else (None, None)
        # Drop timestamps that can't be right rather than send the video somewhere random.
        if start is not None and (start < 0 or (video_duration and start >= video_duration)):
            start, end = None, None
        if start is not None and end is not None and end <= start:
            end = None
        if end is not None and video_duration:
            end = min(end, video_duration)

        lower = s.instruction.lower()
        steps.append(
            Step(
                order=n,
                instruction=s.instruction.strip(),
                timer_seconds=s.timer_seconds if s.timer_seconds and s.timer_seconds > 0 else None,
                doneness_cue=s.doneness_cue or None,
                safety_note=s.safety_note or None,
                equipment_swap=s.equipment_swap or None,
                # The UI highlights terms by finding them in the instruction text.
                terms=[Term(term=t.term, definition=t.definition) for t in s.terms if t.term.lower() in lower],
                video_start_seconds=start,
                video_end_seconds=end if start is not None else None,
            )
        )
    return steps
