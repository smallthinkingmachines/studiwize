# studiwize — landing page

Marketing landing page for studiwize: a web app that turns any PDF or EPUB a student already owns into chapter-marked audio plus an LLM study guide.

## Stack

- Static HTML + CSS + vanilla JS — no framework, no build step
- Fonts: Sora (display/headlines), DM Sans (UI/body), DM Mono (labels/metadata) — loaded non-blocking via Google Fonts preconnect in `<head>`
- Waitlist form: Formspree AJAX (`https://formspree.io/f/xgobrpdd`)

## Dev environment

```
nix develop        # enters shell with node + python3
python3 -m http.server 8000    # local preview at http://localhost:8000
```

## Key files

- `index.html` — the full LP (nav, hero, problem, wedge, how-it-works, waitlist, footer)
- `lib/brand.css` — design tokens: colors, type scale, buttons, wordmark, mark/icon
- `lib/landing.css` — page-specific layout and component styles
- `lib/landing.js` — all interactivity: mark SVG injection, scroll reveal, demo audio player, how-it-works stepper, Formspree AJAX waitlist form
- `favicon.svg` — squircle app icon (page spine + play triangle)
- `flake.nix` / `.envrc` — Nix dev shell (nodejs_22 + python3)

## Brand rules

**Colors (committed — do not change)**
- Paper base: `#F4F1EA` (warm off-white)
- Ink: `#15212C` (deep navy-slate)
- Accent (teal): `#10B3A2` / deep `#0A786E` / on-accent `#052420`
- Night (player bg): `#0E1822`

**Type**
- Display/wordmark: Sora 700, tight tracking (−0.03em)
- UI: DM Sans 400–600
- Labels/mono: DM Mono 500
- No serifs in the product

**Voice** (from brand brief — enforce strictly)
- Plain, student-honest. Specific numbers over vague claims.
- NEVER use: "AI-powered", "seamless", "supercharge", "unlock your potential", "revolutionize"
- No pricing section — monetization model not yet decided
- Not an accessibility tool — don't frame it that way
- BYO-content only — no content library, no catalog

**Wordmark**
- Lowercase always: `studi` + `wize` compound
- Domain: `studiwize.com` only — never use `studiewize` spelling in design

## Form (Formspree)

Endpoint: `https://formspree.io/f/xgobrpdd`

The form submits via AJAX `fetch` with `Accept: application/json` — keeps the inline
success animation in the page. Hidden fields already added:
- `_subject` — labels the Formspree inbox
- `_gotcha` — spam honeypot (hidden, never shown to user)
- `source` — tags the submission source

## Deploy

Static files — deploy anywhere:
- **nginx Docker** (same pattern as `ricardoledan.com`): copy `index.html lib/ favicon.svg og-image.png robots.txt` into `/usr/share/nginx/html/`
- **Cloudflare Pages / Netlify / GitHub Pages**: drag-and-drop or connect the repo, no build command

## Package manager

Always use `npm` if adding Node tooling.
