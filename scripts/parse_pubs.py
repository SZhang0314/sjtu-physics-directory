# -*- coding: utf-8 -*-
"""Extract representative publications from an SJTU profile HTML page."""
import re

VENUE_RE = re.compile(
    r"(Phys\. Rev\. Lett\.|Phys\. Rev\. [A-Z]|Phys\. Rev\.|Nature [A-Za-z]+|Nature|"
    r"Science|Sci\. Adv\.|Adv\. Mater\.|Adv\.|Nano Lett\.|Nano [A-Za-z]*|Opt\. Lett\.|"
    r"Opt\. Express|Opt\.|Appl\. Phys\. Lett\.|Appl\.|JHEP|JCAP|J\. Cosmol\.|"
    r"Astrophys\. J\.|ApJ|ApJL|MNRAS|Astron\. J\.|AJ|PRL|PRB|PRD|PRA|PRC|PRE|PRX|"
    r"Commun\. Phys\.|Commun\.|IEEE [A-Za-z. ]+|Nucl\. [A-Za-z. ]+|"
    r"J\. [A-Za-z. ]+|Rev\. Mod\. Phys\.|New J\. Phys\.|EPL|EPJC|Cell|PNAS)")


def strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
         .replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
         .replace("&ldquo;", "\u201c").replace("&rdquo;", "\u201d"))
    return re.sub(r"\s+", " ", s).strip()


def clean_title(t):
    t = t.strip().strip(",;，；. “”\"")
    t = re.sub(r"\s*[,;]\s*$", "", t)
    # strip leading author remnant: "and Xxx Yyy. Title" / "Xxx Yyy. Title"
    t = re.sub(r"^(?:and\s+)?[A-Z][A-Za-z\-]+(?:\s+[A-Z][A-Za-z\-]*){0,3}"
               r"\s*(?:\*|\.)\s+(?=[A-Z])", "", t)
    t = re.sub(r"^(?:and\s+)?[A-Z][A-Za-z\-]+\s+[A-Z][A-Za-z\-]+,?\s+(?=[A-Z][a-z])", "", t)
    # if the title still leads with an author list ending in a period, drop it
    m = re.search(r"^(?:[A-Z][A-Za-z\-]+\s+){0,4}"
                  r"(?:[A-Z][A-Za-z\-]+\s+){0,1}"
                  r"(?:[A-Z][A-Za-z\-]+(?:\s+[A-Z][A-Za-z\-]*){0,3}"
                  r"(?:,|\sand\s)[^.]{0,60})\.\s+", t)
    if m and m.end() < len(t) - 12 and len(re.findall(r"\b[A-Z]\.", t[:m.end()])) == 0:
        t = t[m.end():]
    # cut off a trailing venue/year tail: ". Venue ..., (year)"
    t = re.sub(r"\.\s+[A-Z][A-Za-z].*$", "", t) if re.search(
        r"\.\s+(Adv|Phys|Opt|Appl|Nano|Quantum|ACS|Nature|Science|IEEE|J\b|"
        r"Commun|New|Rev)", t) else t
    t = re.sub(r",?\s*\(?\s*(?:19|20)\d{2}\s*\)?\s*\.?\s*$", "", t)
    # strip a trailing author name: " ... Title M. Shu" / " ... Title H. Huang"
    t = re.sub(r"\s+[A-Z]\.\s*[A-Z][a-z]+(?:\s+[A-Z]\.\s*[A-Z][a-z]+)?\s*$", "", t)
    t = re.sub(r"\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s*$", "", t) if (
        re.search(r"[a-z]{4,}\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s*$", t)) else t
    return t.strip().rstrip(".,;，；")


def looks_like_author_list(t):
    """Heuristic: many comma-separated short tokens with initials => author list."""
    tokens = [x.strip() for x in re.split(r"[,;]", t) if x.strip()]
    if len(tokens) < 5:
        return False
    short = sum(1 for x in tokens if len(x) <= 18)
    has_init = sum(1 for x in tokens if re.search(r"\b[A-Z]\.?\s*[A-Z]?\.?\b", x))
    return short >= len(tokens) * 0.7 and has_init >= len(tokens) * 0.3


TITLE_WORD = re.compile(r"\b(of|the|in|for|with|on|and|by|from|to|a|an|via|"
                        r"using|based|effect|study|quantum|physics|dynamics|"
                        r"properties|structure|model|theory)\b", re.I)


def is_author_token(p):
    p = p.strip()
    if not p:
        return False
    if p.endswith("*"):  # corresponding-author marker
        return True
    if re.search(r"\b[A-Z]\.", p):  # initials
        return True
    if re.search(r"\band\b", p) and len(p) <= 30 and re.match(r"^[A-Z]", p):
        return True
    if re.match(r"^[A-Z][a-zA-Z\-]+(\s+[A-Z][a-zA-Z\-]*){1,3}$", p) and len(p) <= 26:
        return True
    return False


def extract_title_from_head(head):
    """head = text before the venue with no quotes. Return best title guess."""
    head = head.strip().rstrip(",;，；. ")
    parts = [x.strip() for x in re.split(r"[,;，]", head) if x.strip()]
    # find first non-author token of decent length -> title start
    start = 0
    for i, p in enumerate(parts):
        if not is_author_token(p) and len(p) >= 16:
            start = i
            break
    title_parts = []
    for p in parts[start:]:
        if title_parts and is_author_token(p):
            break
        title_parts.append(p)
    title = ", ".join(title_parts).strip().rstrip("* ")
    return title


def parse_publications(html):
    # collect all item blocks
    items = re.findall(r'<div class="ab_nr ab_nrs">(.*?)</div>\s*</div>', html, flags=re.S)
    best = []
    for it in items:
        lis = re.findall(r"<li[^>]*>(.*?)</li>", it, flags=re.S)
        if len(lis) > len(best):
            best = lis
    pubs = []
    for li in best:
        txt = strip_tags(li)
        if len(txt) < 12:
            continue
        if len(re.findall(r"[\u4e00-\u9fff]", txt)) > 6:
            continue
        title = ""
        q = re.search(r"[“\"]([^”\"]{8,300})[”\"]", txt)
        if q:
            title = clean_title(q.group(1))
        else:
            # title sits before the venue, after the author list
            vm = VENUE_RE.search(txt)
            head = txt[:vm.start()] if vm else txt
            # format "Author, Author and Lastauthor. Title. Venue Year"
            # find the last "Name(s). " boundary before the title
            m = re.search(r"(?:^|and\s+|,\s*)"
                          r"([A-Z][A-Za-z\-]+(?:\s+[A-Z][A-Za-z\-]+){0,3})\.\s+"
                          r"([A-Z][^.(\u2013\-]{14,220})", head)
            if m:
                title = clean_title(m.group(2))
            else:
                title = clean_title(extract_title_from_head(head))
            if looks_like_author_list(title) or len(re.findall(r"\b[A-Z]\.", title)) > 2:
                title = ""
        venue_m = VENUE_RE.search(txt)
        venue = venue_m.group(1).strip() if venue_m else ""
        # reject a "venue" that is really an author name (short, looks like a person)
        if venue and re.match(r"^[A-Z][a-z]+\.?\s*[A-Z]?[a-z]*$", venue) and len(venue) <= 14:
            if not re.search(r"(Phys|Nature|Science|Adv|Opt|Nano|Commun|Appl|J\b|"
                             r"IEEE|Nucl|Rev|PR|EPL|PNAS|Cell)", venue):
                venue = ""
        year = None
        ym = re.findall(r"(?:19|20)\d{2}", txt)
        if ym:
            year = int(ym[-1])
        if title and len(title) >= 10 and not looks_like_author_list(title):
            pubs.append({"title": title[:280], "venue": venue, "year": year})
    return pubs[:5]


if __name__ == "__main__":
    import os, json
    RAW = r"D:\USTC-AI\sjtu-physics-directory\data\html"
    for f in ["jsml__zhangjie.html", "jsml__jiajinfeng.html", "jsml__jinxianmin.html"]:
        h = open(os.path.join(RAW, f), encoding="utf-8", errors="replace").read()
        pubs = parse_publications(h)
        print("###", f, len(pubs))
        for p in pubs:
            print("  ", p)
