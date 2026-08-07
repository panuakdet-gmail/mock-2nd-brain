---
name: mock-export-wiki-as-html
description: >-
  Export an Obsidian LLM-wiki vault (the mock-wikify layout — raw/, raw-gist/,
  wiki/ with numbered topic folders, NN-slug.md pages with aliases) into a
  static HTML website: one page per note, a sidebar built from the topic
  folders, resolved [[wiki-links]], in-page table of contents, prev/next
  paging, light/dark themes, and a print stylesheet. Ships a dependency-free
  Python exporter (stdlib only — no pandoc, no npm, no network) that is
  installed into the vault as a re-runnable build script, plus a link/anchor
  verification pass. Trigger on /mock-export-wiki-as-html and proactively
  whenever the user asks to "export the wiki as html", "turn my vault into a
  website", "make a static site from these notes", "publish the wiki",
  "generate HTML from my Obsidian vault", or similar.
---

# mock-export-wiki-as-html

Turn a maintained LLM-wiki vault into a browsable static website. This is the counterpart to [mock-wikify](../mock-wikify/SKILL.md): that skill builds the vault, this one ships it.

The output is plain files — every link is relative, so `index.html` opens by double-clicking. No server, no build toolchain, no runtime dependency.

## Argument convention

`/mock-export-wiki-as-html <text>` may carry:

- **Output folder** — e.g. `/mock-export-wiki-as-html into docs/` (default: `html/` at the vault root).
- **Scope hint** — e.g. "wiki only", "include the gists".

The **target vault is the current working directory** unless the user names another path.

## The bundled exporter

`assets/export-wiki-html.py` is the engine. It is tested and dependency-free — **copy it, don't rewrite it**. Reach for a rewrite only if the vault needs markdown it genuinely cannot handle, and then extend the copy in the vault rather than reinventing a converter.

What it handles: YAML front matter (`aliases`, `title`, `tags`), ATX headings, paragraphs, nested bullet/ordered lists, task lists, GFM pipe tables (including `\|`-escaped **and** unescaped pipes inside `[[links]]` in cells), blockquotes, Obsidian callouts (`> [!warning]`, collapsible `-`/`+` variants), fenced code blocks, horizontal rules, bold/italic/strikethrough/`==highlight==`/inline code, `[[wiki-links]]` with `#anchors`, `![[embeds]]` (images inline, pages as link cards), markdown links and images, autolinks, bare URLs, and `#tags`.

What it does **not** render, and warns about instead: footnotes, `$math$`, mermaid, and dataview blocks. They pass through as literal text and are listed in the build report.

Resolution rules it implements, which match the vault contract: a `[[link]]` resolves against the numbered stem (`02-fact-framework`), the `aliases` slug (`fact-framework`), and the page title; attachments resolve Obsidian-style by filename anywhere in the vault and are copied into `assets/media/`; a link with no target renders as dimmed non-link text rather than a dead `href`.

## Procedure

### 1. Confirm scope before exporting

Ask with **AskUserQuestion** — the answer changes what gets published, and `raw/` is frequently sensitive:

- **Scope** — `wiki/` only (the default and the safe answer); `wiki/` + `raw-gist/`; or everything including `raw/` source files as downloadable attachments.
- **Repeatability** — install a re-runnable build script (default), or produce a one-time output folder.

Default to **`wiki/` only**. The vault's `CLAUDE.md` usually marks `raw/` as internal working documents — unpublished drafts, personal data, speaker names, production notes. Exporting `raw/` puts all of that into a folder built for distribution. If the user asks for the wider scope, say what is in `raw/` in one sentence, then do it.

### 2. Survey the markdown actually in use

Before building, census the vault so you know what must render and what will warn. This takes one command and prevents surprises:

```bash
cd wiki && for p in '!\[\[' '> \[!' '\$\$' '```' '\- \[ \]' '\[\^' '%%' '^\|' '\[\[' '!\[' '<br\|<div' '~~' '=='; do
  printf "%-10s %s\n" "$p" "$(grep -rE "$p" --include='*.md' . | wc -l)"
done
```

Also check what exists at the `wiki/` root — `index.md` and `log.md` may or may not be present. Note the folder numbering style (numbered sequence vs unnumbered peers); the exporter handles both.

### 3. Install the exporter

Copy `assets/export-wiki-html.py` into the vault as `tools/export-html.py`. Installing it in the vault (rather than running it from the skill directory) is what makes the export re-runnable as the wiki grows, and lets the user tweak the CSS.

For a one-time output, run it from the skill directory instead and skip the config file.

### 4. Write the config

Create `wiki-export.config.json` at the vault root. Section titles are the part worth effort: folder slugs are English and lowercase-hyphenated, but the site's readers need the vault's own language.

```json
{
  "title": "Site title (defaults to wiki/index.md's H1, else the vault folder name)",
  "subtitle": "One line under the title in the header",
  "intro": "Optional lead paragraph on the home page. Supports [[links]] and **bold**.",
  "lang": "th",
  "out": "html",
  "sections": {
    "01-first-topic": "หัวข้อที่หนึ่ง",
    "02-second-topic": "หัวข้อที่สอง"
  }
}
```

Everything is optional. `lang` auto-detects Thai vs English from page titles and drives the UI strings (`Home` / `หน้าแรก`, `On this page` / `ในหน้านี้`, …); add a new language by extending the `LABELS` dict in the script. Unlisted folders fall back to their de-numbered, de-hyphenated slug.

**Derive the section titles from the pages themselves**, not from a literal translation of the folder slug — read a page or two from each folder and name the topic the way the vault's own prose names it.

### 5. Build

```bash
python3 tools/export-html.py                 # → html/
python3 tools/export-html.py --serve         # build, then preview on :8000
```

Read the build report. It lists broken links, ambiguous link keys (two pages competing for one slug), attachments it could not find, unsupported markdown, and orphan pages with no inbound links.

### 6. Verify — do not skip this

A converter that silently mangles one construct across 35 pages looks fine until someone reads page 12. Three checks, all cheap:

**Dead links and anchors.** Every internal `href` must hit a real file, every `#fragment` a real `id`:

```bash
cd html && python3 - <<'PY'
import re
from pathlib import Path
bad=[]; anc=[]; tot=0; na=0
for f in Path('.').rglob('*.html'):
    t=f.read_text(encoding='utf-8'); ids=set(re.findall(r'id="([^"]+)"',t))
    for h in re.findall(r'href="([^"]+)"',t):
        if h.startswith(('http','data:','mailto:')): continue
        if h.startswith('#'):
            na+=1
            if h[1:] not in ids: anc.append(f"{f}{h}")
            continue
        tot+=1
        if not (f.parent/h.split('#')[0]).resolve().exists(): bad.append(f"{f} -> {h}")
print(f"links {tot} broken {len(bad)} | anchors {na} broken {len(anc)}")
for b in (bad+anc)[:10]: print("  ",b)
PY
```

**Unrendered markdown.** Any of these surviving into the HTML means a construct fell through the parser:

```bash
cd html && for p in '\*\*' '\[\[' '\\\|' '`[^`]' '<https' '\]\(' '^#{1,6} '; do
  printf "%-10s %s\n" "$p" "$(grep -rlE "$p" --include='*.html' . | wc -l)"
done
```

Every count must be `0`. Then confirm the link total: `[[...]]` occurrences in `wiki/` should equal rendered `class="wikilink"` plus `class="missing-link"` in `html/`.

**Look at it.** Serve the folder and open three pages in a browser — the home page, the page with the most tables, and the page with the most blockquotes/callouts — in both light and dark. `file://` URLs are blocked for browser automation, so serve over HTTP:

```bash
cd html && nohup python3 -m http.server 8731 --bind 127.0.0.1 >/dev/null 2>&1 &
```

Kill it when done (`pkill -f "http.server 8731"`). Serve from **inside** the output folder, never from the vault root — that would expose `raw/`.

### 7. Report

Say what was produced (page count, folder, size), and separate **export findings** from **source defects**. Source defects are the valuable part — the export is a linter that happens to emit HTML. Typical finds:

- A `[[link]]` to a page that was planned but never written, and how many pages point at it.
- An unescaped `|` inside a wiki-link in a table cell. The exporter tolerates it, but **Obsidian itself renders that row broken**, so it is worth fixing in the source.
- Orphan pages with no inbound links.
- Ambiguous slugs — two pages that a bare `[[slug]]` could resolve to either way.

Offer the fixes with a literal trigger phrase the user can reply with, and do not apply content edits to `wiki/` unless they ask — exporting is not a licence to rewrite the vault.

## Deploying it

Only if the user asks. The output is a plain static folder, so any static host works (Vercel, Netlify, GitHub Pages, S3, a plain web server).

Two things to get right before pushing anything outward:

- **Deploy the output folder, never the vault root.** Running a deploy CLI from the vault uploads `raw/` — often tens of MB of internal source documents. Run it from inside `html/`.
- **Confirm visibility, and raise it yourself if the user does not.** If the vault's `CLAUDE.md` describes the sources as internal or unpublished, a public production URL is a real disclosure, and search engines index it. Offer access-protected and `noindex` options alongside fully public, and let the user choose before deploying.

CLI logins (`vercel login`, `gh auth login`, `netlify login`) are interactive and cannot be driven from a tool call — ask the user to run them in the session with the `!` prefix, e.g. `! vercel login`.

## Notes

- **Re-run after every wiki change.** The script wipes and rebuilds the output folder, so the site never drifts from the vault. Mention this to the user, since it is the reason the script is installed in `tools/` rather than run once and discarded.
- The output folder is regenerated wholesale — never hand-edit files in it. Style changes belong in the `STYLE_CSS` string inside the script.
- Task lists render with completed items dimmed but **not struck through**, matching the vault's own Obsidian CSS snippet.
- The site is intentionally self-contained: no CDN, no web fonts, no analytics. It works offline and from a USB stick. Keep it that way when extending it.
