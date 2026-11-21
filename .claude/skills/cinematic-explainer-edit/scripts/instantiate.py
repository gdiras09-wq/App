#!/usr/bin/env python3
"""Copy a scene template into a project with unique ids, so one template can be used many times.

Usage: python3 -I instantiate.py <template.html> <out.html> --id gfx-fee [--replace OLD NEW ...]
- Sets data-composition-id and the window.__timelines key to --id (the host in index.html must use the same id).
- Prefixes every element id (and its #selectors / url(#..) / getElementById uses) with the instance id,
  so two copies of the same template never collide on one page.
- --replace OLD NEW does a literal text swap after that (OLD must occur), for copy and CFG values, e.g.
  --replace 'BACK IN HISTORY' 'ASSIGNMENT FEE' --replace 'from: 2026' 'from: 0'
"""
import argparse, re
ap = argparse.ArgumentParser()
ap.add_argument("template"); ap.add_argument("out"); ap.add_argument("--id", required=True)
ap.add_argument("--replace", nargs=2, action="append", default=[], metavar=("OLD", "NEW"))
a = ap.parse_args()
s = open(a.template).read()
old = re.search(r'data-composition-id="([^"]+)"', s).group(1)
s = s.replace(f'data-composition-id="{old}"', f'data-composition-id="{a.id}"')
s = s.replace(f'window.__timelines["{old}"]', f'window.__timelines["{a.id}"]')
p = re.sub(r"[^a-zA-Z0-9]", "", a.id)
ids = sorted(set(re.findall(r'(?<![\w-])id="([A-Za-z][\w-]*)"', s)) - {"root"}, key=len, reverse=True)
for i in ids:
    n = f"{p}-{i}"
    s = re.sub(rf'(?<![\w-])id="{re.escape(i)}"', f'id="{n}"', s)
    s = re.sub(rf'#{re.escape(i)}(?![\w-])', f'#{n}', s)
# ids built in script strings, e.g. 'id="cl-t' + i
for pre in sorted({m for m in re.findall(r"id=\"([a-z]+-[a-z]*)' \+", s)}):
    s = s.replace(f"id=\"{pre}' +", f"id=\"{p}-{pre}' +")
    s = s.replace(f'"#{pre}" +', f'"#{p}-{pre}" +')
for o, n in a.replace:
    if o not in s: raise SystemExit(f"--replace: text not found: {o!r}")
    s = s.replace(o, n)
open(a.out, "w").write(s)
print(f"{a.template} -> {a.out} as {a.id} ({len(ids)} ids prefixed)")
