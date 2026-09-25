---
marp: true
theme: deck-kit
paginate: true
size: 16:9
header: ''
footer: 'deck-kit · example deck'
transition: fade 0.12s
---

<!-- _class: lead hero -->
<!-- _header: 'deck-kit · Feature tour' -->
<!-- _paginate: false -->

# Live slides agents can edit

This deck explains the kit it is built with. The app screens show Acme Deploy, a made-up product.

![](mockups/out/overview.png)

[//]: # "Template note (not shown in the deck): This slide uses the `lead hero` classes: kicker (the _header), big title, subtitle, and a mockup on a panel that bleeds off the bottom. Every mockup in this deck shows Acme Deploy, a made-up product used as the example: its web dashboard (this one, from mockups/specs/overview.md) and its acme CLI."

<!-- Speaker notes: This is how I build product decks with an agent: plain text in, reviewed slides out.

- Everything here was written by an agent from short prompts.
- The app on screen is made up: Acme Deploy. -->

---

<!-- _class: agenda -->
<!-- _header: 'Agenda' -->

## How it works

1. **Write**
   - Edit `deck.md`
   - The watcher re-renders on save
2. **Review**
   - "Updated" badges
   - Comments with **C**
3. **Illustrate**
   - Mockups from a text spec
   - Numbered annotations

[//]: # "Template note (not shown in the deck): The agenda class lays out an ordered list as three columns. Keep each group to two or three short bullets."

<!-- Speaker notes: Three steps, and I stay in control of each one.

- I write or prompt, the agent drafts.
- I review by pointing at the slide.
- The agent draws the product screens too. -->

---

<!-- _class: mockup -->
<!-- _header: 'Mockups' -->

## Screens are text files, not screenshots

`mockups/specs/deploy.md` → `mockups/render.sh` → this PNG, frames and labels included.

![](mockups/out/deploy-annotated.png)

[//]: # "Template note (not shown in the deck): The `mockup` class puts one image on a gradient panel. The numbered frames come from the `annotate:` block in the spec. Change a line, re-run render.sh, and the image updates. This one is Acme Deploy's dry-run page; the spec starts with `kind: web`."

<!-- Speaker notes: The product screens are text files, not screenshots.

- I describe the screen in a few lines; the image comes out with numbered callouts.
- When the story changes, I change a line, not a Figma file. -->

---

<!-- _header: 'Mockups' -->

## Zoom into the detail

<div class="zoom" data-zoom="78% 64%" style="position:absolute;left:72px;top:170px;width:1136px;height:490px;overflow:hidden;border-radius:12px;background:var(--panel, var(--card))"><img src="mockups/out/deploy.png" style="position:absolute;width:2400px;max-width:none;height:auto;left:-1264px;top:-430px"></div>

[//]: # "Template note (not shown in the deck): A close-up of the previous slide's mockup. The <div class='zoom' data-zoom='78% 64%'> wrapper makes the live preview zoom from the previous slide's panel into this point (see README, Transitions)."

<!-- Speaker notes: Zooming in keeps the audience oriented.

- Same screen, closer: they see exactly where the detail lives. -->

---

<!-- _class: cards cols-3 hero-first -->
<!-- _header: 'On top of Marp' -->

## What the kit adds

- ![](assets/icons/zap-24.svg) **Live preview** *On save* The watcher re-renders the deck; changed slides get an "Updated" badge.
- ![](assets/icons/terminal-24.svg) **Mockups** *From a spec* A few lines of text become a screenshot of a web app or a terminal.
- ![](assets/icons/people-24.svg) **Comments** *Press C* Click any element; the note lands in comments.md.

[//]: # "Template note (not shown in the deck): Cards: one list item per card. An icon image first becomes a tinted tile; **bold** is the title, *italic* is the small status line. `hero-first` gives card 1 an accent border."

<!-- Speaker notes: What the kit adds on top of plain Markdown slides.

- Live preview: every save shows up, changed slides are flagged.
- Mockups from a spec.
- Comments: I click and type; the agent applies them. -->

---

<!-- _class: backup-table -->
<!-- _header: 'Layouts' -->

## Every layout is one class

| Class | Use it for | Written as |
|---|---|---|
| **lead hero** | Title slide | Title, subtitle, mockup image |
| **agenda** | Sections | Numbered list with sub-bullets |
| **cards** | Features, themes | One list item per card |
| **backup-table** | Comparisons | A plain Markdown table |
| **mockup** | Product screens | One image on a gradient panel |

> **Set it per slide:** `<!-- _class: cards cols-3 -->` above the slide content.

[//]: # "Template note (not shown in the deck): Plain Markdown tables pick up the theme: muted mono header, bold first column, row rules only. The README lists every class, including quote, journey, metrics and opps."

<!-- Speaker notes: Every layout is one line in the file, so the agent can restyle a slide without touching the content. -->

---

<!-- _class: mockup -->
<!-- _header: 'Mockups' -->

## Terminal screens too, same format

`mockups/specs/review.md`, without `kind: web` → the `acme` CLI, same annotations.

![](mockups/out/review-annotated.png)

[//]: # "Template note (not shown in the deck): Same made-up product, its CLI side. Specs without `kind: web` go to tools/render.py and come out as terminal screens: paper style is a plain shell, copilot style is a CLI-assistant screen."

<!-- Speaker notes: Same idea for terminal screens.

- Useful when the product is a CLI or an agent. -->

---

<!-- _class: lead note -->

# Try it

Edit `deck.md`, save, reload. Press **P** for presenter view, **?** for all shortcuts.

[//]: # "Template note (not shown in the deck): Speaker notes are HTML comments that start with 'Speaker notes:'. Run ./speaker-notes.sh to collect them into speaker-notes.md for rehearsal."

<!-- Speaker notes: Try it: edit the file, save, and the deck updates.

- P opens this presenter view, with these notes and a timer. -->
