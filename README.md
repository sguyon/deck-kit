# deck-kit

A kit for building presentations with an AI agent, in two parts:

- **The deck**: slides written in Markdown (`deck.md`) and rendered by [Marp](https://marp.app), with a live preview that re-renders on save and a comment mode to point the agent at what to change.
- **The mockups**: product screens (a terminal or a web app) generated from a few lines of text in `mockups/specs/`, so the agent can write and edit them like the slides.

### The deck

![Title slide of the example deck](docs/screenshots/title.png)
<sub>A slide in the live preview</sub>

![Slide overview: every slide of the deck in one HTML page](docs/screenshots/overview.png)
<sub>The whole deck is one HTML page: press <b>O</b> for the overview</sub>

What you get:

- **Slides in plain text that update live.** You (or your agent) write `deck.md`; the deck in your browser refreshes on every save and marks the slides that changed.
- **Comment on the page to change a slide.** Click any element and type a note ("smaller font", "move this up"). It goes to a file your agent reads and applies.

![Comment mode: a note typed on a slide element](docs/screenshots/comment.png)

- **Present and export.** Presenter view with your notes, the next slide and a timer; export to PDF or HTML.

![Presenter view: current slide, next slide, speaker notes and timer](docs/screenshots/presenter.png)

- **Two themes, each in light and dark,** with quiet transitions between slides: a warm *paper* style and a dark *terminal* style. Ask your agent to [adjust them](https://marpit.marp.app/theme-css), or use any existing [Marp theme](https://github.com/marp-team/marp-core/tree/main/themes).

| | light | dark |
|---|---|---|
| **paper** | ![paper, light](docs/screenshots/cards-paper-light.png) | ![paper, dark](docs/screenshots/cards-paper-dark.png) |
| **terminal** (`copilot`) | ![copilot, light](docs/screenshots/cards-copilot-light.png) | ![copilot, dark](docs/screenshots/cards-copilot-dark.png) |

### The mockups

**Product screens from a description.** Describe a screen in a few lines, a web-app page or a terminal session, and get a clean mockup image, with numbered callouts if you want them. Change the description, get a new image; no design tool needed. Your agent can write and edit the descriptions like the slides.

![Web-app mockup with callouts](mockups/out/deploy-annotated.png)

![Terminal mockup with callouts](mockups/out/review-annotated.png)

## How it works

![How a slide is put together: a prompt, the two text files the agent writes, what deck-kit renders from each, and the finished slide](docs/screenshots/assembly.png)

### With an agent: from brief to finished deck

Open the repo in your coding agent (Claude Code, Codex, Cursor…), start `./watch.sh`, open `deck.live.html`, and talk to the agent. The example follows a made-up product, Pronto, a food-delivery app, and a proposal to add one-tap reorder to its home screen.

1. **Brief it.** The problem, the audience, the time limit, what they'll judge.
   > *"I need a 5-minute pitch for Pronto's head of product: add a one-tap 'Reorder your usual' button to the home screen. They care about repeat orders and checkout drop-off, and they'll ask what it costs to build. Draft `deck.md`: one idea per slide, speaker notes under each."*
2. **Shape the outline.** Ask for the structure before the words.
   > *"Go problem → who reorders → the proposal → what it changes → metrics → rollout. Six slides; put the repeat-order numbers on their own slide."*
3. **Describe the screens.** Mockups are text specs, so ask for them like slides.
   > *"Add a mockup of the new home screen: a greeting, the usual order, the delivery time, and a Reorder button. Number the button and the delivery time."*
4. **Review in the browser.** Press **C**, click what's wrong, type a short note. The agent reads `comments.md` and applies them; changed slides get an "Updated" badge.
   > *"bigger button"* · *"move the metrics before the rollout"* · *"too much text, split it"*
5. **Let it check its work.** The agent reviews the slides it changed and fixes the layout before it tells you it's done.
   > *"Check slides 3–4 in both themes and fix anything that overflows."*
6. **Rehearse and ship.** Press **P** for presenter view with your notes and a timer, then export.
   > *"I ran it and it's 7 minutes. Cut to 5: tell me which slide to drop and trim the notes."*

### What deck-kit adds to Marp

[Marp](https://marp.app) turns Markdown into slides. deck-kit adds what's described above (live preview with change badges, comments, two themes, mockups), plus:

- **A clean presenting mode**: open `deck.live.html?present` and every helper disappears.
- **Transitions**: a quick fade, titles that stay put, and a zoom from a screen into its detail.
- **Screenshots on demand** (`shot.sh`): how the agent checks its own work.
- **Speaker notes for rehearsal** (`speaker-notes.sh`): collects every slide's notes into one file.
- **Agent rules** (`AGENTS.md`): how any coding agent should work in the repo.

### Under the hood

You don't need to read this part. Your agent will know.

Everything is plain files and a few small scripts: no app to install, no build step. `watch.sh` runs Marp in watch mode: each time `deck.md` is saved, it re-renders `deck.live.html` with the two themes (`theme.css`, `theme-copilot.css`) and adds one script, `live-badges.js`, which handles the change badges, the theme switch, the transitions and comment mode in the browser. Comments go to a tiny local server (`comment-server.py`) that appends them to `comments.md`. Mockups are separate: `mockups/render.sh` turns each text spec into an HTML page and screenshots it with a headless browser, and the slides reference the PNGs it writes. The two diagrams below show both paths.

**1. The live deck: from Markdown to your browser**

```
  YOU WRITE                     WATCHER (./watch.sh)                  YOU SEE
 ┌──────────────────┐        ┌──────────────────────────┐        ┌──────────────────────────────┐
 │ deck.md          │  save  │ marp-cli --watch         │ writes │ deck.live.html               │
 │  slides, layout  │───────►│  + theme.css             │───────►│  (file:// in any browser)    │
 │  _class, notes   │        │  + theme-copilot.css     │        │                              │
 └──────────────────┘        │  + live-engine.js ───────┼──┐     │ Marp runtime:                │
 ┌──────────────────┐        │    renders like Marp,    │  │     │  ← → O overview  P presenter │
 │ mockups/out/*.png│        │    then appends a        │  │     │                              │
 │  (diagram 2)     │        │    <script> tag          │  └────►│ live-badges.js:              │
 └────────┬─────────┘        └──────────────────────────┘        │  "Updated" badges            │
          │  ![](mockups/out/x.png) in deck.md                   │  T theme  D dark/light       │
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
 │ user:/tool:/diff:  │    │  copilot CLI-assistant│    └──────────────┘               │
 │ + annotate: frames │    └───────────────────────┘                                   ▼
 └─────────┬──────────┘                                       mockups/out/<name>.png  (paper)
           │                                                  <name>-copilot.png      (copilot)
           │                                                  --all: -dark, -copilot-light
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
| `theme.css`, `theme-copilot.css` | Both themes and every layout (see [Themes](#themes)). |
| `watch.sh` + `live-engine.js` | Re-render on save; inject `live-badges.js` into the live copy only. |
| `live-badges.js` | Everything interactive on top of Marp: badges, theme/mode switcher, mockup swap, comment mode, shortcuts. |
| `comment-server.py` | Local-only endpoint that turns clicks into a `comments.md` checklist. |
| `mockups/` | Text specs → PNGs of terminal screens (`render.py`) or web apps (`web.py`), in both theme styles, with optional annotation frames. |
| `shot.sh` | Fast screenshots of the rendered deck, for visual checks without opening a browser. |

## Quick start

```bash
npm install                                  # Marp CLI + Playwright (pinned)
npx playwright install chromium-headless-shell   # once, for screenshots and mockups
./watch.sh                                   # start the watcher (also: ./watch.sh status | stop)
open deck.live.html                          # or open the file in any browser
```

Edit `deck.md`, save, reload the browser tab. `deck.md` shows every layout in the theme.

Keys in `deck.live.html`:

| Key | Action |
|---|---|
| ← → Space | previous / next slide |
| O | slide overview |
| P | presenter view (notes + timer) |
| T | switch theme: paper / copilot (or open with `?theme=copilot`) |
| D | dark / light mode (or open with `?mode=dark`) |
| C | comment mode |
| Shift+M | hide / show the "Updated" badges |
| ? | all shortcuts |

The round button in the top-right corner goes fullscreen, like **F**. Open `deck.live.html?present` to hide every helper when presenting.

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

- `./shot.sh 1 4 6`: screenshots of slides 1, 4, 6 into `shots/` (reads `deck.live.html`, no re-render). `THEME=paper|copilot` and `MODE=light|dark` pick the look, `OUT=dir` changes the folder. The README images live in `docs/screenshots/`.
- `./speaker-notes.sh`: collects `<!-- Speaker notes: ... -->` comments into `speaker-notes.md`.
- `npm run build` / `npm run pdf`: static HTML or PDF export.

## Themes

Two Marp themes share every layout:

- **`deck-kit`** (default), *paper*: warm off-white canvas, serif headlines, terracotta accent. Light by default; dark mode is the class `dark`.
- **`deck-kit-copilot`**, *copilot*: the terminal look, with Primer color tokens, mono labels and a dot grid on title slides. Dark by default; light mode is the class `light`.

Screenshots of both themes in both modes are at the top of this README.

- **Pick one for the deck** with `theme: deck-kit` or `theme: deck-kit-copilot` in the front matter of `deck.md`. The static exports (`npm run build` / `pdf`) use it.
- **Switch live** in `deck.live.html` with **T** (theme) and **D** (mode). Each theme remembers its own mode.
- **How it's built**: `theme.css` holds all layouts plus both looks. The copilot rules are the base; the paper rules come last, scoped to `section[data-theme="deck-kit"]`. `theme-copilot.css` only imports `deck-kit`, so its slides skip the paper rules. Most of the difference is tokens: colors, `--fontStack-heading` and `--fontStack-label`.

Layout classes, set per slide with `<!-- _class: ... -->`: `lead`, `lead hero`, `lead split`, `agenda`, `cards` (`cols-2..5`, `hero-first`, `lists`, `foot`), `mockup`, `quote`, `dense`, `backup`, `backup-table`, `journey`, `metrics`, `opps`, `note`.

![Layouts slide: every layout is one class](docs/screenshots/layouts.png)

Fonts use system stacks. To use your own font, put the files in `assets/fonts/`, add an `@font-face` rule at the top of `theme.css`, and put the family name first in `--fontStack-sansSerif` (or `--fontStack-heading` for headlines only).

## Mockup generator

1. Write a spec in `mockups/specs/<name>.md`: a front matter block (`app`, `cwd`, `branch`, `cols`, ...) and one line per element (`user:`, `assistant:`, `tool:`, `diff+:`, `success:`, ...).
2. Add an `annotate:` block with `frame: target | Title | Subtitle` lines to get numbered frames and labels.
3. Run `mockups/render.sh` (all specs) or `mockups/render.sh mockups/specs/review.md`. Each spec renders twice: `out/<name>.png` in the paper style (a plain terminal: one-line banner, shell prompt) and `out/<name>-copilot.png` in the copilot style (a CLI-assistant screen with header card, status line and prompt bar). Add `--all` to also get each theme's other mode (`-dark`, `-copilot-light`).
4. Embed the plain name, `![](mockups/out/review.png)`. In the live preview the image follows **T** and **D**. For a static copilot export, point the image at `review-copilot.png` yourself.
5. `mockups/specs/examples/roles.md` shows every role; see `mockups/README.md` for the full format.

`mockups/specs/review.md` is the terminal example and `mockups/specs/deploy.md` the web one; both are shown at the top of this README.

**Web-app mockups.** Put `kind: web` in the front matter and describe the page with blocks instead of terminal lines: `title`, `button` / `button*` (primary), `stats`, `table` + `row` (`{ok}Fixed` becomes a status pill), `chart`, `card`, `text`, `toast`. The front matter sets the browser and app chrome: `url`, `tab`, `nav`, `user`. Two more blocks take indented lines: `code:` (a file panel with line numbers) and `slides:` (a grid of slide thumbnails, `Title | Updated`). `annotate:` works the same way; targets are block names, with `#n` for the n-th one (`row#2`, `stats#4`).

The example deck's mockups all show one made-up product, Acme Deploy: its web dashboard (`specs/overview.md` on the title slide, `specs/deploy.md` annotated) and its `acme` CLI (`specs/review.md`, `specs/start.md`).

On a slide, with the `mockup` class:

![Mockup slide](docs/screenshots/mockup.png)

## Credits

- [Marp](https://github.com/marp-team/marp-cli) (MIT).
- Copilot theme colors from [GitHub Primer](https://github.com/primer/primitives) design tokens (MIT).
- Icons in `assets/icons/` from [Octicons](https://github.com/primer/octicons) (MIT, see `assets/icons/LICENSE-octicons.txt`).
- [Playwright](https://playwright.dev) (Apache-2.0) for screenshots.
