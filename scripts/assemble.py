# -*- coding: utf-8 -*-
"""Assemble faculty.json (search_prof schema) from parsed records."""
import json, os, re
from datetime import datetime, timezone
import importlib.util

BASE = r"D:\USTC-AI\sjtu-physics-directory"

# load the HTML-aware publication parser
_spec = importlib.util.spec_from_file_location(
    "parse_pubs", os.path.join(BASE, "scripts", "parse_pubs.py"))
parse_pubs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parse_pubs)

SUBJECT_BY_INST = [
    ("天文", "天文学 / Astronomy"),
    ("凝聚态", "物理学 / Physics"),
    ("粒子", "物理学 / Physics"),
    ("核物理", "物理学 / Physics"),
    ("激光", "物理学 / Physics"),
    ("等离子体", "物理学 / Physics"),
    ("光学", "物理学 / Physics"),
    ("光子", "物理学 / Physics"),
    ("交叉科学", "物理学 / Physics"),
    ("维尔切克", "物理学 / Physics"),
    ("超快", "物理学 / Physics"),
]


def is_author_only(title):
    t = title.strip().rstrip("*# ")
    if re.fullmatch(r"(?:[A-Z]\.\s*){1,4}[A-Z]?[a-z]*", t):
        return True
    if re.search(r"et al", t) and len(t) < 40:
        return True
    words = t.split()
    if len(words) <= 4 and not re.search(r"\b(of|the|in|for|with|on|a|an|to|and)\b", t, re.I):
        if all(re.match(r"^[A-Z][A-Za-z.\-]*$", w) for w in words):
            return True
    return False


def slugify(s, i):
    base = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    if not base:
        base = "prof"
    return f"sjtu-physics-{base}-{i:04d}"


def split_dirs(raw):
    """Split a long direction string into 2-5 clean sub-directions."""
    out = []
    for d in raw:
        d = d.strip().lstrip("0123456789.、 ")
        if not d:
            continue
        # split on separators & newlines
        parts = re.split(r"[;；\n]|(?<=[a-z\)])\s*[，,]\s*|(?<=[。])\s+", d)
        for p in parts:
            p = p.strip().lstrip(".、 ")
            if p and p not in out:
                out.append(p)
    # cap
    return out[:6]


def derive_dirs_from_bio(bio):
    if not bio:
        return []
    pats = [
        r"(?:主要)?研究方向(?:为|是|：|:)?\s*([^。；]{4,120})",
        r"主要从事\s*([^。；]{4,120})",
        r"长期从事\s*([^。；]{4,120})",
        r"尤其是\s*([^。；]{4,120})",
        r"集中于\s*([^。；]{4,120})",
        r"研究(?:兴趣|领域)(?:为|是|：|:)?\s*([^。；]{4,120})",
    ]
    for pat in pats:
        m = re.search(pat, bio)
        if m:
            d = split_dirs([m.group(1)])
            if d:
                return d
    return []


VENUE_RE = re.compile(
    r"(Phys\. Rev\. Lett\.|Phys\. Rev\. [A-Z]|Phys\. Rev\.|Nature [A-Za-z]+|Nature|"
    r"Science|Sci\. Adv\.|Adv\. Mater\.|Adv\.|Nano Lett\.|Nano|Opt\. Lett\.|"
    r"Opt\. Express|Opt\.|Appl\. Phys\. Lett\.|Appl\.|JHEP|JCAP|Astrophys\. J\.|"
    r"ApJ|MNRAS|AJ|PRL|PRB|PRD|PRA|PRC|PRE|Commun\. Phys\.|Commun\.|"
    r"IEEE [A-Za-z. ]+|Nucl\. [A-Za-z. ]+|J\. [A-Za-z. ]+|Rev\. Mod\. Phys\.)")

# lines that are clearly prose (biography) rather than a citation
PROSE_BAD = re.compile(r"(年毕业于|获得博士|获博士|博士后|学位|导师|聘为|担任|主要从事|"
                       r"研究方向|特聘教授|讲席教授|出生于|留校|加入上海|"
                       r"工作经历|教育背景|主持|项目|基金委|课题|团队|发表论文|"
                       r"SCI|被引|篇)")


def looks_like_citation(s):
    if PROSE_BAD.search(s):
        return False
    # must have a venue OR a quoted title OR author-initial pattern with a year
    has_venue = bool(VENUE_RE.search(s))
    has_quoted = bool(re.search(r'[“"][^”"]{8,}[”"]', s))
    has_inits = bool(re.search(r"[A-Z][a-z]+,?\s+[A-Z]\.", s)) and bool(re.search(r"(19|20)\d{2}", s))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", s))
    if cjk > 6:
        return False
    return has_venue or has_quoted or has_inits


def parse_pub(s):
    s = re.sub(r"\s+", " ", s).strip().strip('"; “”')
    year = None
    ym = re.search(r"(19|20)\d{2}", s)
    if ym:
        year = int(ym.group(0))
    venue = ""
    vm = VENUE_RE.search(s)
    if vm:
        venue = vm.group(1).strip()
    # title: text before the first author-initial/comma pattern; fallback to first clause
    title = s
    cut = re.search(r"(?:,\s*)?[A-Z][a-z]*\.?\s*[A-Z]\.\s*,", s)
    if cut and cut.start() > 12:
        title = s[:cut.start()]
    else:
        title = s.split(",", 1)[0]
    title = title.strip().strip('"; “”')
    if len(title) > 220:
        title = title[:217] + "..."
    return {"title": title, "venue": venue, "year": year}


def main():
    parsed = json.load(open(os.path.join(BASE, "data", "parsed.json"), encoding="utf-8"))
    manifest = json.load(open(os.path.join(BASE, "data", "manifest.json"), encoding="utf-8"))
    by_url = {m["profile_url"]: m for m in manifest}
    HTMlDIR = os.path.join(BASE, "data", "html")
    roster = json.load(open(os.path.join(BASE, "data", "roster.json"), encoding="utf-8"))
    # map profile_url -> dept label
    url_dept = {}
    for key, block in roster.items():
        for rec in block["list"]:
            url_dept[rec["profile"]] = block["dept"]

    professors = []
    for i, r in enumerate(parsed):
        inst = r.get("institute", "")
        subject = "物理学 / Physics"
        for kw, subj in SUBJECT_BY_INST:
            if kw in inst:
                subject = subj
                break
        if "天文" in inst or "天文" in " ".join(r.get("research_directions", [])):
            subject = "天文学 / Astronomy"

        dirs = split_dirs(r.get("research_directions", []))
        if not dirs:
            dirs = derive_dirs_from_bio(r.get("bio", ""))
        # if still just one long blob, split on 、，
        if len(dirs) == 1 and len(dirs[0]) > 40:
            dirs = split_dirs([re.sub(r"[、，]", ";", dirs[0])])

        pubs = []
        m = by_url.get(r["profile_url"])
        if m and m.get("html"):
            html = open(os.path.join(HTMlDIR, m["html"]), encoding="utf-8",
                        errors="replace").read()
            pubs = parse_pubs.parse_publications(html)
        pubs = [p for p in pubs if p.get("title") and len(p["title"]) >= 10]
        pubs = [p for p in pubs if not is_author_only(p["title"])]
        pubs = pubs[:4]

        summary = r.get("bio", "").strip()
        if summary:
            summary = re.split(r"[。；]", summary)[0]
            if len(summary) > 160:
                summary = summary[:157] + "..."
        else:
            summary = "，".join(dirs[:3])

        dept = url_dept.get(r["profile_url"], "Department of Physics and Astronomy")
        if dept.startswith("Department of Physics and Astronomy (joint"):
            dept = "物理与天文学院 / 李政道研究所 (双聘)"

        focus = dirs[1:4] if len(dirs) > 1 else []

        rec = {
            "id": slugify(r["name"], i),
            "name": r["name"],
            "name_local": r["name"],
            "school": "上海交通大学 / Shanghai Jiao Tong University",
            "department": ("物理与天文学院 - " + inst) if inst else "物理与天文学院",
            "title": r.get("title", ""),
            "subject": subject,
            "research_directions": dirs,
            "focus_areas": focus,
            "summary": summary,
            "publications": pubs,
            "homepage": r.get("homepage", ""),
            "profile_url": r["profile_url"],
            "email": r.get("email", ""),
            "sources": [r["profile_url"]],
            "confidence": ("fine" if (pubs and r.get("homepage")) else "coarse"),
            "verified": True,
            "is_academician": ("院士" in (r.get("honors") or "")),
        }
        # honor / title enrichment
        if r.get("honors"):
            rec["honors"] = r["honors"]
        if r.get("phone"):
            rec["phone"] = r["phone"]
        if r.get("address"):
            rec["address"] = r["address"]
        professors.append(rec)

    doc = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "query": {
            "schools": ["上海交通大学 / Shanghai Jiao Tong University"],
            "departments": ["物理与天文学院", "李政道研究所 (TDLI)", "天文系"],
            "topics": ["物理学 / Physics", "天文学 / Astronomy"],
        },
        "professors": professors,
    }
    out = os.path.join(BASE, "data", "faculty.json")
    json.dump(doc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {out}: {len(professors)} professors")
    print("  fine:", sum(1 for p in professors if p["confidence"] == "fine"))
    print("  academicians:", sum(1 for p in professors if p["is_academician"]))
    print("  with homepage:", sum(1 for p in professors if p["homepage"]))
    print("  with email:", sum(1 for p in professors if p["email"]))
    print("  with pubs:", sum(1 for p in professors if p["publications"]))


if __name__ == "__main__":
    main()
