#!/usr/bin/env python3
"""Export an Obsidian LLM-wiki vault (the mock-wikify layout) to a static HTML site.

Dependency-free -- Python standard library only, so it runs on any machine with
python3 and needs no pandoc, no npm install, no network.

Reads `wiki/` from the vault root and writes a browsable multi-page site:
one .html per .md mirroring the folder structure, a sidebar built from the
topic folders, an in-page table of contents, prev/next paging, light/dark
themes, and a print stylesheet. Opens by double-clicking index.html --
every link is relative, so no web server is required.

Markdown handled: YAML front matter (aliases/title/tags), ATX headings,
paragraphs, nested bullet/ordered lists, task lists, GFM pipe tables
(including `\\|`-escaped and wiki-link-internal pipes), blockquotes, Obsidian
callouts, fenced code blocks, horizontal rules, bold/italic/strikethrough/
highlight/inline code, `[[wiki-links]]` and `![[embeds]]`, markdown links,
images, autolinks, bare URLs, and #tags.

Usage:
    python3 export-wiki-html.py                     # vault = cwd, out = ./html
    python3 export-wiki-html.py --vault ~/notes --out site
    python3 export-wiki-html.py --serve             # build, then preview
"""

from __future__ import annotations

import argparse
import html
import http.server
import json
import re
import shutil
import socketserver
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# --------------------------------------------------------------------------
# UI strings
# --------------------------------------------------------------------------

LABELS = {
    "en": {
        "home": "Home",
        "contents": "Contents",
        "on_this_page": "On this page",
        "filter": "Filter pages…",
        "skip": "Skip to content",
        "toggle_theme": "Toggle light/dark theme",
        "open_nav": "Open contents",
        "anchor": "Link to this section",
        "prev": "← Previous",
        "next": "Next →",
        "missing": "this page does not exist yet",
        "pages": "pages",
        "topics": "topics",
        "built": "built",
        "embed": "Embedded page",
    },
    "th": {
        "home": "หน้าแรก",
        "contents": "สารบัญ",
        "on_this_page": "ในหน้านี้",
        "filter": "กรองชื่อหน้า…",
        "skip": "ข้ามไปยังเนื้อหา",
        "toggle_theme": "สลับธีมสว่าง/มืด",
        "open_nav": "เปิดสารบัญ",
        "anchor": "ลิงก์ไปยังหัวข้อนี้",
        "prev": "← ก่อนหน้า",
        "next": "ถัดไป →",
        "missing": "ยังไม่มีหน้านี้",
        "pages": "หน้า",
        "topics": "หัวข้อ",
        "built": "สร้างเมื่อ",
        "embed": "หน้าที่ฝังไว้",
    },
}

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp"}

CALLOUT_ALIASES = {
    "abstract": "summary", "tldr": "summary", "info": "note", "todo": "note",
    "hint": "tip", "important": "tip", "check": "success", "done": "success",
    "help": "question", "faq": "question", "caution": "warning",
    "attention": "warning", "fail": "danger", "missing": "danger",
    "error": "danger", "bug": "danger",
}


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------


@dataclass
class Page:
    src: Path
    section: str  # "" for pages pinned at wiki/ root
    stem: str
    slug: str
    title: str
    summary: str
    body: str
    out_rel: str
    is_home: bool = False
    headings: list = field(default_factory=list)


@dataclass
class Section:
    name: str
    title: str
    number: str = ""
    pages: list = field(default_factory=list)


# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------

TOK_A, TOK_B = "\x00", "\x01"

RE_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
RE_FM_KEY = re.compile(r"^(\w+):\s*(.*)$", re.M)
RE_CODE = re.compile(r"(`+)(.+?)\1", re.S)
RE_EMBED = re.compile(r"!\[\[([^\]]+?)\]\]")
RE_WIKI = re.compile(r"\[\[([^\]]+?)\]\]")
RE_IMG = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RE_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RE_AUTOLINK = re.compile(r"<(https?://[^>\s]+|mailto:[^>\s]+)>")
RE_BARE_URL = re.compile(r"(?<![\"'=(>\w])(https?://[^\s<>\"')\]]+)")
RE_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__", re.S)
RE_ITALIC = re.compile(r"(?<![\*\w])\*([^*\n]+?)\*(?!\*)")
RE_STRIKE = re.compile(r"~~(.+?)~~", re.S)
RE_MARK = re.compile(r"==(.+?)==", re.S)
RE_TAG = re.compile(r"(?<![\w&#/;])#([A-Za-z฀-๿][\w฀-๿/_-]*)")

RE_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
RE_HR = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
RE_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+-]*)")
RE_UL = re.compile(r"^(\s*)([-*+])\s+(.*)$")
RE_OL = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
RE_TASK = re.compile(r"^\[([ xX])\]\s+(.*)$")
RE_QUOTE = re.compile(r"^\s{0,3}>\s?(.*)$")
RE_CALLOUT = re.compile(r"^\[!(\w+)\]([+-])?\s*(.*)$")
RE_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
RE_PIPE = re.compile(r"(?<!\\)\|")

RE_UNSUPPORTED = {
    "footnotes": re.compile(r"\[\^[^\]]+\]"),
    "math": re.compile(r"\$\$|(?<!\$)\$[^$\n]+\$(?!\$)"),
    "mermaid": re.compile(r"^```\s*mermaid", re.M),
    "dataview": re.compile(r"^```\s*dataview", re.M),
}


def is_thai(text: str) -> bool:
    thai = sum(1 for c in text if "฀" <= c <= "๿")
    letters = sum(1 for c in text if c.isalpha())
    return letters > 0 and thai / letters > 0.2


def slugify(text: str) -> str:
    text = strip_md(text).lower()
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    return text.strip("-") or "section"


def strip_md(text: str) -> str:
    text = RE_CODE.sub(r"\2", text)
    text = RE_EMBED.sub(lambda m: re.split(r"(?<!\\)\|", m.group(1))[-1], text)
    text = RE_WIKI.sub(lambda m: re.split(r"(?<!\\)\|", m.group(1))[-1], text)
    text = RE_IMG.sub(r"\1", text)
    text = RE_LINK.sub(r"\1", text)
    text = RE_AUTOLINK.sub(r"\1", text)
    text = RE_BOLD.sub(lambda m: m.group(1) or m.group(2), text)
    text = RE_ITALIC.sub(r"\1", text)
    text = RE_STRIKE.sub(r"\1", text)
    text = RE_MARK.sub(r"\1", text)
    return text.strip()


# --------------------------------------------------------------------------
# Inline renderer
# --------------------------------------------------------------------------


class Inline:
    """Renders one span of markdown. Links/code are stashed behind sentinel
    tokens before escaping so later passes cannot corrupt them."""

    def __init__(self, ctx=None):
        self.ctx = ctx  # PageContext or None

    def render(self, text: str) -> str:
        store: list[str] = []

        def stash(frag: str) -> str:
            store.append(frag)
            return f"{TOK_A}{len(store) - 1}{TOK_B}"

        def code_sub(m):
            return stash(f"<code>{html.escape(m.group(2).strip(), quote=False)}</code>")

        def embed_sub(m):
            target, _, display = split_target(m.group(1))
            if self.ctx:
                return stash(self.ctx.embed(target, display))
            return stash(html.escape(display or target, quote=False))

        def wiki_sub(m):
            target, anchor, display = split_target(m.group(1))
            label = self.emphasis(html.escape(display or target, quote=False))
            if not self.ctx:
                return stash(label)
            return stash(self.ctx.wikilink(target, anchor, label))

        def img_sub(m):
            alt = html.escape(m.group(1), quote=True)
            src = self.ctx.asset(m.group(2)) if self.ctx else m.group(2)
            return stash(f'<img src="{html.escape(src, quote=True)}" alt="{alt}" loading="lazy">')

        def link_sub(m):
            label = self.emphasis(html.escape(m.group(1), quote=False))
            url = m.group(2)
            if re.match(r"^[a-z][a-z0-9+.-]*:|^//|^#", url, re.I):
                href, ext = url, ' target="_blank" rel="noopener"' if url.startswith("http") else ""
            else:
                href = self.ctx.local(url) if self.ctx else url
                ext = ""
            return stash(f'<a href="{html.escape(href, quote=True)}"{ext}>{label}</a>')

        def auto_sub(m):
            u = m.group(1)
            return stash(
                f'<a href="{html.escape(u, quote=True)}" target="_blank" rel="noopener">'
                f"{html.escape(u, quote=False)}</a>"
            )

        text = RE_CODE.sub(code_sub, text)
        text = RE_EMBED.sub(embed_sub, text)
        text = RE_WIKI.sub(wiki_sub, text)
        text = RE_IMG.sub(img_sub, text)
        text = RE_AUTOLINK.sub(auto_sub, text)
        text = RE_LINK.sub(link_sub, text)
        text = html.escape(text, quote=False)
        text = RE_BARE_URL.sub(
            lambda m: stash(
                f'<a href="{html.escape(m.group(1), quote=True)}" target="_blank" '
                f'rel="noopener">{html.escape(m.group(1), quote=False)}</a>'
            ),
            text,
        )
        text = RE_TAG.sub(lambda m: f'<span class="tag">#{m.group(1)}</span>', text)
        text = self.emphasis(text)

        for _ in range(5):
            new = re.sub(f"{TOK_A}(\\d+){TOK_B}", lambda m: store[int(m.group(1))], text)
            if new == text:
                break
            text = new
        return text

    @staticmethod
    def emphasis(text: str) -> str:
        text = RE_BOLD.sub(lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", text)
        text = RE_ITALIC.sub(lambda m: f"<em>{m.group(1)}</em>", text)
        text = RE_STRIKE.sub(lambda m: f"<del>{m.group(1)}</del>", text)
        text = RE_MARK.sub(lambda m: f"<mark>{m.group(1)}</mark>", text)
        return text


def split_target(raw: str) -> tuple[str, str, str]:
    """`target#anchor|display` -> (target, anchor, display)."""
    parts = re.split(r"(?<!\\)\|", raw, maxsplit=1)
    target = parts[0].replace("\\|", "|").strip()
    display = parts[1].replace("\\|", "|").strip() if len(parts) > 1 else ""
    anchor = ""
    if "#" in target:
        target, anchor = target.split("#", 1)
        target, anchor = target.strip(), anchor.strip()
    return target, anchor, display


# --------------------------------------------------------------------------
# Block renderer
# --------------------------------------------------------------------------


class Blocks:
    def __init__(self, inline: Inline, labels: dict):
        self.inline = inline
        self.labels = labels
        self.headings: list[tuple[int, str, str]] = []
        self._ids: dict[str, int] = {}

    def uid(self, text: str) -> str:
        base = slugify(text)
        n = self._ids.get(base, 0)
        self._ids[base] = n + 1
        return base if n == 0 else f"{base}-{n + 1}"

    def render(self, md: str, skip_h1: bool = True, collect: bool = True) -> str:
        lines = md.replace("\r\n", "\n").expandtabs(4).split("\n")
        out: list[str] = []
        i, n = 0, len(lines)
        h1_dropped = False

        while i < n:
            line = lines[i]
            s = line.strip()

            if not s:
                i += 1
                continue

            fence = RE_FENCE.match(line)
            if fence:
                marker, lang = fence.group(2), fence.group(3)
                body, i = [], i + 1
                while i < n and not (
                    lines[i].strip().startswith(marker[0] * len(marker))
                    and set(lines[i].strip()) <= set(marker[0])
                ):
                    body.append(lines[i])
                    i += 1
                i += 1
                cls = f' class="language-{html.escape(lang, quote=True)}"' if lang else ""
                code = html.escape("\n".join(body), quote=False)
                out.append(f'<pre class="code"><code{cls}>{code}</code></pre>')
                continue

            m = RE_HEADING.match(line)
            if m:
                lvl, text = len(m.group(1)), m.group(2)
                if lvl == 1 and skip_h1 and not h1_dropped:
                    h1_dropped = True
                    i += 1
                    continue
                hid = self.uid(text)
                if collect:
                    self.headings.append((lvl, hid, strip_md(text)))
                out.append(
                    f'<h{lvl} id="{hid}">{self.inline.render(text)}'
                    f'<a class="anchor" href="#{hid}" aria-label="{self.labels["anchor"]}">#</a>'
                    f"</h{lvl}>"
                )
                i += 1
                continue

            if RE_HR.match(s):
                out.append("<hr>")
                i += 1
                continue

            if s.startswith("|") and i + 1 < n and RE_TABLE_SEP.match(lines[i + 1]):
                block, i = take(lines, i, lambda x: x.strip().startswith("|"))
                out.append(self.table(block))
                continue

            if RE_QUOTE.match(line):
                block, i = take(lines, i, lambda x: bool(RE_QUOTE.match(x)))
                inner = [RE_QUOTE.match(b).group(1) for b in block]
                out.append(self.quote(inner))
                continue

            if RE_UL.match(line) or RE_OL.match(line):
                block, i = take(
                    lines, i,
                    lambda x: bool(RE_UL.match(x) or RE_OL.match(x)) or x.startswith(" "),
                )
                out.append(self.list_block(block))
                continue

            block, i = take(lines, i, lambda x: bool(x.strip()) and not starts_block(x))
            out.append(f"<p>{self.inline.render(' '.join(b.strip() for b in block))}</p>")

        return "\n".join(out)

    # -- blockquotes & callouts -------------------------------------------
    def quote(self, inner: list[str]) -> str:
        co = RE_CALLOUT.match(inner[0].strip()) if inner else None
        if not co:
            return f"<blockquote>{self.render(chr(10).join(inner), skip_h1=False, collect=False)}</blockquote>"
        kind = co.group(1).lower()
        kind = CALLOUT_ALIASES.get(kind, kind)
        fold, title = co.group(2), co.group(3).strip() or co.group(1).capitalize()
        body = self.render("\n".join(inner[1:]), skip_h1=False, collect=False)
        head = f'<p class="callout-title">{self.inline.render(title)}</p>'
        if fold:
            open_attr = " open" if fold == "+" else ""
            return (
                f'<details class="callout callout-{html.escape(kind, quote=True)}"{open_attr}>'
                f"<summary>{self.inline.render(title)}</summary>{body}</details>"
            )
        return f'<div class="callout callout-{html.escape(kind, quote=True)}">{head}{body}</div>'

    # -- lists -------------------------------------------------------------
    def list_block(self, block: list[str]) -> str:
        items: list[list] = []
        for line in block:
            mo, mu = RE_OL.match(line), RE_UL.match(line)
            if mo:
                items.append([len(mo.group(1)), "ol", int(mo.group(2)), [mo.group(3)]])
            elif mu:
                items.append([len(mu.group(1)), "ul", None, [mu.group(3)]])
            elif items:
                items[-1][3].append(line.strip())
        html_out, _ = self.build_list(items, 0, items[0][0] if items else 0)
        return html_out

    def build_list(self, items, i, indent):
        kind = items[i][1]
        start = items[i][2] if kind == "ol" else None
        attr = f' start="{start}"' if kind == "ol" and start not in (None, 1) else ""
        has_task = False
        parts: list[str] = []

        while i < len(items) and items[i][0] >= indent:
            if items[i][0] > indent:
                child, i = self.build_list(items, i, items[i][0])
                if parts:
                    parts[-1] = parts[-1][: -len("</li>")] + child + "</li>"
                continue
            if items[i][1] != kind:
                break
            text = " ".join(items[i][3]).strip()
            task = RE_TASK.match(text)
            if task:
                has_task = True
                checked = " checked" if task.group(1).lower() == "x" else ""
                cls = " class=\"task done\"" if checked else ' class="task"'
                parts.append(
                    f"<li{cls}><input type=\"checkbox\" disabled{checked}>"
                    f"<span>{self.inline.render(task.group(2))}</span></li>"
                )
            else:
                parts.append(f"<li>{self.inline.render(text)}</li>")
            i += 1

        cls = ' class="task-list"' if has_task else ""
        return f"<{kind}{attr}{cls}>\n" + "\n".join(parts) + f"\n</{kind}>", i

    # -- tables ------------------------------------------------------------
    def table(self, block: list[str]) -> str:
        rows = [self.cells(r) for r in block]
        header, body = rows[0], rows[2:]
        aligns = [align_of(c) for c in self.cells(block[1])]

        def cell(tag, text, j):
            st = f' style="text-align:{aligns[j]}"' if j < len(aligns) and aligns[j] else ""
            return f"<{tag}{st}>{self.inline.render(text)}</{tag}>"

        head = "".join(cell("th", c, j) for j, c in enumerate(header))
        out = ['<div class="table-wrap">', "<table>", f"<thead><tr>{head}</tr></thead>", "<tbody>"]
        for row in body:
            out.append("<tr>" + "".join(cell("td", c, j) for j, c in enumerate(row)) + "</tr>")
        out += ["</tbody>", "</table>", "</div>"]
        return "\n".join(out)

    @staticmethod
    def cells(row: str) -> list[str]:
        # A `|` inside [[...]] separates target from display text, not cells.
        # Vault convention escapes it as `\|`; tolerate it either way.
        row = RE_WIKI.sub(
            lambda m: "[[" + m.group(1).replace("\\|", "|").replace("|", "\\|") + "]]",
            row.strip(),
        )
        if row.startswith("|"):
            row = row[1:]
        if row.endswith("|") and not row.endswith("\\|"):
            row = row[:-1]
        return [c.replace("\\|", "|").strip() for c in RE_PIPE.split(row)]


def take(lines, i, pred):
    block = []
    while i < len(lines) and lines[i].strip() and pred(lines[i]):
        block.append(lines[i])
        i += 1
    return block, i


def starts_block(line: str) -> bool:
    s = line.strip()
    return bool(
        RE_HEADING.match(line) or RE_HR.match(s) or RE_QUOTE.match(line)
        or RE_UL.match(line) or RE_OL.match(line) or RE_FENCE.match(line)
        or s.startswith("|")
    )


def align_of(spec: str) -> str:
    spec = spec.strip()
    if spec.startswith(":") and spec.endswith(":"):
        return "center"
    return "right" if spec.endswith(":") else ""


# --------------------------------------------------------------------------
# Link / asset resolution
# --------------------------------------------------------------------------


class PageContext:
    def __init__(self, page, index, assets, labels, report):
        self.page, self.index, self.assets = page, index, assets
        self.labels, self.report = labels, report

    def _rel(self, to_rel: str) -> str:
        return ("../" * self.page.out_rel.count("/")) + to_rel

    def find(self, target: str):
        key = target.lower()
        return self.index.get(key) or self.index.get(Path(key).stem)

    def wikilink(self, target: str, anchor: str, label: str) -> str:
        if not target and anchor:  # same-page [[#heading]]
            return f'<a class="wikilink" href="#{slugify(anchor)}">{label}</a>'
        hit = self.find(target)
        if hit is None:
            self.report.broken.setdefault(target, set()).add(self.page.src_rel)
            return f'<span class="missing-link" title="{self.labels["missing"]}">{label}</span>'
        self.report.inbound.setdefault(hit.out_rel, set()).add(self.page.out_rel)
        href = self._rel(hit.out_rel) + (f"#{slugify(anchor)}" if anchor else "")
        return f'<a class="wikilink" href="{html.escape(href, quote=True)}">{label}</a>'

    def embed(self, target: str, display: str) -> str:
        if Path(target).suffix.lower() in IMAGE_EXT:
            src = self.asset(target)
            alt = html.escape(display or Path(target).stem, quote=True)
            return f'<img src="{html.escape(src, quote=True)}" alt="{alt}" loading="lazy">'
        hit = self.find(target)
        label = html.escape(display or (hit.title if hit else target), quote=False)
        if hit is None:
            self.report.broken.setdefault(target, set()).add(self.page.src_rel)
            return f'<span class="missing-link" title="{self.labels["missing"]}">{label}</span>'
        href = html.escape(self._rel(hit.out_rel), quote=True)
        return (
            f'<a class="embed-card" href="{href}">'
            f'<span class="embed-kind">{self.labels["embed"]}</span>'
            f"<span>{label}</span></a>"
        )

    def asset(self, ref: str) -> str:
        if re.match(r"^[a-z][a-z0-9+.-]*:|^//", ref, re.I):
            return ref
        name = Path(ref.split("#")[0].split("?")[0]).name
        out_name = self.assets.want(name, ref)
        if out_name is None:
            self.report.missing_assets.setdefault(ref, set()).add(self.page.src_rel)
            return ref
        return self._rel(f"assets/media/{out_name}")

    def local(self, ref: str) -> str:
        base = ref.split("#")[0]
        anchor = ref[len(base):]
        if base.endswith(".md"):
            hit = self.find(Path(base).stem)
            if hit:
                return self._rel(hit.out_rel) + anchor
        return self.asset(ref)


class AssetPool:
    """Resolves attachment references against every non-markdown file in the
    vault (Obsidian style: match by filename), and copies what is used."""

    def __init__(self, vault: Path):
        self.by_name: dict[str, Path] = {}
        for f in vault.rglob("*"):
            if f.is_file() and f.suffix.lower() not in {".md"} and ".obsidian" not in f.parts:
                self.by_name.setdefault(f.name.lower(), f)
        self.used: dict[str, Path] = {}

    def want(self, name: str, ref: str) -> str | None:
        src = self.by_name.get(name.lower())
        if src is None:
            return None
        out = name
        if out in self.used and self.used[out] != src:
            out = f"{Path(name).stem}-{abs(hash(str(src))) % 9973}{Path(name).suffix}"
        self.used[out] = src
        return out

    def copy_into(self, media: Path) -> int:
        if not self.used:
            return 0
        media.mkdir(parents=True, exist_ok=True)
        for out, src in self.used.items():
            shutil.copy2(src, media / out)
        return len(self.used)


@dataclass
class Report:
    broken: dict = field(default_factory=dict)
    inbound: dict = field(default_factory=dict)
    missing_assets: dict = field(default_factory=dict)
    unsupported: dict = field(default_factory=dict)
    collisions: list = field(default_factory=list)


# --------------------------------------------------------------------------
# Vault loading
# --------------------------------------------------------------------------


def read_page(md: Path, section: str, wiki: Path) -> Page:
    text = md.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    fm = RE_FM.match(text)
    if fm:
        meta = {k: v.strip() for k, v in RE_FM_KEY.findall(fm.group(1))}
        text = text[fm.end():]

    slug = ""
    if "aliases" in meta:
        slug = meta["aliases"].strip("[]").split(",")[0].strip().strip("\"'")
    slug = slug or re.sub(r"^\d+[-_]", "", md.stem)

    h1 = re.search(r"^#\s+(.*)$", text, re.M)
    title = strip_md(h1.group(1)) if h1 else meta.get("title", slug)

    summary = ""
    for pat in (r"^\*\*(?:Summary|สรุป)\*\*\s*:\s*(.*)$", r"^\s*([^\s#*>|-].{20,})$"):
        m = re.search(pat, text, re.M)
        if m:
            summary = strip_md(m.group(1))
            break

    stem = md.stem
    out_rel = f"{section}/{stem}.html" if section else f"{stem}.html"
    page = Page(
        src=md, section=section, stem=stem, slug=slug, title=title,
        summary=summary, body=text, out_rel=out_rel,
    )
    page.src_rel = str(md.relative_to(wiki.parent))
    return page


def load(wiki: Path, cfg: dict) -> tuple[list[Section], list[Page], Page | None, Page | None]:
    overrides = cfg.get("sections", {})
    sections: list[Section] = []
    for folder in sorted(p for p in wiki.iterdir() if p.is_dir() and not p.name.startswith(".")):
        num = re.match(r"^(\d+)[-_]", folder.name)
        title = overrides.get(folder.name) or re.sub(r"^\d+[-_]", "", folder.name).replace("-", " ").strip()
        sec = Section(name=folder.name, title=title, number=num.group(1) if num else "")
        for md in sorted(folder.rglob("*.md")):
            sec.pages.append(read_page(md, folder.name, wiki))
        if sec.pages:
            sections.append(sec)

    root_pages = [read_page(md, "", wiki) for md in sorted(wiki.glob("*.md"))]
    home = next((p for p in root_pages if p.stem.lower() == "index"), None)
    log = next((p for p in root_pages if p.stem.lower() == "log"), None)
    if home:
        home.is_home = True
        home.out_rel = "index.html"

    ordered = [p for s in sections for p in s.pages]
    extras = [p for p in root_pages if p not in (home,)]
    return sections, ordered, home, log


# --------------------------------------------------------------------------
# HTML shell
# --------------------------------------------------------------------------


def rel_to(from_rel: str, to_rel: str) -> str:
    return ("../" * from_rel.count("/")) + to_rel


def sidebar(sections, extras, here, from_rel, L, home_title) -> str:
    out = [f'<nav class="sidebar-nav" aria-label="{L["contents"]}">']
    cls = " active" if here == "index.html" else ""
    out.append(f'<a class="nav-home{cls}" href="{rel_to(from_rel, "index.html")}">{html.escape(L["home"])}</a>')
    for i, sec in enumerate(sections, 1):
        num = sec.number or f"{i:02d}"
        opened = " open" if any(p.out_rel == here for p in sec.pages) else ""
        out.append(f"<details class=\"nav-section\"{opened}>")
        out.append(
            f'<summary><span class="nav-num">{html.escape(num)}</span>'
            f"<span>{html.escape(sec.title)}</span></summary><ul>"
        )
        for p in sec.pages:
            a = ' class="active"' if p.out_rel == here else ""
            out.append(f'<li><a{a} href="{rel_to(from_rel, p.out_rel)}">{html.escape(p.title)}</a></li>')
        out.append("</ul></details>")
    if extras:
        out.append('<ul class="nav-extras">')
        for p in extras:
            a = ' class="active"' if p.out_rel == here else ""
            out.append(f'<li><a{a} href="{rel_to(from_rel, p.out_rel)}">{html.escape(p.title)}</a></li>')
        out.append("</ul>")
    out.append("</nav>")
    return "\n".join(out)


def shell(*, title, site, from_rel, sections, extras, here, content, toc="", body_class="", L) -> str:
    assets = rel_to(from_rel, "assets")
    full = title if title == site["title"] else f"{title} — {site['title']}"
    sub = f'<span class="brand-sub">{html.escape(site["subtitle"])}</span>' if site.get("subtitle") else ""
    return f"""<!doctype html>
<html lang="{site['lang']}" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full)}</title>
<meta name="description" content="{html.escape(site.get('subtitle', ''), quote=True)}">
<link rel="stylesheet" href="{assets}/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#128218;</text></svg>">
</head>
<body class="{body_class}">
<a class="skip" href="#main">{html.escape(L['skip'])}</a>
<header class="topbar">
  <button class="icon-btn menu-toggle" aria-label="{html.escape(L['open_nav'])}" aria-expanded="false">☰</button>
  <a class="brand" href="{rel_to(from_rel, 'index.html')}">
    <span class="brand-title">{html.escape(site['title'])}</span>{sub}
  </a>
  <button class="icon-btn theme-toggle" aria-label="{html.escape(L['toggle_theme'])}" title="{html.escape(L['toggle_theme'])}">◑</button>
</header>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="filter-wrap">
      <input type="search" id="nav-filter" placeholder="{html.escape(L['filter'])}" aria-label="{html.escape(L['filter'])}" autocomplete="off">
    </div>
    {sidebar(sections, extras, here, from_rel, L, site['title'])}
  </aside>
  <div class="sidebar-scrim" hidden></div>
  <main id="main" class="content">
{content}
  </main>
  {toc}
</div>
<script src="{assets}/app.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def build(vault: Path, out_dir: Path, cfg: dict) -> Report:
    wiki = vault / cfg.get("wiki_dir", "wiki")
    if not wiki.is_dir():
        sys.exit(f"No '{wiki.name}/' folder in {vault}")

    sections, pages, home, log = load(wiki, cfg)
    if not pages and not home:
        sys.exit(f"No markdown pages found under {wiki}")

    sample = "\n".join(p.title + p.summary for p in pages[:40])
    lang = cfg.get("lang") or ("th" if is_thai(sample) else "en")
    L = LABELS.get(lang, LABELS["en"])

    site = {
        "title": cfg.get("title") or (home.title if home else vault.name),
        "subtitle": cfg.get("subtitle", ""),
        "lang": lang,
    }

    index: dict[str, Page] = {}
    report = Report()
    for p in pages + ([home] if home else []) + ([log] if log else []):
        for key in {p.stem.lower(), p.slug.lower(), p.title.lower()}:
            if key in index and index[key] is not p:
                report.collisions.append(f"{key}: {index[key].out_rel} / {p.out_rel}")
            index.setdefault(key, p)

    for name, pat in RE_UNSUPPORTED.items():
        for p in pages:
            if pat.search(p.body):
                report.unsupported.setdefault(name, set()).add(p.src_rel)

    assets = AssetPool(vault)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "assets").mkdir(parents=True)

    extras = [log] if log else []
    all_docs = pages + extras

    def emit(page, prev, nxt, section):
        ctx = PageContext(page, index, assets, L, report)
        blocks = Blocks(Inline(ctx), L)
        body = blocks.render(page.body, skip_h1=True)
        page.headings = blocks.headings

        crumbs = ""
        if section:
            num = section.number or ""
            label = f"{num} · {section.title}" if num else section.title
            crumbs = (
                f'<nav class="crumbs"><a href="{rel_to(page.out_rel, "index.html")}">{html.escape(L["home"])}</a>'
                f'<span aria-hidden="true">›</span><span>{html.escape(label)}</span></nav>'
            )

        pager = ['<nav class="pager">']
        for p_, cls, lab in ((prev, "pager-prev", L["prev"]), (nxt, "pager-next", L["next"])):
            if p_:
                pager.append(
                    f'<a class="{cls}" href="{rel_to(page.out_rel, p_.out_rel)}">'
                    f'<span class="pager-label">{html.escape(lab)}</span>'
                    f'<span class="pager-title">{html.escape(p_.title)}</span></a>'
                )
            else:
                pager.append("<span></span>")
        pager.append("</nav>")

        items = "".join(
            f'<li class="lvl-{lv}"><a href="#{hid}">{html.escape(tx)}</a></li>'
            for lv, hid, tx in page.headings if lv in (2, 3)
        )
        toc = (
            f'<aside class="toc"><div class="toc-inner">'
            f'<p class="toc-title">{html.escape(L["on_this_page"])}</p><ul>{items}</ul></div></aside>'
            if items else ""
        )

        content = (
            f"{crumbs}\n<article class=\"page\">\n<h1>{html.escape(page.title)}</h1>\n"
            f"{body}\n</article>\n{''.join(pager)}"
        )
        target = out_dir / page.out_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            shell(
                title=page.title, site=site, from_rel=page.out_rel, sections=sections,
                extras=extras, here=page.out_rel, content=content, toc=toc,
                body_class="has-toc" if items else "", L=L,
            ),
            encoding="utf-8",
        )

    for i, page in enumerate(pages):
        section = next(s for s in sections if s.name == page.section)
        emit(page, pages[i - 1] if i else None, pages[i + 1] if i < len(pages) - 1 else None, section)
    for page in extras:
        emit(page, None, None, None)

    # ---- home ----
    if home:
        ctx = PageContext(home, index, assets, L, report)
        blocks = Blocks(Inline(ctx), L)
        inner = blocks.render(home.body, skip_h1=True)
        toc_items = ""
    else:
        cards = []
        for i, sec in enumerate(sections, 1):
            num = sec.number or f"{i:02d}"
            lis = "".join(
                f'<li><a href="{html.escape(p.out_rel)}">{html.escape(p.title)}</a>'
                + (f'<span class="card-sum">{html.escape(p.summary)}</span>' if p.summary else "")
                + "</li>"
                for p in sec.pages
            )
            cards.append(
                f'<section class="sec-card"><h2><span class="nav-num">{html.escape(num)}</span>'
                f"{html.escape(sec.title)}</h2><ol>{lis}</ol></section>"
            )
        inner = f'<div class="sec-grid">{"".join(cards)}</div>'
        toc_items = ""

    stats = (
        f'<p class="meta-line">{len(pages)} {html.escape(L["pages"])} · '
        f'{len(sections)} {html.escape(L["topics"])} · {html.escape(L["built"])} {date.today().isoformat()}</p>'
    )
    intro = cfg.get("intro", "")
    lede = f'<p class="lede">{Inline().render(intro)}</p>\n' if intro else ""
    home_html = (
        f'<article class="page home">\n<h1>{html.escape(site["title"])}</h1>\n'
        f"{lede}{stats}\n{inner}\n</article>"
    )
    (out_dir / "index.html").write_text(
        shell(
            title=site["title"], site=site, from_rel="index.html", sections=sections,
            extras=extras, here="index.html", content=home_html, body_class="is-home", L=L,
        ),
        encoding="utf-8",
    )

    (out_dir / "assets" / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (out_dir / "assets" / "app.js").write_text(APP_JS, encoding="utf-8")
    copied = assets.copy_into(out_dir / "assets" / "media")

    # ---- report ----
    print(f"✓ {len(all_docs) + 1} pages → {out_dir}" + (f"  ({copied} attachments)" if copied else ""))
    orphans = [p.title for p in pages if p.out_rel not in report.inbound]
    if report.collisions:
        print("\n⚠ ambiguous link keys (a [[link]] may hit the wrong page):")
        for c in sorted(set(report.collisions)):
            print(f"   {c}")
    if report.broken:
        print(f"\n⚠ links with no target page ({len(report.broken)}), rendered as dimmed text:")
        for t, srcs in sorted(report.broken.items()):
            print(f"   [[{t}]]  ← {len(srcs)} page(s)")
            for s in sorted(srcs):
                print(f"      {s}")
    if report.missing_assets:
        print(f"\n⚠ attachments not found in the vault ({len(report.missing_assets)}):")
        for t, srcs in sorted(report.missing_assets.items()):
            print(f"   {t}  ← {', '.join(sorted(srcs))}")
    if report.unsupported:
        print("\n⚠ markdown this exporter does not render (left as literal text):")
        for name, srcs in sorted(report.unsupported.items()):
            print(f"   {name}: {len(srcs)} page(s) — {', '.join(sorted(srcs)[:3])}")
    if orphans:
        print(f"\nℹ pages with no inbound [[links]] ({len(orphans)}): {', '.join(orphans[:8])}"
              + (" …" if len(orphans) > 8 else ""))
    print(f"\nOpen: {out_dir / 'index.html'}")
    return report


# --------------------------------------------------------------------------
# Assets
# --------------------------------------------------------------------------

STYLE_CSS = """/* LLM-wiki static export */
:root {
  --font-ui: "IBM Plex Sans Thai", "Sarabun", "Noto Sans Thai", "Sukhumvit Set",
    "Thonburi", -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
  --bg: #f7f7f5; --bg-panel: #fff; --bg-sunk: #efeeea;
  --fg: #22201d; --fg-muted: #6b6862; --fg-faint: #9a968e;
  --border: #e0ddd6; --border-strong: #cfcbc2;
  --accent: #9b1c2e; --accent-soft: #f3e3e5; --accent-fg: #7d1624;
  --shadow: 0 1px 2px rgba(0,0,0,.05), 0 8px 24px rgba(0,0,0,.05);
  --radius: 10px; --sidebar-w: 20rem; --toc-w: 15rem; --measure: 46rem;
}
:root[data-theme="dark"] {
  --bg: #16181d; --bg-panel: #1c1f25; --bg-sunk: #22262d;
  --fg: #e6e5e1; --fg-muted: #a3a29d; --fg-faint: #75746f;
  --border: #2c3037; --border-strong: #3c414a;
  --accent: #f2828f; --accent-soft: #37232a; --accent-fg: #f7a3ad;
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.25);
}
@media (prefers-color-scheme: dark) {
  :root[data-theme="auto"] {
    --bg: #16181d; --bg-panel: #1c1f25; --bg-sunk: #22262d;
    --fg: #e6e5e1; --fg-muted: #a3a29d; --fg-faint: #75746f;
    --border: #2c3037; --border-strong: #3c414a;
    --accent: #f2828f; --accent-soft: #37232a; --accent-fg: #f7a3ad;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 8px 24px rgba(0,0,0,.25);
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 5rem; }
body {
  margin: 0; font-family: var(--font-ui); font-size: 17px; line-height: 1.85;
  background: var(--bg); color: var(--fg); -webkit-font-smoothing: antialiased;
  word-break: break-word; overflow-wrap: anywhere; line-break: loose;
}
a { color: var(--accent-fg); text-decoration-color: color-mix(in srgb, var(--accent) 40%, transparent); text-underline-offset: .18em; }
a:hover { text-decoration-color: var(--accent); }
.skip { position: absolute; left: -9999px; }
.skip:focus { left: 1rem; top: .5rem; z-index: 100; background: var(--bg-panel); padding: .5rem 1rem; border-radius: var(--radius); box-shadow: var(--shadow); }

.topbar {
  position: sticky; top: 0; z-index: 40; display: flex; align-items: center; gap: .75rem;
  padding: .6rem 1.1rem; background: color-mix(in srgb, var(--bg-panel) 88%, transparent);
  backdrop-filter: saturate(1.6) blur(12px); border-bottom: 1px solid var(--border);
}
.brand { display: flex; flex-direction: column; gap: .05rem; text-decoration: none; color: inherit; min-width: 0; margin-right: auto; }
.brand-title { font-weight: 700; font-size: .98rem; line-height: 1.35; }
.brand-sub { font-size: .78rem; color: var(--fg-muted); line-height: 1.3; }
.icon-btn { flex: none; width: 2.25rem; height: 2.25rem; display: grid; place-items: center; font-size: 1.05rem; cursor: pointer; background: transparent; color: var(--fg-muted); border: 1px solid transparent; border-radius: 8px; }
.icon-btn:hover { background: var(--bg-sunk); color: var(--fg); border-color: var(--border); }
.menu-toggle { display: none; }

.layout { display: grid; grid-template-columns: var(--sidebar-w) minmax(0,1fr); align-items: start; max-width: 96rem; margin: 0 auto; }
body.has-toc .layout { grid-template-columns: var(--sidebar-w) minmax(0,1fr) var(--toc-w); }

.sidebar { position: sticky; top: 3.6rem; height: calc(100vh - 3.6rem); overflow-y: auto; overscroll-behavior: contain; padding: 1rem .75rem 3rem; border-right: 1px solid var(--border); scrollbar-width: thin; }
.filter-wrap { position: sticky; top: 0; z-index: 2; padding-bottom: .6rem; background: var(--bg); }
#nav-filter { width: 100%; padding: .45rem .7rem; font: inherit; font-size: .88rem; color: var(--fg); background: var(--bg-panel); border: 1px solid var(--border-strong); border-radius: 8px; }
#nav-filter:focus { outline: 2px solid var(--accent); outline-offset: 1px; border-color: transparent; }
.nav-home { display: block; padding: .35rem .6rem; margin-bottom: .5rem; font-size: .9rem; font-weight: 600; border-radius: 7px; text-decoration: none; color: var(--fg-muted); }
.nav-home:hover { background: var(--bg-sunk); color: var(--fg); }
.nav-home.active { background: var(--accent-soft); color: var(--accent-fg); }
.nav-section { border-radius: 8px; margin-bottom: .1rem; }
.nav-section > summary { display: flex; align-items: baseline; gap: .5rem; padding: .38rem .6rem; cursor: pointer; list-style: none; font-size: .88rem; font-weight: 600; color: var(--fg-muted); border-radius: 7px; }
.nav-section > summary::-webkit-details-marker { display: none; }
.nav-section > summary:hover { background: var(--bg-sunk); color: var(--fg); }
.nav-num { font-family: var(--font-mono); font-size: .72rem; color: var(--fg-faint); flex: none; }
.nav-section ul, .nav-extras { list-style: none; margin: 0 0 .4rem; padding: 0 0 0 1.55rem; border-left: 1px solid var(--border); margin-left: 1.05rem; }
.nav-extras { margin-top: .6rem; }
.sidebar li a { display: block; padding: .26rem .55rem; margin: 1px 0; font-size: .865rem; line-height: 1.55; text-decoration: none; color: var(--fg-muted); border-radius: 6px; }
.sidebar li a:hover { background: var(--bg-sunk); color: var(--fg); }
.sidebar li a.active { background: var(--accent-soft); color: var(--accent-fg); font-weight: 600; }
.sidebar-scrim { display: none; }

.content { padding: 2.2rem clamp(1.1rem, 4vw, 3rem) 6rem; min-width: 0; }
.page { max-width: var(--measure); }
.crumbs { display: flex; gap: .5rem; align-items: center; flex-wrap: wrap; margin-bottom: 1.1rem; font-size: .82rem; color: var(--fg-muted); }
.crumbs a { color: var(--fg-muted); text-decoration: none; }
.crumbs a:hover { color: var(--accent-fg); text-decoration: underline; }

h1,h2,h3,h4 { line-height: 1.45; font-weight: 700; letter-spacing: -.005em; }
h1 { font-size: clamp(1.6rem, 3.4vw, 2.1rem); margin: 0 0 1.4rem; }
h2 { font-size: 1.3rem; margin: 2.6rem 0 .9rem; padding-top: 1.1rem; border-top: 1px solid var(--border); }
h3 { font-size: 1.08rem; margin: 1.9rem 0 .6rem; }
h4 { font-size: .98rem; margin: 1.5rem 0 .5rem; color: var(--fg-muted); }
/* a `---` rule already separates sections -- don't double it with the h2 border */
hr + h2 { border-top: 0; padding-top: 0; margin-top: 1.6rem; }
h2 .anchor, h3 .anchor { margin-left: .45rem; font-weight: 400; text-decoration: none; color: var(--fg-faint); opacity: 0; transition: opacity .15s; }
h2:hover .anchor, h3:hover .anchor { opacity: 1; }
p { margin: 0 0 1.05rem; }
ul, ol { margin: 0 0 1.15rem; padding-left: 1.4rem; }
li { margin-bottom: .4rem; }
li::marker { color: var(--fg-faint); }
li > ul, li > ol { margin-top: .4rem; }
strong { font-weight: 700; color: var(--fg); }
mark { background: color-mix(in srgb, var(--accent) 22%, transparent); color: inherit; padding: .05em .2em; border-radius: 3px; }
del { color: var(--fg-faint); }
hr { height: 1px; margin: 2rem 0; background: var(--border); border: 0; }
img { max-width: 100%; height: auto; border-radius: var(--radius); }

/* task lists -- never strike through completed items (vault convention) */
ul.task-list { list-style: none; padding-left: .2rem; }
li.task { display: flex; align-items: flex-start; gap: .55rem; }
li.task input { margin-top: .55em; flex: none; accent-color: var(--accent); }
li.task.done { text-decoration: none; opacity: .55; }

code { padding: .1em .38em; font-family: var(--font-mono); font-size: .84em; background: var(--bg-sunk); border: 1px solid var(--border); border-radius: 5px; word-break: break-all; }
pre.code { margin: 1.3rem 0; padding: .9rem 1.1rem; overflow-x: auto; background: var(--bg-sunk); border: 1px solid var(--border); border-radius: var(--radius); line-height: 1.65; }
pre.code code { padding: 0; background: none; border: 0; font-size: .84rem; word-break: normal; }

blockquote { margin: 1.3rem 0; padding: .85rem 1.1rem; background: var(--bg-panel); border: 1px solid var(--border); border-left: 3px solid var(--accent); border-radius: 0 var(--radius) var(--radius) 0; color: var(--fg-muted); }
blockquote > :last-child { margin-bottom: 0; }

.callout { margin: 1.3rem 0; padding: .85rem 1.1rem; background: var(--bg-panel); border: 1px solid var(--border); border-left: 3px solid var(--cal, var(--accent)); border-radius: 0 var(--radius) var(--radius) 0; }
.callout > :last-child { margin-bottom: 0; }
.callout-title, .callout > summary { margin: 0 0 .4rem; font-weight: 700; color: var(--cal, var(--accent-fg)); cursor: default; }
.callout > summary { cursor: pointer; }
.callout-note { --cal: #3b82f6; } .callout-tip { --cal: #06b6d4; }
.callout-summary { --cal: #6366f1; } .callout-success { --cal: #16a34a; }
.callout-question { --cal: #a855f7; } .callout-warning { --cal: #d97706; }
.callout-danger { --cal: #dc2626; } .callout-example { --cal: #8b5cf6; }
.callout-quote { --cal: var(--fg-faint); }

.table-wrap { margin: 1.4rem 0; overflow-x: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--bg-panel); }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th, td { padding: .62rem .85rem; text-align: left; vertical-align: top; border-bottom: 1px solid var(--border); line-height: 1.7; }
thead th { background: var(--bg-sunk); font-weight: 700; white-space: nowrap; }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: color-mix(in srgb, var(--bg-sunk) 55%, transparent); }

.wikilink { text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--accent) 35%, transparent); }
.wikilink:hover { border-bottom-color: var(--accent); background: var(--accent-soft); }
.missing-link { color: var(--fg-faint); border-bottom: 1px dashed var(--fg-faint); cursor: help; }
.tag { display: inline-block; padding: .05em .45em; font-size: .82em; color: var(--fg-muted); background: var(--bg-sunk); border: 1px solid var(--border); border-radius: 999px; }
.embed-card { display: flex; flex-direction: column; gap: .1rem; margin: 1.1rem 0; padding: .7rem 1rem; text-decoration: none; color: inherit; background: var(--bg-panel); border: 1px solid var(--border); border-radius: var(--radius); }
.embed-card:hover { border-color: var(--accent); }
.embed-kind { font-size: .72rem; color: var(--fg-faint); }

.pager { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; max-width: var(--measure); margin-top: 3.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
.pager a { display: flex; flex-direction: column; gap: .2rem; padding: .8rem 1rem; text-decoration: none; color: inherit; background: var(--bg-panel); border: 1px solid var(--border); border-radius: var(--radius); }
.pager a:hover { border-color: var(--accent); box-shadow: var(--shadow); }
.pager-next { text-align: right; }
.pager-label { font-size: .76rem; color: var(--fg-muted); }
.pager-title { font-size: .9rem; font-weight: 600; line-height: 1.5; }

.toc { position: sticky; top: 3.6rem; height: calc(100vh - 3.6rem); overflow-y: auto; padding: 2.4rem 1rem 3rem 0; }
.toc-inner { border-left: 1px solid var(--border); padding-left: 1rem; }
.toc-title { margin: 0 0 .5rem; font-size: .76rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--fg-faint); }
.toc ul { list-style: none; margin: 0; padding: 0; }
.toc li { margin: 0; }
.toc a { display: block; padding: .2rem 0; font-size: .82rem; line-height: 1.5; color: var(--fg-muted); text-decoration: none; }
.toc a:hover { color: var(--accent-fg); }
.toc a.current { color: var(--accent-fg); font-weight: 600; }
.toc .lvl-3 a { padding-left: .85rem; font-size: .78rem; }

.home { max-width: 68rem; }
.lede { font-size: 1.05rem; color: var(--fg-muted); max-width: var(--measure); }
.meta-line { font-size: .82rem; color: var(--fg-faint); margin-bottom: 2rem; }
.sec-grid { display: grid; gap: 1.1rem; grid-template-columns: repeat(auto-fill, minmax(19rem, 1fr)); }
.sec-card { padding: 1.1rem 1.25rem 1.25rem; background: var(--bg-panel); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); }
.sec-card h2 { display: flex; align-items: baseline; gap: .55rem; margin: 0 0 .8rem; padding: 0; border: 0; font-size: 1.02rem; }
.sec-card ol { margin: 0; padding-left: 1.2rem; }
.sec-card li { margin-bottom: .75rem; font-size: .9rem; }
.sec-card li a { font-weight: 600; text-decoration: none; }
.sec-card li a:hover { text-decoration: underline; }
.card-sum { display: -webkit-box; margin-top: .1rem; font-size: .8rem; line-height: 1.65; color: var(--fg-muted); -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

@media (max-width: 1180px) {
  body.has-toc .layout { grid-template-columns: var(--sidebar-w) minmax(0,1fr); }
  .toc { display: none; }
}
@media (max-width: 860px) {
  .menu-toggle { display: grid; }
  .layout, body.has-toc .layout { grid-template-columns: minmax(0,1fr); }
  .sidebar { position: fixed; top: 3.6rem; left: 0; z-index: 30; width: min(var(--sidebar-w), 86vw); height: calc(100vh - 3.6rem); background: var(--bg); box-shadow: var(--shadow); transform: translateX(-102%); transition: transform .22s ease; }
  body.nav-open .sidebar { transform: none; }
  body.nav-open .sidebar-scrim { display: block; position: fixed; inset: 3.6rem 0 0; z-index: 29; background: rgba(0,0,0,.35); }
  .brand-sub { display: none; }
  .pager { grid-template-columns: 1fr; }
}
@media print {
  .topbar, .sidebar, .toc, .pager, .crumbs, .anchor { display: none !important; }
  .layout, body.has-toc .layout { grid-template-columns: 1fr; }
  body { font-size: 11pt; background: #fff; color: #000; }
  .content { padding: 0; }
  a { color: #000; }
}
"""

APP_JS = """(function () {
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem('wiki-theme'); } catch (e) {}
  if (stored) root.setAttribute('data-theme', stored);

  var toggle = document.querySelector('.theme-toggle');
  if (toggle) toggle.addEventListener('click', function () {
    var dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var cur = root.getAttribute('data-theme');
    var next = cur === 'auto' ? (dark ? 'light' : 'dark') : (cur === 'dark' ? 'light' : 'dark');
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('wiki-theme', next); } catch (e) {}
  });

  var menu = document.querySelector('.menu-toggle');
  var scrim = document.querySelector('.sidebar-scrim');
  function setNav(open) {
    document.body.classList.toggle('nav-open', open);
    if (menu) menu.setAttribute('aria-expanded', String(open));
  }
  if (menu) menu.addEventListener('click', function () {
    setNav(!document.body.classList.contains('nav-open'));
  });
  if (scrim) scrim.addEventListener('click', function () { setNav(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setNav(false);
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      var f = document.getElementById('nav-filter');
      if (f) { setNav(true); f.focus(); f.select(); }
    }
  });

  var filter = document.getElementById('nav-filter');
  if (filter) {
    var secs = [].slice.call(document.querySelectorAll('.nav-section'));
    var was = null;
    filter.addEventListener('input', function () {
      var q = filter.value.trim().toLowerCase();
      if (q && was === null) was = secs.map(function (s) { return s.open; });
      secs.forEach(function (sec) {
        var lis = [].slice.call(sec.querySelectorAll('li'));
        var hit = 0;
        var secHit = q && sec.querySelector('summary').textContent.toLowerCase().indexOf(q) !== -1;
        lis.forEach(function (li) {
          var show = !q || secHit || li.textContent.toLowerCase().indexOf(q) !== -1;
          li.hidden = !show;
          if (show) hit++;
        });
        sec.hidden = q ? hit === 0 : false;
        if (q) sec.open = true;
      });
      if (!q && was) { secs.forEach(function (s, i) { s.open = was[i]; }); was = null; }
    });
  }

  var links = [].slice.call(document.querySelectorAll('.toc a'));
  if (links.length && 'IntersectionObserver' in window) {
    var map = {}, targets = [];
    links.forEach(function (a) {
      var el = document.getElementById(decodeURIComponent(a.hash.slice(1)));
      if (el) { map[el.id] = a; targets.push(el); }
    });
    var seen = new Set();
    var obs = new IntersectionObserver(function (es) {
      es.forEach(function (en) {
        if (en.isIntersecting) seen.add(en.target.id); else seen.delete(en.target.id);
      });
      var first = targets.filter(function (t) { return seen.has(t.id); })[0];
      links.forEach(function (a) { a.classList.remove('current'); });
      if (first && map[first.id]) map[first.id].classList.add('current');
    }, { rootMargin: '-72px 0px -70% 0px' });
    targets.forEach(function (t) { obs.observe(t); });
  }

  var active = document.querySelector('.sidebar a.active');
  if (active) {
    var b = active.getBoundingClientRect();
    if (b.top < 80 || b.bottom > window.innerHeight - 40) active.scrollIntoView({ block: 'center' });
  }
})();
"""


def serve(out_dir: Path, port: int) -> None:
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(out_dir), **kw)

        def log_message(self, *a):
            pass

    with socketserver.TCPServer(("127.0.0.1", port), H) as httpd:
        print(f"Serving http://127.0.0.1:{port}/  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


def main() -> None:
    ap = argparse.ArgumentParser(description="Export an Obsidian LLM-wiki vault to static HTML.")
    ap.add_argument("--vault", default=".", help="vault root (default: cwd)")
    ap.add_argument("--out", default="html", help="output folder (default: html)")
    ap.add_argument("--config", default="wiki-export.config.json", help="optional JSON config")
    ap.add_argument("--title")
    ap.add_argument("--subtitle")
    ap.add_argument("--lang", choices=sorted(LABELS))
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()

    vault = Path(a.vault).expanduser().resolve()
    cfg_path = Path(a.config)
    if not cfg_path.is_absolute():
        cfg_path = vault / cfg_path
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    for k in ("title", "subtitle", "lang"):
        if getattr(a, k):
            cfg[k] = getattr(a, k)

    out_dir = Path(cfg.get("out", a.out)).expanduser()
    if not out_dir.is_absolute():
        out_dir = vault / out_dir

    build(vault, out_dir, cfg)
    if a.serve:
        serve(out_dir, a.port)


if __name__ == "__main__":
    main()
