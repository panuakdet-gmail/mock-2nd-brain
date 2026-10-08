# The hearing-prep folder

## Layout

The hearing-prep folder is the last numbered folder in `wiki/`. Inside it, numbers run in one sequence across files and subfolders, so no two entries share a number. A subfolder holds at least two files; a topic with one page is a file, not a folder.

```
NN-hearing-prep/
├── 01-hearing-logistics.md
├── 02-what-and-why/
│   ├── 01-router-what-and-why.md
│   └── 02-questions-what-and-why.md
├── 03-what-it-requires/
├── 04-who-does-what/
├── 05-how-we-know-it-works/
├── 06-where-it-came-from/
├── 07-defending-against-scope-creep.md
└── 08-hard-questions.md
```

Slugs must be unique across the vault, which is why each router and questions file carries its group name. The HTML export also flattens these subfolders into one list under the hearing-prep folder, so two files with the same name in different subfolders would overwrite each other, and section titles in the export config apply to top-level folders only.

## Question groups

Group by the shape of the question, because that is how the user looks one up during the meeting. These five fit most curricula, frameworks and policy papers. Rename, drop or add groups to fit the document.

| Group | Questions it holds |
| ----- | ----- |
| What and why | What this is, who authorised it, why it is built this way, whom it covers, what it overlaps with |
| What it requires | What people must be able to do or must comply with, at which level, the wording of each item |
| Who does what | Who is responsible, who pays, what unready or poorly resourced units do, the extra workload |
| How we know it works | Measurement, monitoring, misuse of results, evidence of effect |
| Where it came from | Sources, borrowing from abroad, what is local, who reviewed it, quality of the references |

## Meeting logistics page

Date, time, place, agenda with times, who is in the room and what each group tends to care about, the user's role, and the exact title and status of the document. Its first line links to the one-page overview. Take all of it from the meeting papers.

## Router page

One per group. Tables only: a question someone might ask, the wiki page to open, the section, the pages. Its first line points to the group's questions page. It routes to content; it does not answer.

## Questions page

One per group. Open with one line explaining the answer block, then the questions under a few subject headings. Each question is an H3 so it appears in the page outline and can be searched.

Write the labels in the wiki's language. The block:

```markdown
### Question: <the question, as a sharp person would put it>

**Short answer** — 1 to 3 sentences. Start with the section or item number that already covers the point.

**Evidence** — §x.x what it says — page X(Y) · §y.y what it says — page X(Y) · see [[NN-page|page]]

**If pressed** — what can be conceded, or what the document does not answer, said plainly.

**Stance** — one of the four below.
```

The four stances:

- `accept` — the proposal fixes a real error or gap.
- `accept in part` — one piece is right and the rest widens the scope.
- `take under consideration` — outside what the user can decide in the room.
- `explain and keep` — the document already covers it, or has a stated reason for its choice.

When two groups answer the same question, both keep it, each with a one-line pointer to the other, and the stances must match.

## What makes a prepared question worth having

- **It is one a sharp person would ask.** A senior official asks who pays and who is accountable. An academic asks whether the levels are a real progression or an invented ladder. A teacher asks what changes on Monday. Write for each kind of person the meeting papers put in the room.
- **It names its target.** "Why does item 3.5 stop at the middle level?" is useful. "Is the framework rigorous?" is not.
- **The short answer starts with a section number**, because many proposals ask for what the document already has in other words.
- **The evidence is a quote or a precise pointer**, with its page. If the document is silent, the answer says "the document does not specify this", never a guess.
- **"If pressed" concedes something true.** Take the concession from the known-weak-points page.
- **It promises nothing the document does not.** No budgets, dates or results that are not written in it.
- **It cites nothing the room cannot check.** Minutes of internal meetings, earlier drafts and working plans are not evidence unless the document itself contains them.

Cover both wide questions (legitimacy, cost, sustainability, equity) and narrow ones (a single verb, a single cell of a table, a single reference).

## Defending against scope creep

This page is used when someone proposes an addition. Put the parts in the order they are used:

1. **Diagnostic questions to ask the proposer**, so that the proposer has to justify the addition and the user does not have to refuse it. Derive them from the document's own structure: which existing item is closest and what it lacks; which part of the structure the proposal changes; whether it can be written to fit every dimension the document uses (levels, age bands, mappings to outside standards); whether it belongs in this document or in a companion guide.
2. **Kinds of proposal to accept**: factual errors, internal inconsistencies, unclear wording, real gaps.
3. **Structural reasons, taken from the document**, for declining an addition that widens the scope. Each has its section and page.

## Hard questions

Questions that fit no single group because they challenge the document at its roots: whether it will be out of date soon, whether the body behind it has the right to set it, whether its core concept is sound, who answers if it fails, what it costs, whether it survives a change of leadership, whether it widens inequality. Same answer block. Say directly when the document has no answer.

## Rules that apply to every prep page

- The vault's page format, the no-hard-wrap rule and the neutral third-party reader rule all apply. A page never mentions the user, the preparation process, or that a question "was asked before".
- Never copy a past comment word for word, and never name who raised it.
- Add every new page to `index.md`, link it from the meeting logistics page, and add an entry to `log.md`.
