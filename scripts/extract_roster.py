# -*- coding: utf-8 -*-
"""Extract the SJTU physics faculty roster from the directory pages."""
import re, json, os, subprocess

BASE = r"D:\USTC-AI\sjtu-physics-directory"
RAW = os.path.join(BASE, "data", "rawhtml")
os.makedirs(RAW, exist_ok=True)
CURL = r"C:\Windows\System32\curl.exe"

PAGES = [
    ("jsml.html", "Department of Physics and Astronomy",
     "https://www.physics.sjtu.edu.cn/jsml.html"),
    ("jsml_sp.html", "Department of Physics and Astronomy (joint appointment)",
     "https://www.physics.sjtu.edu.cn/jsml_sp.html"),
    ("jsml_fwxz.html", "Visiting Scholars",
     "https://www.physics.sjtu.edu.cn/jsml_fwxz.html"),
    ("jfry.html", "Teaching/Research Support Staff",
     "https://www.physics.sjtu.edu.cn/jfry.html"),
]

BAD_URLS = {"https://www.physics.sjtu.edu.cn/jsml.html",
            "https://www.physics.sjtu.edu.cn/jsml_sp.html",
            "https://www.physics.sjtu.edu.cn/jsml_fwxz.html",
            "https://www.physics.sjtu.edu.cn/jfry.html",
            "https://www.physics.sjtu.edu.cn/lyys.html",
            "https://www.physics.sjtu.edu.cn/bhml.html",
            "https://www.physics.sjtu.edu.cn/jgsz.html",
            "https://www.physics.sjtu.edu.cn/szdw.html"}


def fetch(url, out):
    if os.path.exists(out) and os.path.getsize(out) > 500:
        return
    subprocess.run([CURL, "-sL", "-m", "60", url, "-o", out], check=False)


def main():
    out = {}
    for fname, dept, url in PAGES:
        p = os.path.join(RAW, fname)
        fetch(url, p)
        html = open(p, encoding="utf-8", errors="replace").read()
        links = re.findall(
            r'<li[^>]*>\s*<a href="(https://www\.physics\.sjtu\.edu\.cn/'
            r'jsml(?:_sp|_fwxz)?/[^"]*)"[^>]*>\s*([^<]+?)\s*</a>', html)
        seen = {}
        for u, n in links:
            if u in BAD_URLS:
                continue
            n = re.sub(r"\s+", " ", n).strip()
            if u not in seen:
                seen[u] = n
        out[fname] = {"dept": dept, "count": len(seen),
                      "list": [{"name": n, "profile": u} for u, n in seen.items()]}
        print(fname, dept, "->", len(seen))
    json.dump(out, open(os.path.join(BASE, "data", "roster.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print("total:", sum(v["count"] for v in out.values()))


if __name__ == "__main__":
    main()
