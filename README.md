# LLM Wiki skills for Claude Code

Two skills that turn a pile of documents into a knowledge base Claude maintains
for you — and then, when you want to share it, into a website.

They implement the **LLM Wiki** pattern described by
[Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
The idea is his; this is one opinionated way of carrying it out. In his words:

> Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.

The point of the pattern is that knowledge **compounds**. Rather than re-reading
your source documents every time you ask a question, Claude reads them once,
writes what it learned into linked pages, and keeps those pages current as you
add more. Ask it something a month later and it answers from the pages, not from
scratch.

---

## The two skills

| Command | What it does |
|---|---|
| `/mock-wikify` | Reads the documents in a folder and builds the wiki: topic folders, cross-linked pages, an index, a change log, and a one-card summary of every source |
| `/mock-export-wiki-as-html` | Turns that wiki into a static website — sidebar, working links, table of contents, light and dark themes, print stylesheet |

The `mock-` prefix is just a namespace to keep these apart from other skills; it
doesn't mean anything.

## What you need

1. **Claude Code**, installed and working.
2. **[Obsidian](https://obsidian.md)** — a free app for reading and editing
   folders of markdown files. You don't strictly need it (the wiki is ordinary
   text files, readable in any editor), but it's what makes the `[[links]]`
   between pages clickable and the whole thing feel like a wiki.
3. **Some documents.** PDFs, Word files, text, markdown, spreadsheets, images.
   Whatever you've got.

Python 3 is needed only for the website export, and macOS and most Linux systems
already include it.

---

## Installing

### Option 1 — ask Claude Code to do it

Easiest, and no terminal required. Open Claude Code and paste this:

```
Please install the LLM Wiki skills for me from this marketplace:
https://github.com/panuakdet-gmail/llm-wiki-skills

Add it as a plugin marketplace, install the "llm-wiki" plugin from it, then tell
me the two commands it gives me and what each one does.
```

Claude Code will ask permission before changing anything. When it's finished,
type `/` and you should see `/mock-wikify` in the list.

### Option 2 — the plugin commands

If you'd rather run them yourself, inside Claude Code:

```
/plugin marketplace add panuakdet-gmail/llm-wiki-skills
/plugin install llm-wiki@llm-wiki-skills
```

Installing this way means `/plugin` can update the skills for you later.

### Option 3 — copy the folders by hand

No plugin system involved. In a terminal:

```bash
git clone https://github.com/panuakdet-gmail/llm-wiki-skills.git
cp -r llm-wiki-skills/skills/mock-wikify ~/.claude/skills/
cp -r llm-wiki-skills/skills/mock-export-wiki-as-html ~/.claude/skills/
```

Restart Claude Code. To update later, pull the repo and copy again.

---

## Using it

**Put your documents in a folder** and open Claude Code there. The folder you're
in *is* the wiki — the skill never builds somewhere else.

**Run `/mock-wikify`.** It will:

1. Read enough of your documents to work out what the collection is *for*.
2. Ask you to confirm that purpose, and to approve the topic folders it proposes
   — both as multiple choice, so you're picking rather than typing.
3. Build the whole thing in one go: pages, links, index, log, and a summary card
   per source.

You can skip the guessing by saying what it's for up front:

```
/mock-wikify a reference base on medieval trade routes
```

Or point it at documents that live somewhere else:

```
/mock-wikify notes for the design committee, docs in ~/Downloads/committee-pack
```

**Then just talk to it.** Ask questions in that folder and Claude answers from
the pages it wrote. Add more documents later and ask it to ingest them; the wiki
grows rather than being rebuilt.

**When you want to share it**, run `/mock-export-wiki-as-html` and you get a
folder of web pages you can open in a browser or upload anywhere.

---

## What gets built

```
your-folder/
├── raw/                  your original documents, untouched
├── raw-gist/             one index card per source — what it is, what it fed
├── wiki/
│   ├── index.md          a curated table of contents, not a file listing
│   ├── log.md            what changed and when, newest first
│   └── 01-topic/         your topic folders, holding the actual pages
│       ├── 01-something.md
│       └── 02-something-else.md
├── CLAUDE.md             the rules that keep the vault consistent afterwards
└── .obsidian/            theme and display settings
```

Two details worth knowing:

**`CLAUDE.md` is what makes it self-maintaining.** It's written to match your
particular wiki — its purpose, its topics, its page format — and Claude reads it
automatically in that folder from then on. That's why the wiki stays consistent
long after the first build.

**Pages are numbered `01-`, `02-` so they sort in reading order,** and each one
declares its plain name as an alias. So `[[01-trade-routes|trade-routes]]` and a
bare `[[trade-routes]]` both work, and renumbering a page doesn't break links
pointing at it by name.

---

## Credits

**The pattern is [Andrej Karpathy's](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).**
His gist `llm-wiki.md` describes the idea — an agent that compiles sources into
a maintained wiki instead of re-reading them per question — and everything here
is an implementation of it. If you find this useful, read his write-up first;
it explains the *why* better than this README does.

The **[Dracula for Obsidian](https://github.com/jarodise/Dracula-for-Obsidian.md)**
theme by jarodise is installed into new vaults, and only when no theme has been
chosen yet. An existing theme is never overridden.

**[Obsidian](https://obsidian.md)** is by Dynalist Inc. and is free for personal
use. Nothing here is affiliated with or endorsed by them.

## Licence

MIT — see [LICENSE](LICENSE). That covers the skill instructions and the export
script in this repository. It says nothing about Karpathy's gist, which is his;
a pattern isn't something this licence could cover in any case.
