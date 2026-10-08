# Confidentiality banner

Added at every export, whether or not the site is ever published. Skip this file entirely if the user said the document is not confidential.

Every exported page gets a banner that stays at the top while scrolling, and a tag that tells search engines not to index it. Edit the vault's copy of the exporter, `tools/export-html.py`, not the HTML files, because the exporter overwrites the output folder on each run.

Add to the page `<head>` template:

```html
<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">
<meta name="referrer" content="no-referrer">
```

Add as the first element inside `<body>`, with the first two texts in the wiki's language and the last kept in English:

```html
<div class="confidential-bar" role="alert">
  <strong>CONFIDENTIAL — DO NOT SHARE</strong>
  <span>Internal unpublished draft. Do not forward. Do not post this link in any public place. Do not describe it as policy in force.</span>
  <span class="confidential-en">CONFIDENTIAL — internal unpublished draft. Do not forward. Do not post this link publicly.</span>
</div>
```

Add to the `STYLE_CSS` string:

```css
.confidential-bar{position:sticky;top:0;z-index:60;display:flex;flex-wrap:wrap;align-items:baseline;gap:.25rem .6rem;
  padding:.5rem .9rem;background:#7f1d1d;color:#fff;font-size:.8rem;line-height:1.45;
  border-bottom:2px solid #fca5a5;box-shadow:0 1px 6px rgba(0,0,0,.35)}
.confidential-bar strong{font-size:.82rem;letter-spacing:.02em;white-space:nowrap;
  background:#fff;color:#7f1d1d;padding:.1rem .45rem;border-radius:3px}
.confidential-bar span{opacity:.97}
.confidential-en{opacity:.8;font-size:.74rem}
@media print{.confidential-bar{position:static;background:#fff;color:#7f1d1d;border:2px solid #7f1d1d}}
@media (max-width:640px){.confidential-bar{font-size:.74rem;padding:.45rem .7rem}.confidential-en{display:none}}
```

If the English line would only repeat the first two, leave it out. Put the same warning in the config's `subtitle`. Rebuild, then confirm the banner is in every HTML file: the count of files containing `confidential-bar` must equal the count of HTML files.
