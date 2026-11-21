#!/usr/bin/env python3
"""Reframe footage to a new aspect while following the speaker's face.

Usage: python3 -I face_crop.py <in.mp4> <out.mp4> [--aspect 9:16] [--region x,y,w,h]
         [--size 1080x1920] [--smooth 0.8] [--no-grade]
--region crops a fixed box first (e.g. a facecam inside a screen recording), then tracks inside it.
Video only (no audio) in the output; mux the audio back with FFmpeg.
"""
import argparse, json, subprocess, sys
def need(mod, pkg):
    try: return __import__(mod)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True); return __import__(mod)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--aspect", default="9:16"); ap.add_argument("--size", default=None)
    ap.add_argument("--region", default=None); ap.add_argument("--smooth", type=float, default=0.8)
    ap.add_argument("--no-grade", action="store_true")
    a = ap.parse_args()
    cv2 = need("cv2", "opencv-python-headless<5"); np = need("numpy", "numpy")
    cap = cv2.VideoCapture(a.inp); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    rx, ry, rw, rh = tuple(map(int, a.region.split(","))) if a.region else (0, 0, W, H)
    aw, ah = map(float, a.aspect.split(":"))
    if rw / rh > aw / ah: cw, ch = int(rh * aw / ah) // 2 * 2, rh // 2 * 2
    else: cw, ch = rw // 2 * 2, int(rw * ah / aw) // 2 * 2
    ow, oh = map(int, a.size.split("x")) if a.size else ((1080, 1920) if ah > aw else (1920, 1080) if aw > ah else (1080, 1080))
    fr = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    pr = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    xs, ys, ts, n = [], [], [], 0
    step = max(1, int(round(fps / 5)))
    while True:
        ok, f = cap.read()
        if not ok: break
        if n % step == 0:
            g = cv2.equalizeHist(cv2.cvtColor(f[ry:ry+rh, rx:rx+rw], cv2.COLOR_BGR2GRAY))
            m = max(40, rh // 12)
            det = list(fr.detectMultiScale(g, 1.1, 5, minSize=(m, m)))
            if not det:
                det = list(pr.detectMultiScale(g, 1.1, 5, minSize=(m, m)))
                det += [(rw - x - w, y, w, h) for (x, y, w, h) in pr.detectMultiScale(cv2.flip(g, 1), 1.1, 5, minSize=(m, m))]
            if det:
                x, y, w, h = max(det, key=lambda r: r[2] * r[3])
                ts.append(n / fps); xs.append(x + w / 2); ys.append(y + h * 0.75)
        n += 1
    if not ts: ts, xs, ys = [0.0], [rw / 2], [rh / 2]
    print(f"face found in {len(ts)} of {n // step} samples", file=sys.stderr)
    t = np.arange(n) / fps
    k = max(1, int(fps * a.smooth))
    sm = lambda v: np.convolve(np.pad(np.interp(t, ts, v), k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
    lx = np.clip(sm(xs) - cw / 2, 0, rw - cw); ly = np.clip(sm(ys) - ch / 2, 0, rh - ch)
    vf = f"scale={ow}:{oh}:flags=lanczos,unsharp=5:5:0.5"
    if not a.no_grade:
        vf += ",eq=contrast=1.1:saturation=1.05:gamma=0.96,colorbalance=bs=0.05:rh=0.03,vignette=PI/4.5"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{cw}x{ch}",
                          "-r", str(fps), "-i", "-", "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                          "-g", str(int(round(fps))), "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(a.inp); i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        x, y = rx + int(lx[min(i, n - 1)]), ry + int(ly[min(i, n - 1)])
        p.stdin.write(np.ascontiguousarray(f[y:y+ch, x:x+cw]).tobytes()); i += 1
    p.stdin.close(); p.wait()
    print(json.dumps({"frames": i, "crop": [cw, ch], "out": [ow, oh]}))

if __name__ == "__main__":
    main()
