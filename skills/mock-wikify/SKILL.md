---
name: mock-wikify
description: >-
  Bootstrap the current folder into an Obsidian "LLM-wiki" — a structured,
  interlinked markdown knowledge base built from source documents, following
  Andrej Karpathy's LLM Wiki pattern. It scaffolds the vault (raw/, wiki/ with
  topic subfolders, a tailored CLAUDE.md, index.md, log.md, a Dracula
  Obsidian theme, and a CSS snippet that stops Obsidian striking through
  completed checklist items), then ingests the source documents into cross-linked starter
  pages in one full-build run. Content pages are numbered (01-, 02-…) for
  reading order, with slug aliases so links stay stable. The wiki's PURPOSE is inferred from the documents
  and confirmed with the user via multiple-choice; the user can also pass the
  purpose as an argument. The target vault is always the current working
  directory. Trigger on /mock-wikify and proactively whenever the user asks to
  "turn this folder into a wiki", "wikify", "build an LLM wiki / knowledge base
  from these docs", "make an Obsidian vault from these PDFs", or similar.
---

# mock-wikify

Turn a folder of source documents into a maintained LLM-wiki: a clean Obsidian vault where Claude ingests `raw/` sources into interlinked `wiki/` pages and keeps an index + operations log. This skill does the **first full build** — scaffold, confirm intent, ingest — and leaves behind a `CLAUDE.md` so the vault stays self-maintaining afterward.

## Argument convention

The optional argument (`/mock-wikify <text>`) carries two things, either or both may be present:

- **Purpose** — free text describing what the wiki is *for* (e.g. "my notes for the X committee", "a reference base on Y"). Use it verbatim as the confirmed purpose instead of inferring.
- **Source location** — a path or folder where the raw documents live, if they are not already in the current folder (e.g. `/mock-wikify reference for project Z, docs in ~/Downloads/zpack`).

The **target vault is always the current working directory** — never taken from the argument.

## Procedure

### 1. Resolve target and locate sources

The target is the cwd. Find the source documents, in this order:

1. If the argument named a **source location**, read from there.
2. Else if a `raw/` subfolder already exists, use it.
3. Else look for loose documents in the cwd (`.pdf`, `.md`, `.txt`, `.docx`, `.csv`, images, etc.).

**If the sources come from outside `raw/`** (the argument's location, or loose files in the cwd), ask the user whether to **copy them into `raw/`** or **read them in place**. Respect the answer for the rest of the run.

If no sources are found anywhere, say so and offer a **purpose-only scaffold** (structure + CLAUDE.md + empty index/log + empty `raw-gist/`, no ingest).

### 2. Infer the purpose

If the argument supplied a purpose, use it. Otherwise read or skim enough of the source documents to interpret what the collection is *for* and who would use it.

### 3. Confirm purpose and taxonomy via multiple choice

Use **AskUserQuestion** — this is the user's preferred way to confirm intent.

- **Purpose question:** offer 2–4 Claude-formulated candidate purposes, the best guess first and labeled "(Recommended)". These must be real interpretations of the documents, not placeholders — the user picks or refines rather than typing from scratch.
- **Taxonomy question:** propose the set of `wiki/` **topic subfolders**, derived from what the documents actually contain (not a fixed list). Different corpora need different buckets — meetings/people/decisions for an organization, concepts/methods/sources for a research base, etc. Let the user confirm or adjust.

You can ask both in one AskUserQuestion call (two questions). Keep `index.md` and `log.md` pinned at the `wiki/` root regardless of taxonomy.

Once the taxonomy is confirmed, **judge whether the topic subfolders form a progression or are peers** — this decides folder numbering (see step 4). If the topics have a natural order a reader would follow (e.g. setup → usage → reference, or a learning path), they are a **sequence**; if they are co-equal buckets with no canonical order (people / decisions / meetings), they are **peers**. When it's a genuine judgment call, ask the user briefly rather than guessing.

### 4. Scaffold the vault

Create, in the cwd:

- `raw/` — the source documents (copied in, or referenced in place per step 1).
- `raw-gist/` — one small gist card per source file (per step 6 / the gist template below). Mirrors `raw/` one-to-one.
- `wiki/` — with `index.md` and `log.md` at its root, plus the confirmed topic subfolders. **Number the topic subfolders only if they form a sequence** (per the step-3 judgment): a progression gets a two-digit prefix in reading order (`01-setup/`, `02-usage/`, …); peer buckets stay unnumbered (alphabetical). Folders never appear in `[[wiki-links]]`, so numbering them carries no link-breakage risk — it's purely for file-list ordering. **Never number `raw/`, `raw-gist/`, or `.obsidian/`** — they're infrastructure, not reading-order content.
- `CLAUDE.md` — generated per step 5.
- `.obsidian/` — appearance config: a theme (only if none is set yet) plus the completed-checklist CSS snippet (always). If the vault has **no theme set yet**, install the **"Dracula for Obsidian"** theme (by jarodise). The location is confirmed and baked in — do **not** search for it:
  1. Create `.obsidian/themes/Dracula for Obsidian/theme.css` from the canonical CSS at `https://raw.githubusercontent.com/jarodise/Dracula-for-Obsidian.md/master/obsidian.css`. (Fallback if offline: copy `theme.css` from another vault on this machine that already has this theme.)
  2. Create `.obsidian/themes/Dracula for Obsidian/manifest.json` (the upstream repo ships none, so generate it):

     ```json
     { "name": "Dracula for Obsidian", "version": "1.0.0", "minAppVersion": "0.16.0", "author": "jarodise", "authorUrl": "https://github.com/jarodise/Dracula-for-Obsidian.md" }
     ```
  3. Set `"cssTheme": "Dracula for Obsidian"` in `.obsidian/appearance.json`.

  **If a theme is already chosen, leave it untouched.**

  Then, **regardless of which theme is active** (the snippet is theme-independent), install the **completed-checklist CSS snippet**. Obsidian strikes through the text of ticked `- [x]` items by default, which makes the vault's checklists — [[pending-actions]]-style worksheets especially — hard to read back once most boxes are ticked. The snippet keeps the text upright and just dims it instead.

  1. Create `.obsidian/snippets/no-strikethrough-for-completed-checklist-items.css` verbatim:

     ```css
     .markdown-source-view .task-list-item.is-checked,
     .markdown-preview-view .task-list-item.is-checked,
     .markdown-rendered .task-list-item.is-checked {
       text-decoration: none !important;
       opacity: 0.5;
     }
     ```
  2. Enable it by adding `"no-strikethrough-for-completed-checklist-items"` to the `enabledCssSnippets` array in `.obsidian/appearance.json` (create the array if absent) — a snippet file alone does nothing until it is listed there. The filename minus `.css` **is** the identifier, so the two must stay in sync.

  Resulting `.obsidian/appearance.json` for a fresh vault:

  ```json
  {
    "cssTheme": "Dracula for Obsidian",
    "enabledCssSnippets": ["no-strikethrough-for-completed-checklist-items"]
  }
  ```

  **If the snippet file already exists, leave it untouched** — but still check that it is listed in `enabledCssSnippets`, since an unenabled snippet is a silent no-op.

### 5. Generate `CLAUDE.md`

Write a `CLAUDE.md` adapted to the confirmed purpose and taxonomy, carrying over these sections (this is the reusable LLM-wiki contract — keep the wording close so the vault behaves consistently):

- **Purpose** — filled from the confirmed purpose.
- **Folder structure** — the confirmed subfolders, with `index.md`/`log.md` at `wiki/` root, plus `raw/` and `raw-gist/` at the vault root. Note that Obsidian `[[wiki-links]]` resolve by page name across folders, so **page names must be unique across the vault**. Content pages carry a two-digit reading-order prefix in the filename (`NN-slug.md`, e.g. `01-…`, `02-…`) so Obsidian's file list sorts in intended reading order, and each declares a YAML `aliases: [slug]` entry (the un-prefixed slug) as a link fallback. Numbering runs **within each subfolder** (that topic's reading order); slugs stay unique vault-wide. `index.md` and `log.md` are unnumbered and pinned at the `wiki/` root. The **topic subfolders themselves** are numbered (`01-setup/`, `02-usage/`, …) only when they form a reading progression; peer-category buckets stay unnumbered. Keep this consistent when adding folders: if the vault's existing topic folders are numbered, a new one takes the next number in the sequence (or slots in with a renumber); if they're unnumbered peers, leave the new one unnumbered too. `raw/`, `raw-gist/`, and `.obsidian/` are never numbered. Folders don't appear in `[[wiki-links]]`, so renaming or renumbering a folder breaks no links.
- **Sources (`raw/`)** — what `raw/` holds, that it is the **source of truth**, and the ingest workflow: extract key info → create/update pages in the right subfolder → add `[[wiki-links]]` → write/refresh the source's `raw-gist/` card → update `index.md` and append to `log.md`. If the documents look non-public (personal data, internal deliberations, scores), include a **sensitivity note** to treat `raw/` accordingly.
- **Gists (`raw-gist/`)** — one small, quick-to-read card per source (`raw-gist/<source-filename>.md`), a safety net if a `raw/` file is deleted and the in-vault stand-in (with a link back) for sources read in place outside the vault. It is **not** a copy of any wiki page's summary. Gisting is **automatic on ingest**; the command **"make raw-gist"** backfills a gist for any source that lacks one. Include the gist template verbatim:

  ```markdown
  # Gist: <original filename>

  **Source**: `raw/<filename>`  — or, if read in place outside the vault: [<filename>](<original absolute path or URL>)

  **Original path**: <absolute path the source came from>

  **Ingested**: <date>

  **Feeds**: [[wiki-page-a]], [[wiki-page-b]]

  **Synopsis**: One or two sentences — what this file *is* (not a summary of its contents).

  **Topics**:

  - topic / section

  **Highlights**:

  - standout fact, figure, quote, or decision

  **Keywords**: kw1, kw2, kw3
  ```
- **Page format** — the template every page follows:

  ```markdown
  ---
  aliases: [page-title-slug]
  ---
  # Page Title

  **Summary**: One to two sentences describing this page.

  **Sources**: Which raw/ files and/or external sources this page draws from.

  **Last updated**: Date of most recent update.

  ---

  Main content. Clear headings, short paragraphs. Link related concepts with [[wiki-links]] throughout.

  ## Related pages

  - [[NN-related-concept-1|related-concept-1]]
  - [[NN-related-concept-2|related-concept-2]]
  ```

  Link to a page by its **numbered filename with clean display text**: `[[02-page-title-slug|page-title-slug]]`. The `aliases` entry means a bare `[[page-title-slug]]` still resolves too, as a fallback.

- **Question answering** — read `index.md` first → read relevant pages → synthesize → cite the pages → if the answer isn't in the wiki, say so and offer to file it.
- **Lint** — on request, check for contradictions between pages, orphan pages (no inbound links), concepts mentioned but lacking their own page, outdated claims, and page-format compliance; report as a numbered list with fixes.
- **Rules** — include verbatim:
  - **No hard-wrapped lines.** Write each paragraph, list item, and blockquote as ONE continuous line — never insert manual newlines mid-sentence to wrap at a column width. Obsidian renders mid-paragraph breaks as ugly visible line breaks; let the editor soft-wrap. Blank lines still separate blocks; code blocks and table rows are unaffected.
  - Treat `raw/` as the source of truth; keep wiki pages consistent with it.
  - **Write each page for a neutral third-party reader.** A page explains its subject standalone; it never references the ingestion process, the user's own questions/annotations, or that something was "confusing" / "flagged" — those motivate the writing but must not appear in it (no "the thing you asked about," "flagged as confusing," "answered directly"). Fix a confusing spot by explaining it well, not by narrating that it was confusing.
  - Always update `index.md` and `log.md` after changes.
  - Content pages are named `NN-slug.md` — a two-digit reading-order prefix plus a lowercase-hyphen slug (e.g. `01-selection-process.md`) — and carry an `aliases: [slug]` front-matter entry. Number within each subfolder for that topic's reading order; keep slugs unique across the whole vault. Standard link form is the numbered target with a clean display label: `[[01-selection-process|selection-process]]`; the alias means a bare `[[selection-process]]` also resolves. If you renumber a file, update the links pointing at its old number (grep the old `NN-slug`). `index.md` and `log.md` stay unnumbered.
  - Record names and personal data as they appear in the source documents.
  - **Language:** use English for structural headings and analysis; keep proper nouns and key terms in the **source documents' own language/script, copied verbatim**, and provide translations for key terms when the sources are not in English.

### 6. Ingest — full build

For each source document, extract its key facts and create or update the relevant page in the right subfolder. Every page follows the page-format template and the **no-hard-wrap** rule, and is **densely cross-linked** with `[[wiki-links]]` to related pages. Give each page a two-digit reading-order number within its subfolder (`NN-slug.md`) and an `aliases: [slug]` front-matter entry, and link between pages with the `[[NN-slug|slug]]` form (see the page-format rules in the generated `CLAUDE.md`). Copy proper nouns grapheme-for-grapheme from the source. Where two sources disagree, **flag the discrepancy on the page rather than silently picking one**.

**Then, for that same source, write its gist** to `raw-gist/` (see below). This is automatic — gisting is part of ingesting, never a separate ask.

### 6a. Gists (`raw-gist/`)

A **gist** is a small, quick-to-read index card for one raw source — a safety net in case a large file in `raw/` is later deleted, and the in-vault stand-in (with a link back) when a source lives **outside** the vault and was read in place. It is deliberately **not** a copy of the full wiki summary that already lives on a wiki page; keep it short and scannable.

One gist file per source, named after the source: `raw-gist/<source-filename>.md` (e.g. `raw-gist/2024-budget.pdf.md`). Gist template:

```markdown
# Gist: <original filename>

**Source**: `raw/<filename>`  — or, if the source was read in place outside the vault: [<filename>](<original absolute path or URL>)

**Original path**: <absolute path the source came from>

**Ingested**: <date>

**Feeds**: [[wiki-page-a]], [[wiki-page-b]]

**Synopsis**: One or two sentences — what this file *is* (not a summary of its contents).

**Topics**:

- topic / section
- topic / section

**Highlights**:

- standout fact, figure, quote, or decision

**Keywords**: kw1, kw2, kw3
```

Rules: keep it short. For external / in-place sources the **Source** line must be a **working link back** to the original — that link is the whole point when there is no `raw/` copy to fall back on. The **Feeds** line links to the wiki page(s) this source produced, so gist → full coverage is one hop.

**On-demand command — "make raw-gist":** when the user says this, scan `raw/` (and any external/in-place sources) and create a gist for every source that lacks one. Leave existing gists untouched unless the source itself changed.

### 7. Wire up index and log

- `wiki/index.md` — a curated, topic-grouped table of contents (not an auto-generated file list), one line per page with a short summary, organized by the confirmed taxonomy. Link each entry with the `[[NN-slug|slug]]` form; because pages are numbered, they list in reading order within each topic.
- `wiki/log.md` — an append-only operations log, newest first. Write the first entry: vault initialized, sources ingested, pages created, and anything flagged for the user to verify.

### 8. Report

Summarize what was built (folders, page count, gist count, theme + snippet), list any facts you flagged for the user to verify, and surface anything time-critical you noticed in the documents.

## Notes

- This is a **full build**: don't stop at a skeleton. After scaffolding, ingest the sources into real pages — and a gist per source into `raw-gist/` — in the same run.
- Honor the user's global preferences (e.g. the Dracula theme) and never override an Obsidian theme the vault already has.
- If the cwd already looks like a populated vault, don't clobber it — confirm with the user before overwriting an existing `CLAUDE.md` or pages.
