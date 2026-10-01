# -*- coding: utf-8 -*-
"""Parse SJTU physics profile pages into structured records."""
import json, os, re

BASE = r"D:\USTC-AI\sjtu-physics-directory"
RAW = os.path.join(BASE, "data", "html")

HONOR_KW = ("院士", "杰出青年", "优秀青年", "万人计划", "长江学者", "人才", "学者",
            "基金", "计划", "奖", "荣誉", "特聘", "讲席", "会士", "Fellow", "杰青",
            "海外", "领军", "拔尖", "高层次")
INST_RE = re.compile(r"^(?:.){1,20}(研究所|研究院|学系|系|中心|实验室|研究部|团队)$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://[^\s，,；;）)】]+")
PHONE_RE = re.compile(r"^(?:0?1[0-9]{8,10}|021[-\s]?\d{7,8}(?:-\d{1,5})?|\+?86[-\s]?\d{7,11})$")
ADDR_RE = re.compile(r"(室|楼|号|校区|路|院|邮编|地址|东川路|华山路)")
META_RE = re.compile(r"^(邮编|地址|电话|传真|Email|邮箱)[：: ]")

# headings that terminate a section
SECTION_HEADS = {
    "个人经历", "个人简介", "代表性论文著作", "代表性论文", "主要论文", "发表论文",
    "学术成果", "荣誉奖励", "科研项目", "学术兼职", "教学工作", "研究方向",
    "研究领域", "联系方式", "教育背景", "教育经历", "工作经历", "主要经历",
    "获奖情况", "承担项目", "科研经历", "主持", "在研", "已完成", "研究兴趣",
    "个人履历", "简历", "教育背景：", "工作经历：", "教育经历：", "研究方向：",
    "研究领域：", "主要荣誉", "承担科研项目", "代表性成果",
}
TITLE_TOKENS = ("教授", "副教授", "助理教授", "研究员", "副研究员", "助理研究员",
                "讲席", "特聘", "教轨", "长聘", "博士后", "讲师", "工程师",
                "高级实验师", "实验师", "院士", "荣誉", "Fellow")


def clean_html(path):
    h = open(path, encoding="utf-8", errors="replace").read()
    h = re.sub(r"<script.*?</script>", "", h, flags=re.S)
    h = re.sub(r"<style.*?</style>", "", h, flags=re.S)
    h = re.sub(r"<(br|/p|/div|/li|/h\d|/tr|/td)[^>]*>", "\n", h, flags=re.I)
    t = re.sub(r"<[^>]+>", "\n", h)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
         .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
         .replace("&ldquo;", "\u201c").replace("&rdquo;", "\u201d")
         .replace("&mdash;", "\u2014").replace("&ndash;", "\u2013"))
    lines = [re.sub(r"\s+", " ", l).strip() for l in t.split("\n")]
    return [l for l in lines if l]


def content_start(lines, name):
    occ = [i for i, l in enumerate(lines) if l == name]
    for i in occ:
        if i > 30:
            return i
    return occ[0] if occ else 0


def parse(path, name):
    lines = clean_html(path)
    s = content_start(lines, name)

    rec = {"name": name, "title": "", "honors": "", "institute": "",
           "research_directions": [], "phone": "", "address": "", "email": "",
           "homepage": "", "bio": "", "publications": []}

    # header: from name up to the first section heading (or 12 lines)
    hdr = [lines[s]]
    j = s + 1
    while j < len(lines) and lines[j] not in SECTION_HEADS and (j - s) <= 12:
        hdr.append(lines[j])
        j += 1
    hdr_end = j

    joined = "\n".join(hdr)
    em = EMAIL_RE.search(joined)
    if em:
        rec["email"] = em.group(0)
    for u in URL_RE.findall(joined):
        if "jaccount" in u or "/user/" in u:
            continue
        rec["homepage"] = u.rstrip(".")
        break

    seq = []
    for l in hdr[1:]:
        if l in SECTION_HEADS or l in ("教师名录",):
            continue
        if EMAIL_RE.search(l) or URL_RE.search(l):
            continue
        if PHONE_RE.match(l):
            rec["phone"] = l
            continue
        if META_RE.match(l):
            if not rec["address"]:
                rec["address"] = l
            continue
        seq.append(l)

    for l in seq:
        if not rec["title"] and len(l) <= 25 and any(t in l for t in TITLE_TOKENS):
            rec["title"] = l
            continue
        # honor/award lines: keyword + optional year -> honors (even if already set)
        if (any(k in l for k in HONOR_KW) and len(l) <= 140
                and (re.search(r"\d{4}\s*年?", l) or any(k in l for k in
                     ("院士", "学者", "人才", "基金", "计划", "奖", "讲席", "特聘")))):
            # avoid swallowing a research direction that merely contains '人才'
            if not re.search(r"(物理|化学|材料|光学|量子|天文|核|等离子)", l):
                rec["honors"] = (rec["honors"] + "；" + l) if rec["honors"] else l
                continue
        if INST_RE.search(l) and len(l) <= 30 and not rec["institute"]:
            rec["institute"] = l
            continue
        # addresses: always consume (never let them become a direction)
        if ADDR_RE.search(l) and len(l) <= 55:
            if not rec["address"]:
                rec["address"] = l
            continue
        if re.search(r"(ICP备|版权所有|Copyright|All Rights|微信公众号|微视频|新浪微博|扫一扫|关注我们)", l):
            continue
        if re.search(r"（at）|\(at\)|（dot）|\(dot\)|@", l):
            continue
        if len(l) <= 80 and not rec["research_directions"]:
            rec["research_directions"].append(l)

    # ---- bio: pick the longest CJK paragraph after the header ----
    pub_heads = {"代表性论文著作", "代表性论文", "主要论文", "发表论文", "学术成果"}
    cand = []
    for l in lines[hdr_end:]:
        if l in SECTION_HEADS:
            continue
        cjk = len(re.findall(r"[\u4e00-\u9fff]", l))
        if len(l) >= 60 and cjk >= 20:
            cand.append(l)
    if cand:
        # join up to first 3 longest-but-contiguous-ish paragraphs (take longest two)
        cand_sorted = sorted(cand, key=len, reverse=True)[:3]
        # keep original order of the selected ones
        sel = [x for x in cand if x in cand_sorted]
        rec["bio"] = " ".join(sel)[:5000]

    # ---- research directions: bullet list under '研究方向' if header lacked a direction ----
    for i, l in enumerate(lines):
        if l in ("研究方向", "研究领域", "研究兴趣") and i > 30:
            rds = []
            for m in range(i + 1, min(i + 12, len(lines))):
                if lines[m] in SECTION_HEADS or lines[m] in pub_heads:
                    break
                if 3 <= len(lines[m]) <= 60 and not re.match(r"^[0-9.、]+$", lines[m]):
                    rds.append(lines[m])
            if rds and (not rec["research_directions"] or len(rec["research_directions"][0]) < 6):
                rec["research_directions"] = rds[:6]
            break

    # ---- publications ----
    for i, l in enumerate(lines):
        if l in pub_heads:
            pubs = []
            for m in range(i + 1, min(i + 300, len(lines))):
                t = lines[m]
                if t in SECTION_HEADS and t not in pub_heads:
                    break
                if len(t) < 12:
                    continue
                if re.search(r"(Phys\.|Nature|Science|PRL|PRB|PR[A-Z]|APL|JHEP|"
                             r"ApJ|ApJL|MNRAS|arXiv|Commun\.|Adv\.|Nano|Opt\.|"
                             r"IEEE|Nucl\.|J\.|Rev\.|20\d\d)", t):
                    pubs.append(t)
                if len(pubs) >= 5:
                    break
            rec["publications"] = pubs
            break

    return rec


def main():
    status = json.load(open(os.path.join(BASE, "data", "manifest.json"), encoding="utf-8"))
    out = []
    for rec in status:
        if not rec["ok"]:
            continue
        parsed = parse(os.path.join(RAW, rec["html"]), rec["name"])
        parsed["profile_url"] = rec["profile_url"]
        out.append(parsed)
    json.dump(out, open(os.path.join(BASE, "data", "parsed.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"parsed {len(out)}")
    for k in ["title", "honors", "institute", "email", "homepage", "bio", "publications"]:
        print(f"  {k}: {sum(1 for r in out if r.get(k))}/{len(out)}")


if __name__ == "__main__":
    main()
