---
name: mock-prep-hearing
description: >-
  Prepare the user to defend a document (a curriculum, a framework, a policy
  paper) in a hearing, review or meeting. Runs in three stages with a stop for
  review after each: a summary wiki of the document, then prepared tough
  questions with ready answers cited to exact PDF pages and checked against the
  source, then an HTML export. Also creates a per-project /ask helper for
  live questions, and can publish the site behind a password when the user asks.
  Calls mock-wikify and mock-export-wiki-as-html. MANUAL TRIGGER ONLY: apply
  this skill only when the user invokes /mock-prep-hearing. Never invoke it on
  your own initiative, not when the user mentions a meeting, a hearing, a
  document to defend, or a wiki.
---

# mock-prep-hearing

The user must answer questions in a meeting about a document they wrote or co-wrote. This skill builds what they use during it: a wiki where one page answers one question, prepared answers to the hard questions, and an exact PDF page for every claim.

It works in three stages. **Each stage ends with a stop**, because the user reviews the wiki before the next stage builds on it.

| Stage | What it produces |
| ----- | ----- |
| 1. Summary | The wiki of the document, with a PDF page reference on every page |
| 2. Prep | Question pages, a check of every answer against the source, and the `/ask` helper |
| 3. Export | A static HTML site, with a confidentiality banner unless the document is not confidential |
| Optional: Publish | The site on Vercel behind a password |

## One command, and how the user stays oriented

**The user needs to remember one command: `/mock-prep-hearing`.** With no argument it runs the next unfinished stage. Work out which from the vault:

1. no `wiki/` folder: stage 1;
2. `wiki/log.md` has no entry whose heading contains `Source check`: stage 2. If question pages already exist, an earlier run stopped part-way, so continue from the first step that left nothing on disk, and always run the source check;
3. that entry exists, and `html/index.html` is missing or older than the newest `.md` file under `wiki/`: stage 3;
4. otherwise everything is done: show the map and stop.

The hearing-prep folder is the highest-numbered folder in `wiki/`, and question pages are the files named `NN-questions-*.md` inside it.

Arguments exist only to jump: `summary`, `prep`, `export` re-run that stage, and `publish` is the only way to publish. A bare invocation never publishes.

**At the first run, open with a short overview**: one sentence on what the skill builds, then the map below with nothing ticked. Keep it under ten lines, then start work.

**At the end of every stage, and whenever a bare invocation finds nothing to do, show the map**, in the language the user is writing in:

```
Where you are
  ✔ 1 Summary   wiki built, 48 pages
  ▶ 2 Prep      next: review the wiki, then type /mock-prep-hearing
    3 Export
    – Publish   optional, only on /mock-prep-hearing publish
```

- `✔` done, with one fact about the result. `▶` the next stage. No mark for later stages.
- Exactly one "next" line, and it gives the literal command.
- Once `/ask` exists, add a line for it under stage 2: `/ask ready`. In the session that created it, add `— start a new session first`.
- The Publish line is part of the map and is the only mention of publishing. Do not add a sentence recommending it.

Do not list the arguments to the user unless they ask.

## Calling the other two skills

Stage 1 runs `mock-wikify` and stage 3 runs `mock-export-wiki-as-html`, both through the Skill tool. Both skills say they run only when the user invokes them. **The user typing `/mock-prep-hearing` is that invocation**, so call them without asking. Do not edit either skill.

Where this file and those skills disagree, this file wins for this run. The differences are listed in each stage.

## Standing defaults

Show these once, in the stage 1 confirmation, as a short list. The user overrides any of them by saying so. Write the confirmed set into the vault's `AGENTS.md`, `CLAUDE.md` and `GEMINI.md` so later stages and later sessions follow it.

- **Stance: defend with evidence.** The user does not accept every proposal. Each page records where a statement comes from and why it was written that way, so the user can tell whether a proposal repeats what the document already says.
- **Resist additions that widen the scope or lengthen the document.** Proposals that fix a real error or gap are accepted.
- **Wiki language is the document's language.** For a Thai document, write mainly in Thai, keep key terms exactly as the document spells them, and give the English term in brackets on first use. Filenames, slugs and aliases stay English. This replaces the English-headings rule in `mock-wikify`.
- **Arabic numerals everywhere** (1 2 3, not ๑ ๒ ๓), including in text quoted from the document, so a search for "3.3" works during the meeting.
- **The document is confidential.** Analysing it is fine. Nothing from it goes anywhere public. An unpublished draft is never described as policy in force. Nothing from the document, the wiki, the HTML or `PROMPT_LOG.md` is sent through the Artifact tool, Claude Docs, a connector, a web search or any other upload. The only upload is `publish`, and it uploads only the built site from `html/` and the password gate files, never a source file.
- **Sources are read in place**, not copied into `raw/`. This answers the copy-or-read question in `mock-wikify`, so do not ask it.
- **Every prompt is logged.** Each message the user sends in this project is appended word for word to `PROMPT_LOG.md` at the vault root, with the time it was sent, the time the reply finished, the elapsed time, and one line on what was done. Newest at the bottom. The user can turn this off in the confirmation, or later by saying so.
- **Subagents are on.** Long jobs are shared between subagents, as set out under "Subagents and models" below. The user can turn this off.
- **Final review by Fable is off.** The final review always runs, and Opus does it. Fable does it only if the user replies OK to this line in the confirmation. Tell the user that Fable gives the most thorough review and costs the most.

### Prompt log

When logging is on:

- Start the log with the invocation that started this skill, and keep it up for every later prompt, in this session and future ones. Write the rule plainly in the vault's `AGENTS.md`, `CLAUDE.md` and `GEMINI.md`, because that is what carries it into future sessions: log at the start of each turn, fill in the reply time at the end, never wait to be asked.
- Entry format:

  ```markdown
  ### Prompt 12

  - **Sent:** 2026-03-14 10:20 (+07)
  - **Responded:** 2026-03-14 10:21 (+07)
  - **Elapsed:** ~1 min

  > the prompt, word for word

  **What Claude did:** one line.
  ```

- The log sits outside `wiki/`, so the export never includes it. Treat it as confidential, and never copy from it into the wiki.
- If the user turns logging off, remove the rule from the three files and leave the existing log file alone.

## Subagents and models

A subagent is a separate Claude session that this session starts with the Agent tool to do one part of the job. When subagents are on:

1. **This session does the shared groundwork first, itself:** the section-to-page map and the one-page overview. Give both to every subagent, with the rules in the vault's `AGENTS.md`, so that page numbers and counts agree across pages.
2. **Opus (`model: opus`) writes all wiki content:** every summary page, the glossary, the bibliography, the question pages, the hard-questions page and the scope page. Opus also does the whole source check, facts and page numbers.
3. **Sonnet (`model: sonnet`) does only work that needs no interpretation:** the gist card for each source, the router pages, which are tables built from pages Opus has already written, and the entries in `index.md`.
4. **The final review** is one fresh agent: `model: opus`, or `model: fable` if the user said OK to it.

Give each subagent its own files, so that no two write the same file. This session writes `log.md`, runs the mechanical checks and resolves anything two subagents disagree on.

If the user turned subagents off, this session does all the writing and checking itself. The final review still runs as a fresh agent, because it must not share this session's conclusions.

## What not to say to the user

The user usually cannot edit the document before the meeting, so:

- Weak points of the document go in the wiki's known-weak-points page. Do not list them in chat.
- Report only what the user must decide or do. Detail goes in the wiki.
- Never suggest recording questions after the meeting, and never suggest publishing. Both happen only when the user asks.

## Stage 1 — Summary

### 1. Find the sources

Search the working folder and its subfolders for three kinds of file. Never treat these as sources: `wiki/`, `raw-gist/`, `html/`, `deploy/`, `tools/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROMPT_LOG.md`, the site access note, or anything else this skill wrote.

- **The document.** Prefer two forms of the same version: a PDF, which is the only source of page numbers, and a text form (`.md`, `.docx`) for exact wording. If only a PDF exists, that is enough. If there is more than one PDF or more than one version, do not choose: ask, as described in step 3.
- **Meeting papers**: schedule, invitation, agenda.
- **Past-question material**: minutes, comment sheets, reports, chat logs from earlier reviews of this document.

Text extraction from some Thai PDFs drops vowels and tone marks. Test each PDF first with `pdftotext -f 1 -l 2`. If the Thai comes back damaged, read that PDF page by page as images with the Read tool and trust extracted text only for digits and Latin letters. If it comes back whole, extracted text is fine for reading and searching.

### 2. Read the meeting papers before asking anything

Take the date, place, audience, agenda and the user's role from them. Ask the user only for facts that are in none of the files.

### 3. One confirmation round

Use AskUserQuestion once, and fold in the purpose and taxonomy questions from `mock-wikify` so the user is not asked twice:

- the purpose, pre-filled from what you read (who the user is, what meeting, what date);
- the proposed topic folders;
- the standing defaults above, shown as a list to confirm, including that every prompt will be logged, that subagents are on, and that both can be turned off;
- the Fable final review, which is off unless the user replies OK;
- which files are in scope;
- **which PDF the page numbers come from**, only if there is more than one PDF or version. Say why you ask, and list the files by name. For example: "I will take every page number from one PDF, so that the pages I cite match the copy people have in the room. Which file is that copy?";
- meeting facts you could not find;
- past-question material, **only if you found none**: ask once whether minutes, reports or chat logs exist. If the answer is no, continue. Stage 2 then uses the bundled question bank.

### 4. Run mock-wikify

Invoke it with the confirmed purpose and source location as its argument, then follow it, with these differences:

- **Its step 3 questions are already answered** by the confirmation round. Do not ask them again, and do not ask whether folders are a sequence: they are always numbered.
- **Its report step is replaced by the stop below.** Defects in the document go to the known-weak-points page, not to chat.
- **Past-question material gets no gist card.** Gist cards are for the document and the meeting papers.
- **Pages are written by subagents**, as set out under "Subagents and models", unless the user turned them off.
- **Folders follow the document's own chapters**, numbered in reading order. Three things are fixed whatever the document is:
  - a first folder of foundations that opens with a **one-page overview** holding every headline number and structure;
  - a **reference folder** holding a glossary, the **section-to-page map**, and a **known-weak-points page** (errors, inconsistencies and gaps in the document itself, each with what to say if someone points at it);
  - the **last folder number is kept for hearing prep**, which stage 2 fills. Stage 1 puts only the meeting logistics page there.
- **One page answers one question in full.** The reader will open one page, not three.
- **Every page carries its source pages.** Add a line under `**Sources**` naming the section and the PDF pages, in the format below. See `references/page-numbers.md` for how to build the map first and cite from it.
- **Quote the document exactly** where wording may be challenged, with the section number beside the quote.
- **Do not put past-question material into the wiki.** It is read in stage 2 as a guide, never catalogued. Other files are ingested only if the user put them in scope.

### 5. Page number format

Cite a PDF page as **X(Y)** when the two numbers differ: X is the page's position in the file (what Cmd+Option+G in Preview takes), Y is the number printed on the page. Write a plain number when they are the same. Example: `§4.2.1 — page 33(31)`. The full rule, and the one-line legend to put at the top of the section-to-page map and in the `/ask` guide, are in `references/page-numbers.md`.

### 6. Stop

Report the folders, the page count, and anything the user must decide. Then show the map, with stage 2 as next.

## Stage 2 — Prep

Read `references/prep-pages.md` before writing. It has the folder layout, the answer block, and what makes a prepared question worth having.

### 1. Learn how this audience asks

Read the past-question material if there is any, and always read `references/question-bank.md`. Use both to learn the kinds of question this audience raises and how they phrase them. Then write the questions a sharp person in that room would ask about **this** document, including ones nobody has asked yet.

Never copy a past comment into the wiki word for word, and never attach a name or an organisation to a question. Rewrite each in neutral words.

### 2. Write the hearing-prep folder

Question pages grouped by the shape of the question, a navigation page for each group, a page for handling proposed additions, and a page of hard questions that challenge the document at its roots. Every answer has a short answer, the evidence with section and page, what to concede if pressed, and a stance.

Share the writing between subagents as set out under "Subagents and models".

### 3. Check everything against the source

Follow `references/source-check.md` in full. It checks two things for every citation, in the prep pages **and** the stage 1 pages: that the fact is what the document says, and that the page number is the page the text is on. It also finds contradictions between wiki pages and claims that come from somewhere other than the document.

Finish with the final review described there, by Opus or by Fable as the user chose. Fix what it finds.

### 4. Create `/ask`

Always create the project's own `/ask` helper, from `references/ask-helper.md`.

### 5. Stop

Report the number of questions prepared, the result of the source check in one line, and that `/ask` is ready. Then show the map, with stage 3 as next.

## Stage 3 — Export

Invoke `mock-export-wiki-as-html` and follow it, with these differences:

- **Scope is `wiki/` only**, with a re-runnable build script. Do not ask the scope question.
- **Every page shows a confidentiality banner** that stays at the top while scrolling, and tells search engines not to index it. Add both to the vault's copy of the exporter, `tools/export-html.py`, never to the copy inside the skill. The markup is in `references/banner.md`. If the user said in the confirmation that the document is **not** confidential, add neither.
- **On a rebuild, keep the vault's exporter.** If `tools/export-html.py` already exists, skip the export skill's install step, which would copy a fresh exporter over it and remove the banner. Run `python3 tools/export-html.py` directly.
- Section titles in the config come from the pages' own wording, in the wiki's language.

Run the export skill's three checks. Stop and report the page count and the output folder, then show the map with all three stages ticked. After a later wiki change, a bare `/mock-prep-hearing` rebuilds the site, because the wiki is then newer than `html/`.

## Publish — only when the user asks

Run this only on `/mock-prep-hearing publish` or the user's own request to put the site online. Afterwards show the map with Publish ticked and the site address beside it. A password-protected site still places a confidential document on the internet, so before uploading, state in one sentence what will go up and where, and wait for a yes. An approval given in an earlier session does not count.

Then follow `references/publish.md`.

## Files in this skill

- `references/page-numbers.md` — building the section-to-page map and citing from it.
- `references/prep-pages.md` — layout and templates for the hearing-prep folder.
- `references/source-check.md` — the fact check and the page-number check.
- `references/question-bank.md` — question types gathered from earlier projects, with no names. Add to it only when the user asks.
- `references/ask-helper.md` — the per-project `/ask` skill and its two agents.
- `references/banner.md` — the confidentiality banner added at export.
- `references/publish.md` — the Vercel password gate.
- `assets/deploy/` — the password gate files, copied into the vault at publish time.
