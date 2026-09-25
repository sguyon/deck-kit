# AGENTS.md

## Read first

- `PROGRESS.md` (gitignored, local only): the running log of what changed in this checkout and why. Read it before starting. After each change you make, add an entry under today's date: what changed, why, and any gotcha. If the file is missing, create it.
- `README.md`: how the kit works (layout classes, scripts, mockup spec format in `mockups/README.md`).

## Setup (when the user asks you to set up or start the deck)

1. `npm install`, then `npx playwright install chromium-headless-shell` (once).
2. Start the watcher: `./watch.sh` (check with `./watch.sh status`).
3. Start the comment server in the background: `python3 comment-server.py`.
4. Open `deck.live.html` in the user's browser, then offer to replace the example `deck.md` with their presentation.

## Working rules

- Edit `deck.md`, `theme.css` or `mockups/specs/*.md`; never edit generated files (`deck.live.html`, `mockups/out/*.png`) by hand.
- Two themes: `deck-kit` (paper, default) and `deck-kit-terminal`. Layout rules are shared; paper-only rules go at the end of `theme.css`, scoped to `section[data-theme="deck-kit"]`. Check a visual change in both: `THEME=paper ./shot.sh N` and `THEME=terminal ./shot.sh N`.
- The example deck's mockups all show Pronto, a made-up food-delivery app: its web pages (`mockups/specs/orders.md`, `home.md`) and a coding agent working in its repo (`start.md`, `review.md`). Keep new example mockups in that universe (app Pronto, user Alex Kim, repo `pronto-web`).
- Mockups render once per theme (`<name>.png` paper, `<name>-terminal.png`); reference the plain name in `deck.md`, the live preview swaps it.
- The watcher (`./watch.sh`, check with `./watch.sh status`) re-renders `deck.live.html` on save. After changing a mockup spec, run `mockups/render.sh <spec>`.
- Check visual changes with `./shot.sh <slide numbers>` and look at the PNGs in `shots/` before calling a change done.
- README images live in `docs/screenshots/`; regenerate them with `shot.sh` (`OUT=docs/screenshots`, plus `THEME`/`MODE` for the variants; see the file names) when the slides they show change.
- Comments from the live deck land in `comments.md` (see README, "Comment mode"). Process them one batch at a time: apply, check with `shot.sh`, move the entry to `comments-done.md` as `[x]`, empty `comments.md`.
- Keep the slides, the speaker notes and the talk track in sync. When you change what a slide says, update its `<!-- Speaker notes: ... -->` in the same edit, and if the deck has a talk-track file (for example `talk-track.md`, one section per slide, in slide order), update that section too. When the user edits the notes or the talk track, check whether the slide still matches and fix it. Then run `./speaker-notes.sh`. Never leave one of the three describing a version of the slide that no longer exists.

## Gotchas

- macOS `sed` is BSD sed: `\|` alternation doesn't work in basic regexes and the edit silently does nothing. Use `sed -E` with `|`, or a short Python script.
- To add `<!-- _class: ... -->` to a slide, split `deck.md` on `---` and edit that slide. Searching backwards from the slide's title for the nearest `_class` comment can land on the previous slide.
