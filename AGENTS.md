# AGENTS.md

## Read first

- `PROGRESS.md` (gitignored, local only): the running log of what changed in this checkout and why. Read it before starting. After each change you make, add an entry under today's date: what changed, why, and any gotcha. If the file is missing, create it.
- `README.md`: how the kit works (layout classes, scripts, mockup spec format in `mockups/README.md`).

## Working rules

- Edit `deck.md`, `theme.css` or `mockups/specs/*.md`; never edit generated files (`deck.live.html`, `mockups/out/*.png`) by hand.
- Two themes: `deck-kit` (paper, default) and `deck-kit-copilot`. Layout rules are shared; paper-only rules go at the end of `theme.css`, scoped to `section[data-theme="deck-kit"]`. Check a visual change in both: `THEME=paper ./shot.sh N` and `THEME=copilot ./shot.sh N`.
- The example deck's mockups all show Acme Deploy, a made-up product: its web dashboard (`mockups/specs/overview.md`, `deploy.md`) and its `acme` CLI (`start.md`, `review.md`). Keep new mockups in that universe (same app name, nav, user, repo `acme-app`). Don't show deck-kit itself as a web app: there is no hosted deck-kit, and a screen of one confuses readers.
- Mockups render once per theme (`<name>.png` paper, `<name>-copilot.png`); reference the plain name in `deck.md`, the live preview swaps it.
- The watcher (`./watch.sh`, check with `./watch.sh status`) re-renders `deck.live.html` on save. After changing a mockup spec, run `mockups/render.sh <spec>`.
- Check visual changes with `./shot.sh <slide numbers>` and look at the PNGs in `shots/` before calling a change done.
- README images live in `docs/screenshots/`; regenerate them with `shot.sh` (`OUT=docs/screenshots`, plus `THEME`/`MODE` for the variants; see the file names) when the slides they show change.
- Comments from the live deck land in `comments.md` (see README, "Comment mode"). Process them one batch at a time: apply, check with `shot.sh`, move the entry to `comments-done.md` as `[x]`, empty `comments.md`.

## Gotchas

- macOS `sed` is BSD sed: `\|` alternation doesn't work in basic regexes and the edit silently does nothing. Use `sed -E` with `|`, or a short Python script.
- To add `<!-- _class: ... -->` to a slide, split `deck.md` on `---` and edit that slide. Searching backwards from the slide's title for the nearest `_class` comment can land on the previous slide.
