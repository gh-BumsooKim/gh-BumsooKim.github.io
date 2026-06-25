import json
import re

# Maps HTML div id → internal tab key used in publications.json
TAB_DIV_IDS = {
    "pubtabselected":      "selected",    # pubs where selected == true
    "pubtabintime":        "intime",      # all non-ongoing pubs (auto)
    "pubtab3ddata":        "3ddata",
    "pubtabphotos":        "photos",
    "pubtabsound":         "sound",
    "pubtabartsandgaming": "artsandgaming",
    "pubtabrealworld":     "realworld",
    "pubtabrendering":     "rendering",
}

STATUS_LABELS = {
    "accepted":     "accepted",
    "rejected":     "rejected",
    "under_review": "Under review",
}


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def sort_key(pub):
    """ongoing first, then newest year/month descending. null month sorts last within a year."""
    if pub.get("status") == "ongoing":
        return (0, 0, 0)
    year = pub.get("year") or 0
    month = pub.get("month") or 0
    return (1, -year, -month)


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

def render_authors(authors):
    parts = []
    for a in authors:
        name = a["name"]
        suffix = ("*" if a.get("equal") else "") + ("&dagger;" if a.get("corresponding") else "")
        if a.get("is_me"):
            url = a.get("url", "")
            parts.append(f'<a target="_blank" href="{url}">{name}</a>{suffix}')
        else:
            parts.append(f"{name}{suffix}")
    return ", ".join(parts)


def render_venue(pub):
    venue = pub.get("venue", "")
    workshop = pub.get("venue_workshop")
    venue_note = pub.get("venue_note", "")
    year = pub.get("year")
    status_label = STATUS_LABELS.get(pub.get("status", ""), "")

    if venue:
        if workshop:
            venue_str = f'{venue} <a target="_blank" href="{workshop["url"]}">{workshop["name"]}</a>'
        else:
            venue_str = venue
    else:
        venue_str = ""

    if venue_note:
        venue_str = (venue_str + " " if venue_str else "") + venue_note

    if year:
        result = f"{venue_str}, {year}" if venue_str else str(year)
    else:
        result = venue_str

    if status_label:
        result += f" ({status_label})"

    return result


def render_links_html(pub):
    links = pub.get("links", {})

    # pubwebpage: project + extra_links + pdf (pipe-separated)
    webpage_parts = []
    if links.get("project"):
        webpage_parts.append(f'<a target="_blank" href="{links["project"]}">Project webpage</a>')
    for el in links.get("extra_links", []):
        webpage_parts.append(f'<a href="{el["url"]}">{el["label"]}</a>')
    pdf = links.get("pdf")
    if pdf == "soon":
        webpage_parts.append("<a>PDF (Soon)</a>")
    elif pdf:
        webpage_parts.append(f'<a href="{pdf}">PDF</a>')
    webpage_html = " | ".join(webpage_parts)

    # pubcode: github + arxiv + huggingface + chatgpt
    code_parts = []
    github = links.get("github")
    if github == "soon":
        code_parts.append(
            '<a target="_blank"><img src="asset/images/github-mark.svg" height="15em">&nbsp;Code (Soon)</a>'
        )
    elif github:
        code_parts.append(
            f'<a target="_blank" href="{github}"><img src="asset/images/github-mark.svg" height="15em">&nbsp;Code</a>'
        )
    if links.get("arxiv"):
        code_parts.append(
            f'<a target="_blank" href="{links["arxiv"]}"><img src="asset/images/arxiv-logo.svg" height="15em"></a>'
        )
    if links.get("huggingface"):
        code_parts.append(
            f'<a target="_blank" href="{links["huggingface"]}"><img src="asset/images/huggingface-logo.svg" height="15em">&nbsp;HuggingFace Dataset</a>'
        )
    if links.get("chatgpt"):
        code_parts.append(
            f'<a target="_blank" href="{links["chatgpt"]}"><img src="asset/images/chatgpt.svg" height="15em">&nbsp;ChatGPT Demo</a>'
        )
    code_html = " ".join(code_parts)

    return webpage_html, code_html


_TRACK_SUFFIXES = {"poster", "posters", "workshop", "workshops", "oral", "spotlight", "demo"}

def _venue_short(venue):
    words = venue.split()
    while words and words[-1].lower() in _TRACK_SUFFIXES:
        words = words[:-1]
    return " ".join(words) if words else venue


def render_venue_badge(pub):
    if pub.get("status") == "ongoing":
        return ""
    venue = pub.get("venue", "").strip()
    year = pub.get("year")
    if venue.lower().startswith("searching"):
        venue = ""
    if venue:
        venue = _venue_short(venue)
    if not venue and not year:
        return ""
    label = f"{venue} {year}".strip() if venue else str(year)
    return f'<div class="pub-venue-badge">{label}</div>'


def render_card(pub):
    image = pub.get("image") or ""
    img_tag = f'<img src="{image}" width="120px">' if image else '<img width="120px">'
    badge = render_venue_badge(pub)
    media_inner = (f'{badge}\n    ' if badge else "") + img_tag
    card_cls = "pub-card" + (" pub-highlight" if pub.get("highlight") else "")

    if pub.get("status") == "ongoing":
        return (
            f'<div class="{card_cls}">\n'
            f'    <div class="pubimgmedia">{media_inner}</div>\n'
            f'    <div class="pub-info">\n'
            f'        <div class="pubtitle">{pub["title"]}</div> (TBD)\n'
            f'        <div class="pubauthors"></div>\n'
            f'        <div class="pubvenueyear"></div>\n'
            f'        <div class="pubwebpage"></div>\n'
            f'        <div class="pubcode"></div>\n'
            f'        <div class="pubnote"></div>\n'
            f'    </div>\n'
            f'</div>'
        )

    authors_html = render_authors(pub.get("authors", []))
    venue_html = render_venue(pub)
    webpage_html, code_html = render_links_html(pub)
    note = pub.get("note", "")

    return (
        f'<div class="{card_cls}">\n'
        f'    <div class="pubimgmedia">{media_inner}</div>\n'
        f'    <div class="pub-info">\n'
        f'        <div class="pubtitle">{pub["title"]}</div>\n'
        f'        <div class="pubauthors">{authors_html}</div>\n'
        f'        <div class="pubvenueyear">{venue_html}</div>\n'
        f'        <div class="pubwebpage">{webpage_html}</div>\n'
        f'        <div class="pubcode">{code_html}</div>\n'
        f'        <div class="pubnote">{note}</div>\n'
        f'    </div>\n'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Tab filtering
# ---------------------------------------------------------------------------

def get_tab_pubs(pubs, tab_key):
    if tab_key == "selected":
        return [p for p in pubs if p.get("selected")]
    if tab_key == "intime":
        return [p for p in pubs if p.get("status") != "ongoing"]
    return [p for p in pubs if tab_key in p.get("tabs", [])]


# ---------------------------------------------------------------------------
# index.html transformations
# ---------------------------------------------------------------------------

def update_official_code(html, pubs):
    """Replace content between CODE:official markers with pubs that have a real GitHub URL."""
    items = []
    for pub in sorted(pubs, key=sort_key):
        links  = pub.get("links", {})
        github = links.get("github")
        year   = pub.get("year")
        if github and github != "soon":
            repo  = github.rstrip("/").split("/")[-1]
            label = f"{repo} ({year})" if year else repo
            items.append(
                f'<li><a target="_blank" href="{github}">'
                f'<img src="asset/images/github-mark.svg" height="15em">&nbsp;{label}</a></li>'
            )
        elif github == "soon" and links.get("github_repo"):
            repo  = links["github_repo"]
            label = f"{repo} ({year})" if year else repo
            items.append(
                f'<li><img src="asset/images/github-mark.svg" height="15em">&nbsp;{label} (TBD)</li>'
            )

    content = "\n".join(items) if items else "<li>TBD</li>"
    pattern = r'(<!-- CODE:official:START -->)(.*?)(<!-- CODE:official:END -->)'
    new_html, count = re.subn(pattern, rf'\1\n{content}\n\3', html, flags=re.DOTALL)
    if count == 0:
        print("WARNING: no marker found for 'CODE:official' — skipped")
    else:
        print(f"Updated official code section ({len(items)} entries)")
    return new_html


def update_tab_content(html, pubs):
    """Replace content between PUB markers for every tab."""
    for div_id, tab_key in TAB_DIV_IDS.items():
        tab_pubs = sorted(get_tab_pubs(pubs, tab_key), key=sort_key)
        cards_html = "\n".join(render_card(p) for p in tab_pubs)

        pattern = rf'(<!-- PUB:{tab_key}:START -->)(.*?)(<!-- PUB:{tab_key}:END -->)'
        new_html, count = re.subn(
            pattern, rf'\1\n{cards_html}\n\3', html, flags=re.DOTALL
        )
        if count == 0:
            print(f"WARNING: no marker found for '{tab_key}' — skipped")
        else:
            html = new_html
            print(f"Updated {div_id} ({len(tab_pubs)} entries)")
    return html


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    with open("publications.json", encoding="utf-8") as f:
        pubs = json.load(f)["publications"]

    with open("index.html", encoding="utf-8") as f:
        html = f.read()

    html = update_tab_content(html, pubs)
    html = update_official_code(html, pubs)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("\nindex.html updated successfully.")


if __name__ == "__main__":
    main()
