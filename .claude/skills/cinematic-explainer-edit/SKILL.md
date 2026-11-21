---
name: cinematic-explainer-edit
description: >-
  Edit raw talking-head / interview / podcast footage into a cinematic "explainer" short like premium TikTok/Reels/Shorts edits: dark graded A-roll intercut every 2-4 s with full-screen navy-purple motion-graphic scenes (big gradient numbers, gauges, clocks with progress rings, checklists, timelines, phone mockups) that illustrate exactly what the speaker says, plus small karaoke subtitles. Uses Groq (transcription), FFmpeg (cuts, crops, grade, audio) and HyperFrames (graphics + render). Use this whenever the user uploads a raw clip and asks to "edit it like this", "make it look pro/cinematic", "add motion graphics", "edit like the reference", "explainer style", "edit with opus", or wants a podcast/interview turned into a short — even if they don't name the style.
---

# Cinematic Explainer Edit

Turn a raw talking-head clip into a short where the speaker's key ideas become full-screen
motion-graphic "cutaways". The look: calm, premium, dark; the viewer *sees* every number and
concept the moment it is said.

## The look (match this)

| Element | Spec |
|---|---|
| Canvas | 1920×1080, 30 fps by default. 1080×1920 only when the user asks for vertical (then stack the same scenes vertically). |
| A-roll | Speaker footage, dark cinematic grade (contrast up, slight teal shadows, warm skin), strong vignette, rounded nothing — full frame. |
| B-roll scenes | Full-frame background `#05060d` with a soft radial glow (`#1b2a6b` → transparent, a hint of `#5b2a86`). One hero object, centred-left; hero text right. Faint floor reflection under the object. |
| Hero text | Huge heavy sans (Inter/Montserrat 900), white, or the accent gradient `linear-gradient(90deg,#c86bff,#6f7bff,#4fa3ff)` as text fill on the key number/word. |
| Kicker | Small uppercase above the hero, letter-spacing .3em, `#9fb0d8`, ~22 px at 1080p ("BACK IN HISTORY", "CLOSE TO", "AWAKE"). |
| Sub-line | Small sentence case under the hero, `#b8c2dd` ("= the most urgent thing", "to get done"). |
| Subtitles | Bottom centre, sentence case (not uppercase), ~30 px at 1080p, no outline, soft shadow. Words already spoken are white, upcoming words `rgba(255,255,255,.38)`. One short phrase at a time. |
| Rhythm | A new shot every 2–4 s. About half the runtime is graphics. Never two graphics scenes of the same type back to back. |
| Motion | Values *move*: counters roll, needles sweep, rings draw, checkboxes tick, timelines scroll. Arrive with `expo.out` (0.4–0.7 s), leave fast. Scene changes: blur-swap or slight push (scale 1.04→1). No bouncy UI. |
| Sound | Soft whoosh on each cut into a graphic, tick/pop when a value lands, one impact on the biggest number. Music bed only if one is available (~0.12 volume under voice). |

Honesty rule: graphics illustrate only what the speaker actually says. A gauge at "100% signal"
is fine because he said it; a fake app screenshot, invented statistic or real brand UI is not.

## Workflow

Paths below: `$SK` = this skill's folder. Work in a scratch project folder; put the final MP4
where the user can open it (e.g. `<repo>/edits/`).

### 1. Inspect
```bash
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height,r_frame_rate -of compact in.mp4
ffmpeg -v error -i in.mp4 -vf "fps=1/3,scale=320:-1,tile=5x4" -frames:v 1 sheet.jpg   # look at it
```
Note: aspect, where the face is, whether there are burned-in captions, length.

### 2. Transcribe (Groq, word timings)
```bash
python3 -I $SK/scripts/transcribe_groq.py in.mp4 words.json
```
Needs Groq access (a saved network credential for api.groq.com, or `GROQ_API_KEY`). If the
request is blocked, ask the user for a Groq key via the secure credential form — never paste
keys in chat. Read the transcript: it's the edit's script. Keep the original language
(Tagalog/Taglish stays as spoken).

### 3. Plan the beats (write `PLAN.md` before building)
Go through the transcript and pick 5–8 **anchor words**: numbers, durations, percentages,
years, lists ("three things"), and named concepts ("signal vs noise"). Each becomes one
graphics scene starting ~0.1 s before its anchor word and lasting 2–4 s. Between them, A-roll.
Pick the scene type from `references/scenes.md` that best *shows* the idea. Write the table:

| start | end | shot | anchor words | scene / content |

Cut dead air: gaps between words > 0.35 s shrink to ~0.12 s (use the word timings), and drop
false starts if timings are clean. Keep the speech natural.

### 4. Prepare the A-roll (FFmpeg)
- Same aspect as output: grade + vignette:
  `-vf "eq=contrast=1.1:saturation=1.05:gamma=0.96,colorbalance=bs=0.05:rh=0.03,vignette=PI/4.5"`
- Needs reframing (landscape → vertical, or a small facecam in a screen recording):
  `python3 -I $SK/scripts/face_crop.py in.mp4 out.mp4 --aspect 9:16` tracks the face and keeps
  it centred (`--region x,y,w,h` to crop a facecam box first).
- Audio: `highpass=f=80,acompressor=threshold=-20dB:ratio=3,loudnorm=I=-16:TP=-1.5`, 48 kHz.
- Encode `-g 30` (keyframe every second) so HyperFrames can seek it.
- Silence cuts / joins: trim + concat with matching audio; then shift your word timings by
  the same offsets (keep a remap function — subtitles must stay in sync).

### 5. Build in HyperFrames
Load the `hyperframes` skill first (it installs the package and explains the CLI and the
render contract; follow it). Then:
- `index.html` (root, 1920×1080, duration = A-roll length): the A-roll `<video data-has-audio="true">`
  inside a wrapper (`#cam`) for punch-ins; one host per graphics scene with
  `data-track-kind="graphics"`; one captions host; `<audio>` SFX clips with ids.
- Graphics scenes: start from `templates/` with `python3 -I $SK/scripts/instantiate.py <template> compositions/<id>.html --id <id> --replace OLD NEW ...`
  (it makes every element id unique, so one template can be used several times; the host id must match `--id`).
  Each template is a complete sub-composition with an opaque background, so while it plays it
  *is* the shot (cutaway). See `references/scenes.md` for what each template shows.
- Subtitles: `python3 -I $SK/scripts/gen_subtitles.py words.json compositions/subs.html --width 1920 --height 1080`
  (add `--remap remap.json` if you cut the audio). Style `explainer` (default) is the
  grey→white sentence style; `--style bold` gives big uppercase outlined shorts captions.
- Punch-ins on A-roll: `tl.set("#cam",{scale:1.08},t)` hard cuts on emphasis words, back to 1
  on the next sentence; a slow 1.00→1.04 push across a long A-roll shot.
- SFX: bundled with HyperFrames media-use (`.agents/skills/media-use/audio/assets/sfx/`):
  `whoosh`, `whoosh-short`, `pop`, `click-soft`, `impact-bass-1`, `riser`. Measure each file's
  peak and start it so the peak lands one frame after the visual hit. Volume 0.3–0.5.

### 6. Check, look, render
```bash
npx hyperframes check --json        # fix every error (overlaps, safe zones, unread lines)
npx hyperframes snapshot --at <one time inside each scene> --no-end -o snaps
```
Look at the snapshots yourself: hero text readable, nothing over the face, subtitles not on
top of a graphic's text. Then render `-q delivery`, and verify the file:
duration, resolution, loudness (`ffmpeg -i out.mp4 -af ebur128=peak=true -f null -` → about
−16 to −14 LUFS, peak ≤ −1 dB), and a 5-frame contact sheet.

### 7. Deliver
Send the MP4. Summarise in plain words: which moments got which graphic, what was cut, what
is missing (e.g. no music without a track), and offer 1–2 tweaks.

## Pitfalls learned the hard way
- A white flash clip that relies on a tween at local time 0 can render as a solid white hold — avoid flash frames; use a blur-swap.
- Text columns offset to dodge platform UI look off-centre; keep text centred and narrow instead.
- `fitTextFontSize` + scaled emphasis words: give words a margin (`.15em`) or they touch.
- Whisper merges tokens like `a $19,000` and splits `19 000` — normalise before building groups.
- Footage under 1080p gets soft when cropped to vertical: say so in the delivery note.
