#!/usr/bin/env python3
"""Transcribe a video/audio file with Groq Whisper and write word-level timings.

Usage: python3 -I transcribe_groq.py <input> <words.json> [--language tl] [--model whisper-large-v3]
Output JSON: {"language": "...", "text": "...", "words": [{"text","start","end"}], "segments": [...]}
Needs network access to api.groq.com. A key comes from GROQ_API_KEY or from a credential the
environment's proxy injects (then any placeholder value works).
"""
import argparse, json, os, subprocess, sys, tempfile

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("out")
    ap.add_argument("--language", default=None, help="ISO code to force, e.g. en, tl")
    ap.add_argument("--model", default="whisper-large-v3")
    a = ap.parse_args()
    try:
        from groq import Groq
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "groq"], check=True)
        from groq import Groq
    os.environ.setdefault("GROQ_API_KEY", "proxy-injected")
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.mp3")  # mp3 keeps uploads under Groq's size limit
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.input, "-ac", "1", "-ar", "16000", "-b:a", "48k", wav], check=True)
        kw = dict(model=a.model, response_format="verbose_json", timestamp_granularities=["word", "segment"])
        if a.language: kw["language"] = a.language
        with open(wav, "rb") as f:
            d = Groq().audio.transcriptions.create(file=f, **kw).model_dump()
    words, prev = [], 0.0
    for w in d.get("words") or []:
        t = w["word"].strip()
        if not t: continue
        s = max(float(w["start"]), prev); e = max(float(w["end"]), s + 0.06)
        words.append({"text": t, "start": round(s, 3), "end": round(e, 3)}); prev = s + 0.01
    # Whisper invents "Thank you." over trailing silence: drop a final segment that ends past the media.
    out = {"language": d.get("language"), "text": d.get("text", "").strip(), "words": words,
           "segments": [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in d.get("segments") or []]}
    json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"{len(words)} words, language={out['language']}")
    for s in out["segments"]: print(f"[{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")

if __name__ == "__main__":
    main()
