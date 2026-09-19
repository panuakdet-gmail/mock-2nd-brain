# LLM Wiki skills for coding agents

Two skills that turn a pile of documents into a knowledge base your agent
maintains for you — and then, when you want to share it, into a website.

Built and tested on **Claude Code**, where they run as slash commands. The instructions themselves are plain markdown with nothing
Claude-specific in them, so other agents can follow them too.

They implement the **LLM Wiki** pattern described by
[Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
The idea is his; this is one opinionated way of carrying it out. In his words:

> Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.

The point of the pattern is that knowledge **compounds**. Rather than re-reading
your source documents every time you ask a question, your agent reads them
once, writes what it learned into linked pages, and keeps those pages current as
you add more. Ask it something a month later and it answers from the pages, not
from scratch.

---

## The two skills

| Command | What it does |
|---|---|
| `/mock-wikify` | Reads the documents in a folder and builds the wiki: topic folders, cross-linked pages, an index, a change log, and a one-card summary of every source |
| `/mock-export-wiki-as-html` | Turns that wiki into a static website — sidebar, working links, table of contents, light and dark themes, print stylesheet |

The `mock-` prefix is just a namespace to keep these apart from other skills; it
doesn't mean anything.

## What you need

1. **A coding agent.** [Claude Code](https://claude.com/claude-code) is the
   supported path, and the two commands below appear in its `/` menu. Codex,
   Antigravity, Gemini CLI and other agents can use them too: *Option 3* is a
   prompt that asks your agent to install them for you.
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

Options 1 and 2 are for Claude Code. Option 3 is for other agents. Pick one.

### Option 1 — ask Claude Code to do it

This is the easiest way, and you do not need a terminal. Open Claude Code and paste this:

```
Please install the Claude Code skills from https://github.com/panuakdet-gmail/mock-2nd-brain.

1. Download the repository, with its full history, to a temporary folder.
2. For each folder inside its skills/ folder, look for a folder with the same name in ~/.claude/skills/.
   - If there is none, copy the folder there.
   - If there is one, and every file in it matches a version that was once published in this repository, replace it with the new version.
   - If there is one, and it matches no published version, I have edited it. First move my copy to ~/.claude/skill-backups/<folder name>-<today's date>/. Then install the new version, show me what I had changed, and offer to merge my changes into it.
3. Delete the temporary download and tell me what you installed or updated.
```

Claude Code asks your permission before it changes anything. When it has finished, restart Claude Code and type `/`. You should see `/mock-wikify` in the list.

**To update later**, paste the same prompt again. If you changed the skills yourself, your version is saved first and Claude Code offers to merge your changes into the new one.

### Option 2 — copy the folders yourself

In a terminal:

```bash
git clone https://github.com/panuakdet-gmail/mock-2nd-brain.git
cp -r mock-2nd-brain/skills/mock-wikify ~/.claude/skills/
cp -r mock-2nd-brain/skills/mock-export-wiki-as-html ~/.claude/skills/
```

Then restart Claude Code. To update, run the same commands again. This replaces the old folders, so any changes you made to them are lost.

### Option 3 — ask another agent to do it

Open Codex, Antigravity, Gemini CLI, or whatever agent you use, and paste this:

```
Please install the skills from https://github.com/panuakdet-gmail/mock-2nd-brain for this agent.

1. Download the repository, with its full history, to a temporary folder.
2. Each folder inside its skills/ folder is one skill. Install each folder whole, including subfolders such as assets/, because the instructions use those files.
3. The skills were written for Claude Code, so adapt only the packaging: register each one the way this agent handles reusable skills or commands, so I can run it by name. Do not change the instructions inside each SKILL.md.
4. Before you install each skill, check whether I already have it.
   - If I do not, install it.
   - If I do, and its files match a version that was once published in this repository, replace it with the new version. Ignore packaging changes that an agent made when it installed the skill.
   - If I do, and it matches no published version, I have edited it. First copy my version to a backup folder outside the place this agent loads skills from, and tell me where it is. Then install the new version, show me what I had changed, and offer to merge my changes into it.
5. Delete the temporary download. Then tell me what you installed or updated, and how to run each skill here.
```

Most agents turn each skill into a slash command. If yours has no command system, it can still read `skills/mock-wikify/SKILL.md` and follow it. You name the file each time instead of typing a command, and the wiki it builds is the same.

**To update later**, paste the same prompt again. If you changed the skills yourself, your version is saved first.

### If you installed the old plugin version

This repository used to be a Claude Code plugin. That version no longer updates. Remove it before you use Option 1 or 2, otherwise every command appears twice. Inside Claude Code, run:

```
/plugin uninstall mock-2nd-brain@mock-2nd-brain
/plugin marketplace remove mock-2nd-brain
```

---

## Using it

**Put your documents in a folder** and open your agent there. The folder you're
in *is* the wiki — the skill never builds somewhere else.

**Run `/mock-wikify`.** (On another agent, use whatever name Option 3 set up —
everything below is the same either way.) It will:

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

**Then talk to it.** Ask questions in that folder and your agent answers from
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
├── AGENTS.md             the rules that keep the vault consistent afterwards
├── GEMINI.md             the same rules, under the names other agents read
├── CLAUDE.md
└── .obsidian/            theme and display settings
```

Two details worth knowing:

**The rule files are what make it self-maintaining.** They're written to match
your particular wiki — its purpose, its topics, its page format — and an agent
reads them automatically when it opens that folder. That's why the wiki stays
consistent long after the first build. The same rules are written three times
because different agents look for different filenames: `AGENTS.md`, `GEMINI.md`,
`CLAUDE.md`. Whichever you open the folder with, it knows the conventions.

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
