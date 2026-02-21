# NEXT STEPS TOMORROW - ROUND 2

## Current state

- Round 2 result: `NO VIABLE (de momento)`.
- No candidate passed minimum robustness/power gates.
- Pipeline integrity is not the issue (`PIPELINE_BUG_SUSPECTED=NO`).

## Plan (3-5 tasks)

1. Build a **new candidate batch with explicit power target**:
   - Keep only 2 families.
   - Enforce expected sample target before run (`target >= 100 trades` on 60k-bars subset).
   - Avoid candidates likely to generate <20 trades.

2. Add a **pre-screen step** in discovery runner:
   - Fast dry check to estimate expected signal count (rough heuristic from recent year or micro-pass).
   - Skip configs with clearly non-operable frequency.

3. Run one **frequency-first discovery batch**:
   - Focus on simple structures that naturally increase sample size.
   - Keep same falsification stack (expectancy audit + posthoc + temporal) unchanged.

4. If again no candidates pass:
   - Stop incremental tweaking of current families.
   - Pivot to a narrower redesign brief with fewer assumptions and one family at a time.

## What to follow next

- Follow: only configs that can plausibly produce robust sample size.
- Do not follow: ultra-low-trade winners even if PF looks high.

## What not to touch yet

- Do not modify `docs/RANGE_EDGE_VALIDATION.md`.
- Do not widen into large grids or multi-family tuning.
- Do not add ad-hoc hour filters to "force" positive metrics.
