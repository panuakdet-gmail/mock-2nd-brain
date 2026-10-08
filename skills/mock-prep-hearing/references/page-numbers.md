# Page numbers

Page numbers are built once into one table, and every citation is taken from that table.

## The two numbers

- **Position (X)**: where the page sits in the PDF file, counting the cover as 1. This is what a PDF reader's "go to page" box takes.
- **Printed (Y)**: the number printed on the page itself. This is what a person holding paper sees.

Cite as **X(Y)** when they differ, and as a plain number when they are the same. For a range, write `33–35(31–33)`. For a page with no printed number, such as a cover, write `1(–)`.

## Build the map first

Before writing any wiki page:

1. Get the page count with `pdfinfo`.
2. Read every page of the PDF as an image with the Read tool's `pages` option, up to 20 pages per call. For each page record its position, its printed number, and every section heading that starts on it.
3. Work out each section's range: it runs from its own first page to the page where the next section starts. A section that starts mid-page shares that page with the one before it, so both ranges include it.
4. Write the result as the section-to-page map page in the reference folder: one row per section, with the section number, its title as the document spells it, the wiki page that covers it, and the pages in X(Y) form.

Do not take page numbers from the table of contents. It gives only the first page of each section, it is often out of date in a draft, and it gives printed numbers only.

Always confirm page numbers by eye, on the page image. If a Thai PDF's extracted text has lost vowels and tone marks, a search for a Thai heading fails without saying so. Use that text only to cross-check digits and Latin letters, such as the section number "4.2.1".

## Citing from the map

- Every wiki page has a source-pages line under `**Sources**`, giving the section and its pages. Name the line in the wiki's language.
- Inside an answer's evidence line, cite each section with its page: `§4.2.1 — page 33(31)`.
- When a quoted sentence sits on one known page of a multi-page section, cite that page, not the whole range.
- A page that draws on many sections says so in its source-pages line and points to the map, and still gives a page beside each section in its evidence lines.

## Legend

Put this at the top of the map page and in the `/ask` guide, in the wiki's language:

> Page numbers are written X(Y). X is the page's position in the PDF file: in Preview press Cmd+Option+G and type X. Y is the number printed on the page. A single number means both are the same.
