# The per-project `/ask` helper

`/ask` answers a question the user has just heard in the meeting: an answer they can speak, plus the page to open. It lives **inside the project** (`.claude/skills/ask/`), because its voice, routing table and wiki belong to one document.

Create it for every project. Write all four files in the wiki's language; the outlines below are in English for reference. In the frontmatter, the keys and the values of `name`, `model`, `effort` and `tools` stay in English.

## How it works

Speed matters more than polish, so two subagents answer the same question at once: a fast model and a stronger one. The fast answer is shown as soon as it arrives, and the stronger one replaces or confirms it. If the stronger one arrives first, the fast one is stopped.

```
.claude/
├── skills/ask/
│   ├── SKILL.md          instructions for the caller
│   └── answer-guide.md   instructions the two subagents read
└── agents/
    ├── ask-sonnet.md     fast model, medium effort
    └── ask-opus.md       stronger model, medium effort
```

## `.claude/skills/ask/SKILL.md`

Frontmatter: `name: ask`, and a description saying it answers a question heard live at `<meeting>` about `<document>`, in `<language>`, in the voice of `<the user's role>`. It triggers on `/ask` and when the user pastes or paraphrases a question, objection or proposal from the room.

Body, for the caller:

1. If the project logs prompts, append the question to `PROMPT_LOG.md` first, and fill in the reply time when the final answer is shown. The caller does this; the subagents never write.
2. Start both subagents in one message, with the same prompt: the user's question word for word, behind a fixed prefix such as `Question from the floor:`. Do not search or answer yourself while waiting, and do not guess the result.
3. If the fast agent finishes first, show its answer under a line saying the stronger review is still coming, and end the turn.
4. If the stronger agent finishes first, stop the fast one with TaskStop and show the stronger answer. TaskStop may need loading first with ToolSearch `select:TaskStop`.
5. When the stronger answer follows the fast one: if it differs in something the user would say aloud (a section number, an item number, the stance), show it in full with one line on what changed. If it agrees in substance, write one line saying so and do not repeat the block.
6. If one agent fails, use the other. If both fail, say so and give the literal reply that retries.
7. Several questions in one message go out as one pair of calls; the agents split the blocks.

Caller rules: show the agent's answer as received, with no rewording and no account of the steps. Change no file in the vault while `/ask` is in use, apart from `PROMPT_LOG.md`. A new question is written into the wiki only when the user gives the literal command for it, which the skill states.

## `.claude/skills/ask/answer-guide.md`

What the subagents follow. Sections:

**Purpose.** Speed before completeness: the answer should arrive while the speaker is still finishing. Do not read the whole vault. Do not open the source document unless the wiki cannot answer, and copy in any caution about the source files from the vault's `AGENTS.md`, such as lines or pages that must not be read.

**Steps.**

1. Grep `wiki/` for the question's key words and open the 1 to 3 closest pages. For a wide question start at a router page.
2. Look in the hearing-prep folder for a prepared answer. If one matches or is close, use it and fit its wording to the question that was asked.
3. If the question is a proposal to add something, also open the scope page and say whether it is a kind to accept, or which structural reason answers it.
4. If the wiki has no answer, say so. Never guess what the document says. Offer what can safely be said, such as taking the point under consideration.

**Answer format**, one block per question:

```
## <the question heard, as one sentence>

**Short answer** — 1 to 3 sentences, opening with the section or item number that already covers it.

**Say into the microphone** — 2 to 4 sentences to read aloud. Acknowledge the concern first, then point to where the document handles it.

**Evidence** — §x.x … — page X(Y) · §y.y … — page X(Y)

**If pressed** — what can be conceded, or what the document leaves open. Omit for a purely factual question.

**Stance** — accept / accept in part / take under consideration / explain and keep

**Open this page** — [[NN-page|page]] `wiki/NN-folder/NN-page.md` — why · [[NN-backup|backup]] — why
```

Give the file path beside each link, because the user may be in Obsidian or on the exported site.

**Voice.** Fill in from the user's role. The defaults:

- Acknowledge the concern before answering.
- Lead with the number, because much of what is proposed is already in the document under other words.
- No rebuttal tone, and never say the asker has misunderstood.
- Claim no more than the evidence. Promise no budget, date or result the document does not contain. Where the document is silent, say it has not specified this.
- If the document is a draft, call it a proposal. Never call it policy in force.

**Routing table.** One row per question shape, pointing at the router page; plus rows for the scope page, the hard-questions page, the one-page overview, the section-to-page map (for "someone cited page N") and the known-weak-points page (for "someone pointed at an error").

**Rules.** The page-number legend. The vault's numeral and no-hard-wrap rules. Read-only: change no file. Return only the answer blocks, with no preamble and no account of which files were read.

## `.claude/agents/ask-sonnet.md` and `ask-opus.md`

Identical apart from name and model.

```markdown
---
name: ask-sonnet
description: Used only by the /ask skill. Answers one live question about <document> in <language>, from the wiki, using Sonnet at medium effort.
model: sonnet
effort: medium
tools: Read, Grep, Glob, Bash
---

You answer a question heard live at <meeting> about <document>. First read `.claude/skills/ask/answer-guide.md` in the project root and follow it exactly: find the answer in `wiki/`, and return only the answer block or blocks in the format it defines, in <language>. No preamble and no report of which files you read. Read-only: never create or edit any file.
```

For `ask-opus.md`, set `name: ask-opus` and `model: opus`.

## Test before the meeting

Run `/ask` on three questions: a blunt two-word one, a proposal to add something, and one the wiki cannot answer. Check that the section and page numbers match the wiki, that the third one says the wiki has no answer, and that the first answer arrives quickly. Tell the user it is ready and give one example to try.

Agents defined in `.claude/agents/` are loaded when a session starts, so the user must start a new session in the project before `/ask` works. Say this.
