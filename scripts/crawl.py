# -*- coding: utf-8 -*-
"""Crawl SJTU physics faculty profile pages (coarse stage)."""
import json, os, re, subprocess, sys, time

BASE = r"D:\USTC-AI\sjtu-physics-directory"
RAW = os.path.join(BASE, "data", "html")
os.makedirs(RAW, exist_ok=True)

SRC = os.path.join(BASE, "data", "roster.json")

CURL = r"C:\Windows\System32\curl.exe"


def fetch(url, out):
    if os.path.exists(out) and os.path.getsize(out) > 500:
        return True
    for attempt in range(3):
        r = subprocess.run([CURL, "-sL", "-m", "45", url, "-o", out,
                            "-w", "%{http_code}"], capture_output=True, text=True)
        code = (r.stdout or "").strip()
        if code == "200" and os.path.exists(out) and os.path.getsize(out) > 500:
            return True
        time.sleep(0.8)
    return False


def slug(url):
    m = re.search(r"/(jsml(?:_sp)?)/([^/]+)\.html", url)
    if m:
        return m.group(1) + "__" + m.group(2)
    return re.sub(r"[^a-zA-Z0-9]+", "_", url)[-80:]


def main():
    roster = json.load(open(SRC, encoding="utf-8"))
    targets = []
    for key, block in roster.items():
        if block["dept"].startswith("Teaching") or block["dept"].startswith("Visiting"):
            continue
        for rec in block["list"]:
            targets.append(rec)
    # de-dupe by profile url
    seen = {}
    for rec in targets:
        seen[rec["profile"]] = rec
    targets = list(seen.values())
    print(f"targets: {len(targets)}")

    manifest = []
    ok = 0
    for i, rec in enumerate(targets, 1):
        url = rec["profile"]
        out = os.path.join(RAW, slug(url) + ".html")
        good = fetch(url, out)
        manifest.append({"name": rec["name"], "profile_url": url,
                         "html": os.path.basename(out) if good else None,
                         "ok": good})
        if good:
            ok += 1
        if i % 20 == 0:
            print(f"  {i}/{len(targets)} ok={ok}")
    json.dump(manifest, open(os.path.join(BASE, "data", "manifest.json"), "w",
                             encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"done. fetched {ok}/{len(targets)}")


if __name__ == "__main__":
    main()
