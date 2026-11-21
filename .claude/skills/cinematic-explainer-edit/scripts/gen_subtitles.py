#!/usr/bin/env python3
"""Build a HyperFrames subtitles sub-composition from word timings.

Usage:
  python3 -I gen_subtitles.py words.json compositions/subs.html
      [--width 1920 --height 1080] [--style explainer|bold] [--remap remap.json]
      [--duration SECONDS] [--emph word,word,...] [--bottom PX]

words.json: output of transcribe_groq.py ({"words":[{"text","start","end"}]}).
remap.json: list of [src_start, src_end, out_start, speed] spans describing how the edit moved
            source time (cuts and speed ramps). Words outside every span are dropped.
Styles:
  explainer  small sentence-case line, spoken words white, upcoming words dim (reference look)
  bold       big uppercase outlined 2-3 word captions, emphasis words yellow (shorts look)
The host in index.html must use data-composition-id="subs" and data-track-kind="captions".
"""
import argparse, html, json

def load_words(path, remap):
    ws = json.load(open(path))["words"]
    out = []
    for w in ws:
        t = w["text"].strip()
        if not t: continue
        s, e = w["start"], w["end"]
        if remap:
            m = None
            for a, b, o, sp in remap:
                if a <= s < b:
                    m = (o + (s - a) / sp, o + (min(e, b) - a) / sp); break
            if m is None: continue
            s, e = m
        # Whisper sometimes glues an article to a number ("a $19,000") or splits "19 000".
        if " " in t:
            parts = t.split(); step = (e - s) / len(parts)
            for i, p in enumerate(parts): out.append([p, s + i * step, s + (i + 1) * step])
            continue
        if out and t.isdigit() and len(t) == 3 and out[-1][0].replace("$", "").isdigit() and s - out[-1][2] < 0.3:
            out[-1][0] += "," + t; out[-1][2] = e; continue
        out.append([t, s, e])
    prev = 0.12
    for w in out:
        w[1] = max(w[1], prev); w[2] = max(w[2], w[1] + 0.08); prev = w[1] + 0.02
    return out

def group(words, max_words, max_chars):
    gs, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        chars = sum(len(x[0]) + 1 for x in cur)
        if (len(cur) >= max_words or chars >= max_chars or w[0][-1] in ".?!," or nxt is None
                or nxt[1] - w[2] >= 0.3):
            gs.append(cur); cur = []
    return gs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words"); ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--style", choices=["explainer", "bold"], default="explainer")
    ap.add_argument("--remap"); ap.add_argument("--duration", type=float)
    ap.add_argument("--emph", default=""); ap.add_argument("--bottom", type=int)
    a = ap.parse_args()
    remap = json.load(open(a.remap)) if a.remap else None
    words = load_words(a.words, remap)
    end_all = a.duration or (words[-1][2] + 0.5 if words else 1)
    W, H = a.width, a.height; portrait = H > W
    bold = a.style == "bold"
    groups = group(words, 3 if bold else 7, 18 if bold else (34 if portrait else 46))
    emph = {x.strip().lower() for x in a.emph.split(",") if x.strip()}
    if bold:
        fs = 80 if portrait else 72; maxw = int(W * (0.78 if portrait else 0.7))
        bottom = a.bottom if a.bottom is not None else (int(H * 0.36) if portrait else 120)
        text_css = ('font-family:"Montserrat",sans-serif;font-weight:900;text-transform:uppercase;color:#fff;'
                    '-webkit-text-stroke:10px #000;paint-order:stroke fill;text-shadow:0 6px 0 rgba(0,0,0,.55),0 10px 26px rgba(0,0,0,.45);'
                    'line-height:1.02;')
    else:
        fs = 42 if portrait else 30; maxw = int(W * (0.8 if portrait else 0.6))
        bottom = a.bottom if a.bottom is not None else (int(H * 0.3) if portrait else 56)
        text_css = ('font-family:"Inter",sans-serif;font-weight:500;color:#fff;letter-spacing:.005em;'
                    'text-shadow:0 2px 12px rgba(0,0,0,.85),0 1px 2px rgba(0,0,0,.9);line-height:1.25;')
    rows, js = [], []
    for gi, g in enumerate(groups):
        gs = max(0.1, g[0][1] - 0.05)
        nxt = groups[gi + 1][0][1] - 0.05 if gi + 1 < len(groups) else end_all
        ge = min(nxt, g[-1][2] + (0.45 if bold else 0.7), end_all)
        if ge - gs < 0.25: ge = min(gs + 0.25, end_all)
        spans = []
        for wi, (t, s, e) in enumerate(g):
            key = t.lower().strip(".,?!\"'")
            txt = html.escape(t.upper().rstrip(",.") if bold else t)
            cls = "w e" if key in emph else "w"
            spans.append(f'<span id="sb-{gi}-{wi}" class="{cls}">{txt}</span>')
            js.append(f"say('#sb-{gi}-{wi}',{s:.3f},{min(e, ge):.3f});")
        rows.append(f'    <div id="sb-{gi}" class="clip sb" data-start="{gs:.3f}" data-duration="{ge - gs:.3f}" data-track-index="0">'
                    f'<div id="sb-{gi}i" class="in">{" ".join(spans)}</div></div>')
        js.append(f"enter('#sb-{gi}i',{gs:.3f});")
    left = (W - maxw) // 2
    doc = f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; }}
    .sb {{ position: absolute; left: {left}px; width: {maxw}px; bottom: {bottom}px; height: {int(fs * 2.6)}px; overflow: visible;
          display: flex; align-items: flex-end; justify-content: center; text-align: center; }}
    .in {{ font-size: {fs}px; {text_css} }}
    .w {{ display: inline-block; margin: 0 {".14em" if bold else ".02em"}; }}
  </style>
  <div id="root" data-composition-id="subs" data-width="{W}" data-height="{H}">
{chr(10).join(rows)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    const BOLD = {str(bold).lower()};
    const HI = "#FFD21F";
    if (BOLD) document.querySelectorAll("#root .in").forEach(el => {{
      const f = window.__hyperframes && window.__hyperframes.fitTextFontSize;
      const r = f ? f(el.textContent, {{ fontFamily: "Montserrat", fontWeight: 900, maxWidth: {maxw - 20} }}) : null;
      if (r && r.fontSize) el.style.fontSize = Math.min(r.fontSize, {fs}) + "px";
    }});
    function enter(sel, at) {{
      if (BOLD) tl.fromTo(sel, {{ scale: 0.8, y: 20 }}, {{ scale: 1, y: 0, duration: 0.18, ease: "back.out(2.2)" }}, at);
      else tl.fromTo(sel, {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.2, ease: "power2.out" }}, at);
    }}
    function say(sel, s, e) {{
      const em = document.querySelector(sel).classList.contains("e");
      if (BOLD) {{
        tl.fromTo(sel, {{ color: "#ffffff", scale: 1 }}, {{ color: em ? HI : "#ffffff", scale: em ? 1.15 : 1.06, duration: 0.07 }}, s);
        tl.to(sel, {{ scale: 1, duration: 0.12, ease: "power2.out" }}, Math.max(e, s + 0.1));
      }} else {{
        tl.fromTo(sel, {{ color: "rgba(255,255,255,0.38)" }}, {{ color: em ? "#c9a8ff" : "#ffffff", duration: 0.12, ease: "none" }}, s);
      }}
    }}
    {(chr(10) + "    ").join(js)}
    window.__timelines["subs"] = tl;
  </script>
</template>
'''
    open(a.out, "w").write(doc)
    print(f"{len(words)} words in {len(groups)} groups -> {a.out}")

if __name__ == "__main__":
    main()
