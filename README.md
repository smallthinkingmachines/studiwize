# studiwize — landing page

Marketing LP for [studiwize.com](https://studiwize.com). Static HTML/CSS/vanilla JS — no build step required.

## Local preview

```bash
nix develop                    # enter dev shell (nodejs_22 + python3)
python3 -m http.server 8000    # open http://localhost:8000
```

Or with direnv:

```bash
direnv allow    # activates the shell automatically on cd
python3 -m http.server 8000
```

## Waitlist form

Form posts to Formspree (`xgobrpdd`) via AJAX. To test end-to-end, submit a real address
and confirm it appears in the [Formspree dashboard](https://formspree.io).

## Files

```
index.html          main landing page
lib/
  brand.css         design tokens, buttons, wordmark, mark
  landing.css       page layout and section styles
  landing.js        interactivity (player demo, form, stepper)
favicon.svg         app icon (squircle mark)
og-image.png        social preview — 1200×630 (add before launch)
robots.txt
flake.nix / flake.lock
.envrc              use flake
```

## Deploy

No build step. Copy static files to any host. See `AGENTS.md` for deploy options.
