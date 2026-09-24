# Terminal mockups

Turns small text specs into PNG screenshots of a fictional command-line app: a macOS-style window, a header card, a timeline of messages and tool calls, a status line, a prompt and a footer. Optional annotation frames with numbered labels.

## Render

```bash
mockups/render.sh                         # all specs/*.md -> out/<name>.png (paper) + out/<name>-copilot.png
mockups/render.sh mockups/specs/start.md  # one spec
mockups/render.sh --all                   # also out/<name>-dark.png and out/<name>-copilot-light.png
mockups/render.sh --svg                   # plus out/<name>.svg
```

`render.sh` finds Playwright in `../node_modules` (run `npm install` in the repo root) and a headless Chromium (`npx playwright install chromium-headless-shell`). Override with `PW_MODULE` / `PW_EXEC`. Intermediate HTML goes to `.build/`.

The font is SF Mono when available (macOS), otherwise Menlo / DejaVu Sans Mono / Consolas. PNGs have a transparent background and a soft shadow.

## Two looks

The same spec renders in the style of each deck theme; the palette decides the look:

| `--theme` | Look | Output |
|---|---|---|
| `paper` (default) | plain terminal: one-line banner (`app version · tagline`), content, a shell prompt (`cwd (branch) $ prompt`) | `<name>.png` |
| `paper-dark` | same, dark palette | `<name>-dark.png` |
| `dark` | CLI-assistant screen: header card, status line, prompt bar, footer | `<name>-copilot.png` |
| `light` | same, light palette | `<name>-copilot-light.png` |

Keys only the copilot look draws (`welcome:` right pane, `status_right`, `model`, `mode`, footer) are ignored by the paper look; annotation targets such as `welcome` or `prompt` still resolve. Palettes are the `THEMES` dict in `tools/render.py`.

## Spec format

```
---
cols: 110             # terminal width in characters
rows: 0               # minimum height (0 = fit content)
fit: rows             # keep cols fixed, pad with rows to reach the aspect ratio
aspect: 2.4           # canvas ratio (none = off)
app: acme             # header card + window title
version: 2.3.0
tagline: A command-line helper || second line
cwd: ~/src/acme-app   # status line, left
branch: main
status_right: 3 tasks today
model: default model  # footer, right
mode: plan            # plan | auto: colors the prompt bar, shown in the footer
prompt: text typed in the prompt
tabs: Chat            # active tab; omit for no tab row
tab_list: Chat, History, Settings
title: custom window title ({size} = cols×rows)
theme: paper          # palette when render.py runs without --theme (render.sh always passes one)
---
welcome:               # header card; indented lines replace the right pane
  heading: Getting started
  sel: selected option
  opt: other option
tip: /cmd | description
user: question >> 10:42          # ">> x" = right-aligned text
assistant: reply | continuation line || another └ line
tool: $ | Shell | npm test >> 6s  # icon | verb | detail
thought: italic reasoning block
diff: path   diff-: old line   diff+: new line
success: / warning: / error: / info: / item: / skill:
box: Title   (indented lines = body)
menu*: /cmd | desc   menu: ...   (slash menu, * = selected)
row*: icon | title | sub >> right   (list rows)
tr: a ¦ b ¦ c   (table row; widths from colw: 5,5,34,...)
line: raw full-width line
session: *name | sub
text: / muted: free text
blank: 2
sidebar:  (indented sel: / item: name | sub)
```

Inline styles: `{b}` bold, `{i}` italic, `{s}` strikethrough, `{dim}`, `{muted}`, `{accent}`, `{ok}`, `{warn}`, `{err}`, `{code}`, any `{#hex}`, `{bg=token}`; `{/}` resets. Token names are the keys of `THEMES` in `tools/render.py`.

## Annotations

```
annotate:
  frame: thought | Explains before editing | One sentence on the cause
  frame: diff#1 .. diff+#1 | Shows the exact change | A two-line diff
  crop: thought, diff+      # zoom region
  cols: 104                 # terminal width for annotated/zoom output
  dim: 0.4                  # darken everything outside the frames (0 = none; default 0.4 dark, 0.14 light)
  label_w: 380  aspect: 2.4  zoom_font: 22
  tag: NEW                  # small label above each title (empty = none)
  style: question           # purple dashed frames with a "?" badge
```

A spec with `annotate:` also produces `<name>-annotated.png` (frames + labels on the right) and `<name>-zoom.png` (close-up of the `crop:` targets). `render: annotated` in the front matter produces only the annotated image, under the plain name.

Frame targets: a role name (`thought`, `user`), the n-th of a role (`tool#2`), named anchors (`welcome`, `welcome.right`, `welcome.left`, `prompt`, `status.left`, `status.right`, `tab.Chat`, `sidebar.list`), `welcome.right[1-3]` (lines of the right pane), `rows 3-8 cols 40-100`, `a + b` (union), `a .. b` (every row from a to b). Append ` @0.8` to align the label along the frame, ` ^` to bring the leader line in from above. An unknown name prints the full list.

## Examples

- `specs/start.md`: start screen and a short exchange.
- `specs/review.md`: a proposed edit with three annotation frames.
- `specs/examples/roles.md`: every role and inline style (not rendered by default).
- `specs/overview.md`, `specs/deploy.md`: two pages of Acme Deploy's web dashboard (`kind: web`), the made-up app used in the example deck; `deploy.md` has annotation frames.

## Web-app mockups (`kind: web`)

A spec with `kind: web` in its front matter goes to `tools/web.py` instead: a browser window (tab, address bar) around an app (sidebar, page header, content). Same themes, output names and `annotate:` block; no zoom or SVG output.

```
---
kind: web
app: Acme Deploy                          # sidebar logo
url: deploy.acme.dev/acme-app             # address bar
tab: Overview · acme-app                  # browser tab title
nav: Overview*, Deploys (3), Settings     # * = active, (n) = count badge
user: Alex Kim                            # sidebar footer (optional)
width: 1400                               # window width in px
---
title: acme-app | main · last deploy 12 min ago
button: Docs
button*: New deploy                       # * = primary; buttons sit in the page header
stats: Deploys today | 14 | note ¦ Failed | 1   # label | value | optional note, ¦ between stats
table: Deploy ¦ Branch ¦ Status
row: #482 ¦ fix-totals ¦ {ok}Live         # {ok} {warn} {err} {info} {muted} = status pill
chart: Deploy time (min) | Mon 20, Tue 14, Wed 9
card: Title | body text
text: a paragraph
toast: #482 is live on production
code: plan.diff                           # file panel; indented lines are the text, kept verbatim
  + image: acme/api:2.3.1
slides: Slides                            # thumbnail grid; indented lines: Title | badge
  Overview | Updated
annotate:
  frame: button#2 | Ship it | Nothing runs before you confirm
```

Tables, charts, cards, code and slides panels sit side by side in one row, in spec order. Annotation targets are block names with an optional `#n` (1-based): `title`, `button`, `stats`, `table`, `row`, `chart`, `card`, `code`, `slides`, `slide`, `text`, `toast`, `nav`, `url`. Examples: `specs/overview.md`, `specs/deploy.md`.
