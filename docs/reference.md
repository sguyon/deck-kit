# deck-kit reference

The details behind the [README](../README.md). You don't need to read this to use deck-kit: your agent will, via [`AGENTS.md`](../AGENTS.md).

## What deck-kit adds to Marp

[Marp](https://marp.app) turns Markdown into slides. On top of the live preview, comment mode, the two themes and the mockups described in the README, deck-kit adds:

- **A clean presenting mode**: open `deck.live.html?present` and every helper disappears.
- **Transitions**: a quick fade, titles that stay put, and a zoom from a screen into its detail.
- **Screenshots on demand** (`shot.sh`): how the agent checks its own work.
- **Speaker notes for rehearsal** (`speaker-notes.sh`): collects every slide's notes into one file.
- **Agent rules** (`AGENTS.md`): how any coding agent should work in the repo.

## Under the hood

Everything is plain files and a few small scripts: no app to install, no build step. `watch.sh` runs Marp in watch mode: each time `deck.md` is saved, it re-renders `deck.live.html` with the two themes (`theme.css`, `theme-terminal.css`) and adds one script, `live-badges.js`, which handles the change badges, the theme switch, the transitions and comment mode in the browser. Comments go to a tiny local server (`comment-server.py`) that appends them to `comments.md`. Mockups are separate: `mockups/render.sh` turns each text spec into an HTML page and screenshots it with a headless browser, and the slides reference the PNGs it writes. The two diagrams below show both paths.

**1. The live deck: from Markdown to your browser**

```
  YOU WRITE                     WATCHER (./watch.sh)                  YOU SEE
 ┌──────────────────┐        ┌──────────────────────────┐        ┌──────────────────────────────┐
 │ deck.md          │  save  │ marp-cli --watch         │ writes │ deck.live.html               │
 │  slides, layout  │───────►│  + theme.css             │───────►│  (file:// in any browser)    │
 │  _class, notes   │        │  + theme-terminal.css     │        │                              │
 └──────────────────┘        │  + live-engine.js ───────┼──┐     │ Marp runtime:                │
 ┌──────────────────┐        │    renders like Marp,    │  │     │  ← → O overview  P presenter │
 │ mockups/out/*.png│        │    then appends a        │  │     │                              │
 │  (diagram 2)     │        │    <script> tag          │  └────►│ live-badges.js:              │
 └────────┬─────────┘        └──────────────────────────┘        │  "Updated" badges            │
          │  ![](../mockups/out/x.png) in deck.md                   │  T theme  D dark/light       │
          └──────────────────────────────────────────────────────┤  mockup swap per theme       │
                                                                 │  C comment mode ──────────┐  │
                                                                 └───────────────────────────┼──┘
                                                                           POST 127.0.0.1:8765 │
  COMMENT MODE                                                                               │
 ┌──────────────────┐        ┌───────────────────┐  appends  ┌─────────────────┐             │
 │ AI assistant or  │◄ read ─│ comments.md       │◄──────────│ comment-server  │◄────────────┘
 │ teammate         │        │ checklist: slide, │           │ .py (local only)│
 └──────────────────┘        │ element, comment  │           └─────────────────┘
                             └───────────────────┘   server down? → browser storage + clipboard
```

**2. Mockups, screenshots and exports**

```
  MOCKUPS (mockups/render.sh)
 ┌────────────────────┐    ┌───────────────────────┐    ┌──────────────┐    ┌──────────────────────┐
 │ mockups/specs/     │    │ tools/render.py       │    │ .build/*.html│    │ tools/shot.js        │
 │   start.md         │───►│ spec → cell grid →    │───►│ one per look │───►│ Playwright Chromium  │
 │   review.md        │    │ HTML, once per look:  │    │ (+ annotated,│    │ 2x, transparent PNG  │
 │ front matter +     │    │  paper   plain shell  │    │    zoom)     │    └──────────┬───────────┘
 │ user:/tool:/diff:  │    │  terminal agent CLI   │    └──────────────┘               │
 │ + annotate: frames │    └───────────────────────┘                                   ▼
 └─────────┬──────────┘                                       mockups/out/<name>.png  (paper)
           │                                                  <name>-terminal.png     (terminal)
           │                                                  --all: -dark, -terminal-light
           │ kind: web    ┌───────────────────────┐
           └─────────────►│ tools/web.py          │───► same .build → shot.js path, same names
                          │ browser window + app  │
                          │ blocks, per look      │
                          └───────────────────────┘

  CHECKS AND EXPORTS
  deck.live.html ──► ./shot.sh 3 5 ──► Playwright ──► shots/slide-3.png   (THEME=, MODE=, OUT=)
  deck.md ─────────► ./speaker-notes.sh ────────────► speaker-notes.md    (rehearsal)
  deck.md ─────────► npm run build | pdf ───────────► deck.html | deck.pdf
                     (plain Marp, no live script; theme from the front matter)
```

| Piece | Role |
|---|---|
| `deck.md` | The only file you edit for content. Front matter picks the theme; `<!-- _class: ... -->` picks each slide's layout. |
| `theme.css`, `theme-terminal.css` | Both themes and every layout (see [Themes](#themes)). |
| `watch.sh` + `live-engine.js` | Re-render on save; inject `live-badges.js` into the live copy only. |
| `live-badges.js` | Everything interactive on top of Marp: badges, theme/mode switcher, mockup swap, comment mode, shortcuts. |
| `comment-server.py` | Local-only endpoint that turns clicks into a `comments.md` checklist. |
| `mockups/` | Text specs → PNGs of terminal screens (`render.py`) or web apps (`web.py`), in both theme styles, with optional annotation frames. |
| `shot.sh` | Fast screenshots of the rendered deck, for visual checks without opening a browser. |
## Transitions

The example deck uses `transition: fade 0.12s` in its front matter, a quick cross-fade between slides (Marp's [bespoke transitions](https://github.com/marp-team/marp-cli/blob/main/docs/bespoke-transitions/README.md), View Transitions API: Chrome/Edge 111+, Safari 18.2+, Firefox 144+; other browsers switch instantly, reduced-motion users get a plain fade).

On top of that, in the live preview:
- The kicker, the title and the footer hold still, so only the content changes.
- Anything that repeats on the next slide (the same image, table row or list item) moves into its new place instead of fading. A table shown again with extra rows keeps its rows still and fades in the new ones.
- Zoom: wrap a close-up in `<div class="zoom" data-zoom="78% 64%">` (where to zoom, in % across and down) and the previous slide's mockup zooms into it, clipped to the panel.

Remove the `transition:` line to turn it all off.

## Comment mode

1. Run `python3 comment-server.py` (listens on `127.0.0.1:8765`, local only).
2. In the deck, press **C**, click an element, type your comment, press **Enter**.
3. Each comment is appended to `comments.md` with the slide number, title, element and its text.

If the server isn't running, the comment is saved in the browser and copied to the clipboard instead.

**Working through comments with an AI assistant.** A loop that works well: the assistant runs a background watcher that waits for comments to arrive, handles them, then waits again.

```bash
while [ ! -s comments.md ]; do sleep 2; done; sleep 5; cat comments.md
```

For each comment: apply the change, check it with `./shot.sh N`, append the entry to `comments-done.md` marked `[x]`, empty `comments.md`, and restart the watcher. The 5-second pause lets you leave several comments in a row before the assistant starts. Only one comment server can listen on port 8765: if you have several decks, stop the other one first, or its `comments.md` gets your notes.

## Other scripts

- `./shot.sh 1 4 6`: screenshots of slides 1, 4, 6 into `shots/` (reads `deck.live.html`, no re-render). `THEME=paper|terminal` and `MODE=light|dark` pick the look, `OUT=dir` changes the folder. The README images live in `docs/screenshots/`.
- `./speaker-notes.sh`: collects `<!-- Speaker notes: ... -->` comments into `speaker-notes.md`.
- `npm run build` / `npm run pdf`: static HTML or PDF export.

## Themes

Two Marp themes share every layout:

- **`deck-kit`** (default), *paper*: warm off-white canvas, serif headlines, terracotta accent. Light by default; dark mode is the class `dark`.
- **`deck-kit-terminal`**, *terminal*: the terminal look, with Primer color tokens, mono labels and a dot grid on title slides. Dark by default; light mode is the class `light`.

Screenshots of both themes in both modes are in the [README](../README.md#what-you-get).

- **Pick one for the deck** with `theme: deck-kit` or `theme: deck-kit-terminal` in the front matter of `deck.md`. The static exports (`npm run build` / `pdf`) use it.
- **Switch live** in `deck.live.html` with **T** (theme) and **D** (mode). Each theme remembers its own mode.
- **How it's built**: `theme.css` holds all layouts plus both looks. The terminal rules are the base; the paper rules come last, scoped to `section[data-theme="deck-kit"]`. `theme-terminal.css` only imports `deck-kit`, so its slides skip the paper rules. Most of the difference is tokens: colors, `--fontStack-heading` and `--fontStack-label`.

Layout classes, set per slide with `<!-- _class: ... -->`: `lead`, `lead hero`, `lead split`, `agenda`, `cards` (`cols-2..5`, `hero-first`, `lists`, `foot`), `mockup`, `quote`, `dense`, `backup`, `backup-table`, `journey`, `metrics`, `opps`, `note`.

![Layouts slide: every layout is one class](../docs/screenshots/layouts.png)

Fonts use system stacks. To use your own font, put the files in `assets/fonts/`, add an `@font-face` rule at the top of `theme.css`, and put the family name first in `--fontStack-sansSerif` (or `--fontStack-heading` for headlines only).

## Mockup generator

1. Write a spec in `mockups/specs/<name>.md`: a front matter block (`app`, `cwd`, `branch`, `cols`, ...) and one line per element (`user:`, `assistant:`, `tool:`, `diff+:`, `success:`, ...).
2. Add an `annotate:` block with `frame: target | Title | Subtitle` lines to get numbered frames and labels.
3. Run `mockups/render.sh` (all specs) or `mockups/render.sh mockups/specs/review.md`. Each spec renders twice: `out/<name>.png` in the paper style (a plain terminal: one-line banner, shell prompt) and `out/<name>-terminal.png` in the terminal style (a CLI-assistant screen with header card, status line and prompt bar). Add `--all` to also get each theme's other mode (`-dark`, `-terminal-light`).
4. Embed the plain name, `![](../mockups/out/review.png)`. In the live preview the image follows **T** and **D**. For a static terminal export, point the image at `review-terminal.png` yourself.
5. `mockups/specs/examples/roles.md` shows every role; see `mockups/README.md` for the full format.

`mockups/specs/review.md` is the terminal example and `mockups/specs/home.md` the web one; both are shown in the [README](../README.md#what-you-get).

**Web-app mockups.** Put `kind: web` in the front matter and describe the page with blocks instead of terminal lines: `title`, `button` / `button*` (primary), `stats`, `table` + `row` (`{ok}Fixed` becomes a status pill), `chart`, `card`, `text`, `toast`. The front matter sets the browser and app chrome: `url`, `tab`, `nav`, `user`. Two more blocks take indented lines: `code:` (a file panel with line numbers) and `slides:` (a grid of slide thumbnails, `Title | Updated`). `annotate:` works the same way; targets are block names, with `#n` for the n-th one (`row#2`, `stats#4`).

The example deck's mockups all show one made-up product, Pronto, a food-delivery app: its web pages (`specs/orders.md` on the title slide, `specs/home.md` annotated) and a coding agent working in its repo (`specs/start.md`, `specs/review.md`).

On a slide, with the `mockup` class:

![Mockup slide](../docs/screenshots/mockup.png)
