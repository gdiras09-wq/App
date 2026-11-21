# Scene library

Every template in `../templates/` is a HyperFrames sub-composition (1920×1080, opaque
background) built for a 3 s slot. Copy it into `compositions/`, rename the `data-composition-id`
and the timeline key to match its host, then edit the marked values. All animation is on a
paused GSAP timeline, deterministic.

| Template | Shows | Use when the speaker says… | Edit |
|---|---|---|---|
| `stat-counter.html` | A number that rolls from A to B over a scrolling ruler, kicker above | a year, an amount, a count ("back in 1453", "$250,000", "10,000 people") | `KICKER`, `FROM`, `TO`, `PREFIX`/`SUFFIX` |
| `gauge.html` | A chrome gauge whose needle sweeps to a value, big gradient % + word beside it | a percentage or a level ("close to 100% signal", "90% of people") | `VALUE` (0–100), `KICKER`, `WORD` |
| `clock-ring.html` | Alarm clock with a gradient progress ring drawing round, big number + unit | hours, time, deadlines, "every day" ("18 hours", "in 3 weeks") | `HOURS` (ring fraction = HOURS/24), `KICKER`, `UNIT` |
| `checklist.html` | Clipboard with numbered boxes that tick, big number + label | lists, steps, "three things" | `COUNT` (1–5), `LABEL`, `SUB` |
| `concept.html` | One hero word with a sub-line, plus an optional second word that slides in for contrast | a named idea or a contrast ("SIGNAL = the most urgent thing" then "vs NOISE") | `WORD`, `SUB`, `WORD2`, `SUB2` |

## Choosing

- Prefer a scene whose *motion* matches the sentence: growth → counter up, decline → counter
  down, "almost all" → gauge near 100, time → clock ring, steps → checklist ticking in step
  with the speaker naming them.
- Keep each scene on screen until the idea is finished being said (2–4 s), then cut back to the face.
- Vary types; repeat a type only with a different colour emphasis or layout side.
- Vertical (1080×1920): put the hero object in the top half and the text block under it;
  scale fonts ×1.3.

## Making a new scene type

Follow the same recipe so it matches: `#05060d` ground + radial glow, one hero object drawn with
CSS/SVG (metallic = `linear-gradient(#f4f6fb,#9aa3b8)` + inner shadow), reflection = the object
copied with `transform: scaleY(-1)` at 12% opacity under a fade mask, hero text right side,
gradient fill on the key value, one moving value. Durations: entrance 0.5–0.7 s `expo.out`,
value motion 0.8–1.4 s `power3.out`, hold, no exit tween (the cut does the exit).
