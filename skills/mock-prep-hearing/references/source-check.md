# Checking the wiki against the source

This pass checks every citation, one at a time, because the user will read these answers aloud to people who have the document open. Sampling is not enough.

Run it after the prep pages are written, over the whole wiki: stage 1 pages and prep pages alike. When subagents are on, Opus subagents do sections 1 to 3, each with its own set of wiki pages.

## 1. Facts

For every claim that cites the document:

- **The section says what the page says it says.** Open the section in the text form of the document and compare. A quote must match character for character, apart from numeral conversion.
- **Nothing is attributed to the document that comes from elsewhere.** Minutes, earlier drafts, working plans, general knowledge and reasonable inference are the usual sources of this error. Remove the claim, or rewrite it as "the document does not state this".
- **Counts and lists are complete.** If a page says "5 items have no match", list them from the source and count.
- **"The document never mentions X" is tested** with a search of the full text for X and its synonyms, not from memory.
- **Qualifiers survive.** "May", "at least", "for example" and "or" change what a sentence commits to. Check they were not dropped.

Where a table in the wiki copies a table in the document, compare it by script when you can: extract both and diff them, cell by cell.

## 2. Page numbers

For every page reference in the wiki:

- **Open that PDF page as an image** and confirm the cited section or quote is on it. Do not confirm from the section-to-page map alone, since the map may be the thing that is wrong.
- **Check both numbers.** X must be the position in the file and Y the number printed on that page.
- **Check ranges at both ends.** The first page must contain the section's heading and the last page its final line.
- **A quote cited to a single page must be on that page**, not merely somewhere in its section.

Work page by page through the PDF: gather every citation in the wiki that points at a given PDF page, open that page once, and confirm them all together. Then confirm every wiki page has a source-pages line.

## 3. Consistency between wiki pages

- **The same question answered in two places** gives the same facts and the same stance.
- **The same number** (a count, a level, a date) is the same everywhere it appears.
- **Routers** point at pages that do contain the answer, with the section and pages matching the target page.

## 4. Mechanical checks

Run these by script and fix every hit:

- broken `[[wiki-links]]` and pages with no inbound link;
- numerals in the wrong script, if the vault uses Arabic numerals only;
- a line break inside a paragraph;
- an unescaped `|` inside a wiki-link in a table row;
- a page missing its summary, sources, source-pages or last-updated line.

## 5. Final review

Start a fresh agent with the Agent tool: `subagent_type: general-purpose`, `model: opus`, or `model: fable` if the user said OK to the Fable review in the confirmation. This review always runs, even when subagents are off. Give it the vault path, the path of the PDF, the text form of the document and this file, and tell it to look at PDF pages with the Read tool's `pages` option. Do not give it your findings or tell it what you expect. Ask it for errors of fact, wrong page numbers, contradictions between pages, and answers a hostile but informed listener could take apart. Fix what it finds, then re-run the mechanical checks.

## 6. Record

Write one entry in `wiki/log.md` whose heading contains the English words `Source check`, whatever the wiki's language, because the skill uses that heading to know stage 2 is finished. The entry says what was checked, what was corrected, and the counts (citations checked, page references checked, corrections made). Tell the user the result in one line. Corrections to the wiki are not listed in chat.

If the check finds a defect in the document itself, add it to the known-weak-points page with what to say if someone points at it. (The source check runs in stage 2, so the "what to say" line belongs here.) Do not raise it in chat.
