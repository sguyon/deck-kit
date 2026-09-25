#!/usr/bin/env python3
"""Terminal mockup renderer: spec (.md) -> cell grid -> HTML (+ SVG).

  render.py SPEC.md OUTDIR [--theme paper|paper-dark|dark|light] [--svg] [--annotated|--zoom]

Two looks, paired with the deck themes:
  paper / paper-dark: a plain terminal (one-line banner, shell prompt), warm palette -> <name>.html / <name>-dark.html
  dark / light:       the CLI-assistant TUI (header card, status line, prompt band, footer), Primer palette
                      -> <name>-terminal.html / <name>-terminal-light.html
Writes OUTDIR/<name><suffix>.html (and .svg). PNG is produced by shot.js (see render.sh).
Colors are GitHub Primer color tokens (MIT), see the README credits.
"""
import html, os, re, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- themes
# dark / light: GitHub Primer primitives, "tui" look. paper / paper-dark: warm palette matching the deck's
# paper theme, "shell" look. Edit freely: every style in a spec refers to one of these token names, or a #hex.
# _look, _light, annot (annotation frame color) and suffix (output file name) are per-theme settings.
THEMES = {
    "dark": dict(
        bg="#0d1117", fg="#f0f6fc",
        muted="#9198a1", tiptext="#cbd1d7",
        border="#3d444d", accent="#58a6ff", heading="#4493f8",
        tab_on_bg="#0969da", tab_on_fg="#ffffff", tab_bg="#141b22", tab_fg="#b1bac4",
        band="#141b22", bar="#818b98", plan="#2f81f7", auto="#a475f9",
        ok="#3fb950", sel="#373b40", pill_bg="#051d4d", pill_fg="#58a6ff",
        footer_key="#9198a1", footer_label="#9198a1",
        warn="#d29922", err="#f85149", code="#b1bac4",
        diff_add="#3fb950", diff_add_bg="#12261e", diff_del="#f85149", diff_del_bg="#2d1215",
        chrome="#161b22", chrome_fg="#9198a1", chrome_border="#30363d",
        _look="tui", _light=False, annot="#3fb950", suffix="-terminal",
    ),
    "light": dict(
        bg="#ffffff", fg="#1f2328",
        muted="#59636e", tiptext="#1f2328",
        border="#6e7781", accent="#0969da", heading="#0969da",
        tab_on_bg="#0969da", tab_on_fg="#ffffff", tab_bg="#e8e9eb", tab_fg="#59636e",
        band="#e8e9eb", bar="#59636e", plan="#0969da", auto="#8250df",
        ok="#1a7f37", sel="#dde1e6", pill_bg="#ddf4ff", pill_fg="#0969da",
        footer_key="#59636e", footer_label="#6e7781",
        warn="#9a6700", err="#d1242f", code="#59636e",
        diff_add="#1a7f37", diff_add_bg="#dafbe1", diff_del="#d1242f", diff_del_bg="#ffebe9",
        chrome="#f6f8fa", chrome_fg="#59636e", chrome_border="#d1d9e0",
        _look="tui", _light=True, annot="#3fb950", suffix="-terminal-light",
    ),
    "paper": dict(
        bg="#fffdf8", fg="#1f1c18",
        muted="#7a7266", tiptext="#1f1c18",
        border="#d9d0c1", accent="#c2461c", heading="#c2461c",
        tab_on_bg="#c2461c", tab_on_fg="#ffffff", tab_bg="#f1ebe0", tab_fg="#6d665c",
        band="#f1ebe0", bar="#b3a995", plan="#c2461c", auto="#8a5a9e",
        ok="#2f7d4f", sel="#f1e4d6", pill_bg="#f7e1d4", pill_fg="#b5461f",
        footer_key="#6d665c", footer_label="#7a7266",
        warn="#9a6700", err="#b42318", code="#6d665c",
        diff_add="#2f7d4f", diff_add_bg="#e3f1e6", diff_del="#b42318", diff_del_bg="#fbe6e3",
        chrome="#efe9de", chrome_fg="#6d665c", chrome_border="#ddd4c4",
        _look="shell", _light=True, annot="#c2461c", suffix="",
    ),
    "paper-dark": dict(
        bg="#1f1c18", fg="#f4efe6",
        muted="#a79f93", tiptext="#e8e1d5",
        border="#4a443c", accent="#f08a5d", heading="#f08a5d",
        tab_on_bg="#f08a5d", tab_on_fg="#1f1c18", tab_bg="#2a2621", tab_fg="#a79f93",
        band="#2a2621", bar="#7d7468", plan="#f08a5d", auto="#c49bd6",
        ok="#7fc79a", sel="#3a332b", pill_bg="#4a2d1f", pill_fg="#f08a5d",
        footer_key="#a79f93", footer_label="#a79f93",
        warn="#e3b341", err="#f47067", code="#c9c1b4",
        diff_add="#7fc79a", diff_add_bg="#1f3326", diff_del="#f47067", diff_del_bg="#3d201c",
        chrome="#2a2621", chrome_fg="#a79f93", chrome_border="#3a352f",
        _look="shell", _light=False, annot="#f08a5d", suffix="-dark",
    ),
}
# ANSI-16 names, usable in specs as {red}, {brblue}, ... (Terminal.app-like values)
ANSI = dict(black="#000000", red="#c91b00", green="#00c200", yellow="#c7c400", blue="#0225c7",
            magenta="#ca30c7", cyan="#00c5c7", white="#c7c7c7", brblack="#686868", brred="#ff6e67",
            brgreen="#5ffa68", bryellow="#fffc67", brblue="#6871ff", brmagenta="#ff77ff",
            brcyan="#60fdff", brwhite="#ffffff")


def S(**k):
    base = dict(fg=None, bg=None, bold=False, italic=False, dim=False)
    base.update(k)
    return base


# ---------------------------------------------------------------- grid
class Grid:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.cells = [[(" ", S()) for _ in range(cols)] for _ in range(rows)]
        self.bands = []    # (row_top_float, row_bottom_float, bar_token)
        self.cursor = None
        self.anchors = {}  # name -> (r0, c0, r1, c1), used by annotate:/crop:

    def ensure(self, rows):
        while len(self.cells) < rows:
            self.cells.append([(" ", S()) for _ in range(self.cols)])
        self.rows = len(self.cells)

    def put(self, y, x, text, style=None):
        style = style or S()
        for ch in text:
            if 0 <= x < self.cols and 0 <= y < self.rows:
                self.cells[y][x] = (ch, dict(style))
            x += 1
        return x

    def put_runs(self, y, x, runs):
        for ch, st in runs:
            if 0 <= x < self.cols and 0 <= y < self.rows:
                self.cells[y][x] = (ch, dict(st))
            x += 1
        return x

    def fill_bg(self, y, x0, x1, token):
        for x in range(x0, x1):
            ch, st = self.cells[y][x]
            st = dict(st); st["bg"] = token
            self.cells[y][x] = (ch, st)


# ---------------------------------------------------------------- inline markup
STYLE_WORDS = {"s": dict(strike=True), "b": dict(bold=True), "i": dict(italic=True), "dim": dict(dim=True), "n": dict(bold=False, italic=False, dim=False, strike=False)}


def parse_inline(text, base=None):
    """'{b}Done{/} — {muted}text' -> list of (char, style). {/} resets to base."""
    base = base or S(fg="fg")
    out, st = [], dict(base)
    for tok in re.split(r"(\{[#\w/=]+\})", text):
        m = re.fullmatch(r"\{([#\w/=]+)\}", tok or "")
        if m:
            name = m.group(1)
            if name == "/":
                st = dict(base)
            elif name in STYLE_WORDS:
                st.update(STYLE_WORDS[name])
            elif name.startswith("bg="):
                st["bg"] = name[3:]
            elif name == "code":
                st["fg"] = "code"
            else:
                st["fg"] = name  # theme token or #hex
            continue
        out.extend((c, dict(st)) for c in tok)
    return out


def wrap_runs(runs, width, indent=0):
    """Word-wrap a run list; returns list of run lists (continuation lines get `indent` spaces)."""
    lines, cur, w = [], [], width
    words, word = [], []
    for c in runs:
        word.append(c)
        if c[0] == " ":
            words.append(word); word = []
    if word: words.append(word)
    for wd in words:
        if len(cur) + len(wd) - (1 if wd[-1][0] == " " else 0) > w and cur:
            lines.append(cur); cur = [(" ", S())] * indent; w = width
        cur = cur + wd
    if cur: lines.append(cur)
    return [l[:width] for l in lines] or [[]]


def split_right(text):
    if " >> " in text:
        a, b = text.split(" >> ", 1)
        return a, b
    return text, None


# ---------------------------------------------------------------- spec parsing
def parse_spec(path):
    src = open(path, encoding="utf-8").read()
    meta, body = {}, src
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", src, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.strip().startswith("#"):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    items = []
    for raw in body.splitlines():
        if raw.startswith("  ") and items and items[-1][0] == "code":   # web.py code panel: keep lines verbatim
            items[-1][2].append(raw[2:])
            continue
        if raw.strip().startswith("<!--") or raw.strip().startswith("#!"):
            continue
        if raw.startswith("  ") and items and items[-1][0] in ("welcome", "box", "annotate", "sidebar", "slides"):  # slides: web.py
            items[-1][2].append(raw.strip())
            continue
        line = raw.rstrip()
        if not line.strip():
            continue
        if ":" in line:
            role, rest = line.split(":", 1)
            role = role.strip()
            rest = rest[1:] if rest.startswith(" ") else rest
        else:
            role, rest = line.strip(), ""
        items.append((role, rest, []))
    return meta, items


# ---------------------------------------------------------------- components
def box(g, y, x0, x1, height):
    bs = S(fg="border", dim=True)
    g.put(y, x0, "╭" + "─" * (x1 - x0 - 1) + "╮", bs)
    for r in range(1, height - 1):
        g.put(y + r, x0, "│", bs); g.put(y + r, x1, "│", bs)
    g.put(y + height - 1, x0, "╰" + "─" * (x1 - x0 - 1) + "╯", bs)


def welcome(g, y, meta, lines):
    """Header card: app name / version / tagline on the left, a free-form right pane.
    Meta keys: app, version, tagline (use ' || ' for a second line). Right pane defaults to 'Getting started'."""
    cols = g.cols
    if meta.get("_look") == "shell":   # plain terminal: one banner line instead of the header card
        app, ver = meta.get("app", "acme"), meta.get("version", "")
        x = g.put(y, 1, app, S(fg="heading", bold=True))
        if ver: x = g.put(y, x + 1, ver, S(fg="muted"))
        tag = " ".join(meta.get("tagline", "").split(" || "))
        if tag: g.put_runs(y, x, parse_inline(" · " + tag, S(fg="muted")))
        for k in ("welcome", "welcome.left", "welcome.right"):
            g.anchors[k] = (y, 0, y + 1, cols)
        return y + 1
    x0, x1 = 0, cols - 5
    divider = 39
    right = []
    heading = "Getting started"
    if lines:
        heading = None
        for l in lines:
            k, _, v = l.partition(":")
            v = v[1:] if v.startswith(" ") else v
            if k.strip() == "heading":
                heading = v
            elif k.strip() in ("sel", "opt"):
                right.append(("{fg}❯ " if k.strip() == "sel" else "  ") + v + ("\x00SEL" if k.strip() == "sel" else ""))
            else:
                right.append(v)
    else:
        right = ["Type a request, or pick a command below",
                 "{fg}/init — {muted}Set up a config file for this project",
                 "{fg}/help — {muted}List every command"]
    rw = x1 - (divider + 3) - 1
    rlines = []
    if heading is not None:
        rlines.append(parse_inline(heading, S(fg="heading", bold=True)))
    sel_rows = []
    for r in right:
        if r.endswith("\x00SEL"):
            r = r[:-4]; sel_rows.append(len(rlines))
        runs = parse_inline(r, S(fg="muted"))
        rlines.extend(wrap_runs(runs, rw, indent=0))
    inner = max(4, len(rlines))
    height = inner + 4
    g.ensure(y + height + 1)
    box(g, y, x0, x1, height)
    top = y + 2
    for r in range(inner):
        g.put(top + r, divider, "│", S(fg="border", dim=True))
    app = meta.get("app", "acme")
    g.put(top, 3, "▍", S(fg="accent")); g.put(top, 5, app, S(fg="heading", bold=True))
    ver = meta.get("version", "1.0.0")
    if ver:
        g.put(top + 1, 5, f"v{ver}", S(fg="muted"))
    for i, t in enumerate(meta.get("tagline", "A command-line assistant").split(" || ")[:2]):
        g.put_runs(top + 2 + i, 5, parse_inline(t, S(fg="muted"))[: divider - 6])
    for i, runs in enumerate(rlines):
        g.put_runs(top + i, divider + 3, runs)
    for i in sel_rows:   # selected row: same bg as the real Sessions-tab selection
        g.fill_bg(top + i, divider + 2, x1 - 1, "sel")
    opts = [i for i, l in enumerate(rlines) if l and "".join(c for c, _ in l[:2]) in ("❯ ", "  ") and any(c != " " for c, _ in l)]
    if sel_rows:
        g.anchors["welcome.options"] = (top + min(opts + sel_rows), divider + 2, top + max(opts + sel_rows) + 1, x1)
    g.anchors["welcome"] = (y, x0, y + height, x1 + 1)
    g.anchors["welcome.right"] = (top, divider + 2, top + len(rlines), x1)
    g.anchors["welcome.left"] = (top, 1, top + 4, divider)
    return y + height


def tabs(g, y, active, names, disabled=()):
    x = 1
    for name in names:
        on = name == active
        st = S(fg="tab_on_fg", bg="tab_on_bg", bold=True) if on else S(fg="tab_fg", bg="tab_bg", dim=name in disabled)
        g.anchors[f"tab.{name}"] = (y, x, y + 1, x + len(name) + 2)
        x = g.put(y, x, f" {name} ", st) + 1


def bullet_item(g, y, bullet_style, text, cont=None, base=None, right=None):
    """● text / └ continuation — the CLI's timeline item shape."""
    width = g.cols - 3 - 2
    g.put(y, 1, "●", bullet_style)
    lines = wrap_runs(parse_inline(text, base or S(fg="fg")), width, indent=0)
    for i, l in enumerate(lines):
        g.ensure(y + i + 1)
        g.put_runs(y + i, 3, l)
    if right:
        g.put(y, g.cols - 1 - len(right), right, S(fg="muted"))
    y += len(lines)
    if cont:
        cl = [l for part in cont.split(" || ") for l in wrap_runs(parse_inline(part, S(fg="muted")), g.cols - 5 - 2, indent=0)]
        for i, l in enumerate(cl):
            g.ensure(y + 1)
            if i == 0:
                g.put(y, 3, "└", S(fg="muted"))
            g.put_runs(y, 5, l)
            y += 1
    return y


def render_items(g, meta, items):
    y = 0
    # tabs: <active tab name>   tab_list: Chat, History, Settings   (no tabs: key = no tab row)
    if meta.get("tabs", "none") != "none":
        names = [t.strip() for t in meta.get("tab_list", "Chat, History, Settings").split(",")]
        tabs(g, 0, meta["tabs"], names)
        y = 2
    counts = {}
    for role, rest, block in items:
        g.ensure(y + 2)
        y0 = y
        if role in ("annotate", "sidebar"):
            continue
        if role == "blank":
            y += int(rest) if rest.strip() else 1
        elif role == "welcome":
            y = welcome(g, y, meta, block) + 1
        elif role == "tip":
            cmd, _, desc = rest.partition(" | ")
            y = bullet_item(g, y, S(fg="accent"), f"Tip: {cmd}", desc, base=S(fg="tiptext")) + 1
        elif role in ("item", "assistant", "info", "success", "warning", "error", "skill"):
            color = {"item": "accent", "assistant": "accent", "info": "accent", "success": "ok",
                     "skill": "ok", "warning": "warn", "error": "err"}[role]
            text, right = split_right(rest)
            main, _, cont = text.partition(" | ")
            y = bullet_item(g, y, S(fg=color), main, cont or None, right=right) + 1
        elif role == "user":
            text, right = split_right(rest)
            g.put(y, 1, "❯", S(fg="fg"))
            for i, l in enumerate(wrap_runs(parse_inline(text), g.cols - 6, 0)):
                g.ensure(y + i + 1); g.put_runs(y + i, 3, l)
            if right: g.put(y, g.cols - 1 - len(right), right, S(fg="muted"))
            y += 2
        elif role == "tool":
            text, right = split_right(rest)
            parts = [p.strip() for p in text.split(" | ")]
            icon, verb, detail = (parts + ["", "", ""])[:3]
            ist = {"MD": S(fg="muted", bold=True), "$": S(fg="warn"), "/": S(fg="fg")}.get(icon, S(fg="fg"))
            x = g.put(y, 1, icon, ist) + 1
            x = g.put(y, x, verb + " ", S(fg="fg", bold=True))
            g.put_runs(y, x, parse_inline(detail)[: g.cols - x - 6])
            if right: g.put(y, g.cols - 1 - len(right), right, S(fg="muted"))
            y += 1
        elif role == "detail":
            g.put_runs(y, 3, parse_inline(rest)[: g.cols - 5]); y += 1
        elif role == "thought":
            g.put(y, 1, "⌄ ", S(fg="fg")); g.put(y, 3, "Thought", S(fg="fg", italic=True)); y += 1
            for l in wrap_runs(parse_inline(rest, S(fg="fg", italic=True)), g.cols - 6, 0):
                g.ensure(y + 1); g.put(y, 1, "│", S(fg="fg", dim=True)); g.put_runs(y, 3, l); y += 1
        elif role in ("text", "dim", "muted"):
            base = S(fg="fg") if role == "text" else S(fg="muted")
            text, right = split_right(rest)
            for l in wrap_runs(parse_inline(text, base), g.cols - 4, 0):
                g.ensure(y + 1); g.put_runs(y, 1, l); y += 1
            if right: g.put(y - 1, g.cols - 1 - len(right), right, S(fg="muted"))
        elif role in ("diff+", "diff-", "diff"):
            tok = {"diff+": ("diff_add", "diff_add_bg", "+"), "diff-": ("diff_del", "diff_del_bg", "-"), "diff": ("muted", None, " ")}[role]
            g.put(y, 3, f"{tok[2]} ", S(fg=tok[0]))
            g.put_runs(y, 5, parse_inline(rest, S(fg="fg"))[: g.cols - 8])
            if tok[1]: g.fill_bg(y, 3, g.cols - 2, tok[1])
            y += 1
        elif role == "box":
            lines = [wrap_runs(parse_inline(b), g.cols - 10, 0) for b in block]
            flat = [l for ls in lines for l in ls]
            h = len(flat) + (4 if rest else 2)
            g.ensure(y + h + 1)
            box(g, y, 0, g.cols - 5, h)
            r = y + 1
            if rest:
                g.put_runs(r, 2, parse_inline(rest, S(fg="fg", bold=True)))
                g.put(r + 1, 2, "─" * (g.cols - 9), S(fg="border", dim=True)); r += 2
            for l in flat:
                g.put_runs(r, 2, l); r += 1
            y += h + 1
        elif role in ("menu", "menu*"):
            cmd, _, desc = rest.partition(" | ")
            sel = role == "menu*"
            g.put(y, 0, "┃", S(fg="heading" if sel else "muted"))
            g.put(y, 2, ("❯ " if sel else "  ") + cmd, S(fg="fg"))
            g.put_runs(y, 38, parse_inline(desc, S(fg="fg" if sel else "muted"))[: g.cols - 40])
            if sel: g.fill_bg(y, 0, g.cols, "band")
            y += 1
        elif role in ("tr", "tr*"):
            widths = [int(w) for w in meta.get("colw", "5,5,34,10,12,12,16").split(",")]
            cells = re.split(r" ¦ ?", rest)
            x = 0
            for w, cell in zip(widths + [999], cells):
                runs = parse_inline(cell, S(fg="muted"))[: max(w - 1, 1)] if w < 999 else parse_inline(cell, S(fg="muted"))
                g.put_runs(y, x, runs); x += w
            if role == "tr*": g.fill_bg(y, 0, g.cols, "band")
            y += 1
        elif role in ("line", "line*"):
            text, right = split_right(rest)
            g.put_runs(y, 0, parse_inline(text, S(fg="fg"))[: g.cols])
            if right:
                rr = parse_inline(right, S(fg="muted")); g.put_runs(y, g.cols - 1 - len(rr), rr)
            if role == "line*": g.fill_bg(y, 0, g.cols, "band")
            y += 1
        elif role in ("row", "row*"):
            text, right = split_right(rest)
            icon, _, tail = text.partition(" | ")
            title_, _, sub = tail.partition(" | ")
            sel = role == "row*"
            g.ensure(y + 3)
            if sel:
                g.bands.append((y - 0.5, y + 2.5, "border", "sel"))
            g.put_runs(y, 3, parse_inline(icon, S(fg="ok")))
            g.put_runs(y, 6, parse_inline(title_, S(fg="heading" if sel else "fg", bold=True)))
            g.put_runs(y + 1, 6, parse_inline(sub, S(fg="muted")))
            if right:
                rr = parse_inline(right, S(fg="muted"))
                g.put_runs(y, g.cols - 2 - len(rr), rr)
                g.anchors[f"{role}.right#{counts.get(role, 0) + 1}"] = (y, g.cols - 2 - len(rr), y + 1, g.cols - 2)
            y += 3
        elif role == "session":
            name, _, sub = rest.partition(" | ")
            dot = "●" if name.startswith("*") else "○"
            name = name.lstrip("*")
            g.put(y, 3, dot, S(fg="ok" if dot == "●" else "muted"))
            g.put(y, 6, name, S(fg="fg", bold=True))
            g.put_runs(y + 1, 6, parse_inline(sub, S(fg="muted")))
            y += 3
        else:
            raise SystemExit(f"unknown role '{role}' in spec")
        if role not in ("blank", "welcome"):
            counts[role] = counts.get(role, 0) + 1
            rect = (y0, 0, y, g.cols)
            g.anchors.setdefault(role, rect)
            g.anchors[f"{role}#{counts[role]}"] = rect
    return y


def chrome_rows(g, y_content_end, meta):
    """status line + prompt band + footer, pinned to the bottom like the real TUI."""
    want = int(meta.get("rows", 28))
    if meta.get("_look") == "shell":   # plain terminal: a single shell prompt line at the bottom
        rows = max(want, y_content_end + 2)
        g.ensure(rows)
        p = rows - 1
        cwd, br = meta.get("cwd", "~/repo"), meta.get("branch")
        x = g.put(p, 1, cwd, S(fg="accent", bold=True))
        if br: x = g.put(p, x, f" ({br})", S(fg="muted"))
        x = g.put(p, x, " $ ", S(fg="fg"))
        g.anchors["status.left"] = g.anchors["status.right"] = (p, 1, p + 1, x)
        prompt = meta.get("prompt", "")
        if prompt: g.put_runs(p, x, parse_inline(prompt, S(fg="fg")))
        g.anchors["prompt"] = (p, 0, p + 1, g.cols)
        g.cursor = (p, x + len(re.sub(r"\{[#\w/=]+\}", "", prompt)))
        return
    rows = max(want, y_content_end + 6)
    g.ensure(rows)
    s, b, f = rows - 5, rows - 4, rows - 1
    if meta.get("chrome") == "footer":
        g.put_runs(f, 1, parse_inline(meta.get("footer", ""), S(fg="footer_label")))
        return
    cwd = meta.get("cwd", "~/repo")
    br = meta.get("branch")
    left = cwd + (f" [⎇ {br}]" if br else "")
    g.put(s, 1, left, S(fg="muted"))
    right = meta.get("status_right", "")
    g.put(s, g.cols - 1 - len(right), right, S(fg="muted"))
    g.anchors["status.left"] = (s, 1, s + 1, 1 + len(left))
    g.anchors["status.right"] = (s, g.cols - 1 - len(right), s + 1, g.cols - 1)
    g.anchors["prompt"] = (b + 1, 0, b + 2, g.cols)
    mode = meta.get("mode", "")
    bar = {"plan": "plan", "auto": "auto"}.get(mode, "bar")
    g.bands.append((b + 0.5, b + 2.5, bar))
    prompt = meta.get("prompt", "")
    if prompt:
        g.put_runs(b + 1, 2, parse_inline(prompt, S(fg="fg")))
    g.cursor = (b + 1, 2 + len(re.sub(r"\{[#\w/=]+\}", "", prompt)))
    # footer
    x = 1
    parts = [("←", " sidebar")] if any(it[0] == "sidebar" for it in meta.get("_items", [])) else []
    if mode: parts.append((None, mode))
    parts += [("/", " commands"), ("?", " help")]
    if meta.get("tabs", "none") != "none": parts.append(("tab", " next tab"))
    if meta.get("footer"):
        parts = []
        g.put_runs(f, 1, parse_inline(meta["footer"], S(fg="footer_label")))
    for i, (k, lab) in enumerate(parts):
        if i: x = g.put(f, x, " · ", S(fg="footer_key"))
        if k is None:
            x = g.put(f, x, lab, S(fg=bar))
        else:
            x = g.put(f, x, k, S(fg="footer_key", bold=True))
            x = g.put(f, x, lab, S(fg="footer_label"))
    model = meta.get("model", "")
    g.put(f, g.cols - 1 - len(model), model, S(fg="footer_key"))


# ---------------------------------------------------------------- output
def color(tok, theme, default):
    if tok is None:
        return default
    if tok.startswith("#"):
        return tok
    if tok in ANSI:
        return ANSI[tok]
    return theme.get(tok, default)


def runs_of(row):
    out, cur, buf = [], None, ""
    for ch, st in row:
        key = (st["fg"], st["bg"], st["bold"], st["italic"], st["dim"], st.get("strike", False))
        if key != cur and buf:
            out.append((cur, buf)); buf = ""
        cur = key; buf += ch
    if buf: out.append((cur, buf))
    return out


CW, LH = 0.6185, 1.24  # monospace advance (em) measured from SF Mono renders; line height (em)


def tight(g, rect):
    """Shrink a (r0,c0,r1,c1) rect to its non-blank cells."""
    r0, c0, r1, c1 = rect
    rs, cs = [], []
    for y in range(r0, min(r1, g.rows)):
        for x in range(c0, min(c1, g.cols)):
            if g.cells[y][x][0] != " " or g.cells[y][x][1].get("bg"):
                rs.append(y); cs.append(x)
    if not rs:
        return rect
    return (min(rs), min(cs), max(rs) + 1, max(cs) + 1)


def resolve(g, target):
    target = target.split(" @")[0].rstrip(" ^")
    if " .. " in target:
        a_, b_ = [resolve(g, t) for t in target.split(" .. ")]
        return tight(g, (min(a_[0], b_[0]), 0, max(a_[2], b_[2]), g.cols))
    if " + " in target:
        rs = [resolve(g, t) for t in target.split(" + ")]
        return (min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs))
    t = target.strip()
    m = re.fullmatch(r"rows\s+(\d+)-(\d+)(?:\s+cols\s+(\d+)-(\d+))?", t)
    if m:
        r0, r1 = int(m.group(1)), int(m.group(2)) + 1
        c0, c1 = (int(m.group(3)), int(m.group(4)) + 1) if m.group(3) else (0, g.cols)
        return tight(g, (r0, c0, r1, c1))
    m = re.fullmatch(r"([\w.#*+-]+)\[(\d+)-(\d+)\]", t)
    if m:
        r0, c0, r1, c1 = g.anchors[m.group(1)]
        return tight(g, (r0 + int(m.group(2)), c0, r0 + int(m.group(3)) + 1, c1))
    if t not in g.anchors:
        raise SystemExit(f"annotate: unknown target '{t}'. Known: {', '.join(sorted(g.anchors))}")
    return tight(g, g.anchors[t])


def cellsafe(text):
    """Non-ASCII glyphs may come from a fallback font with a different advance width;
    pin each one to exactly 1ch so columns never drift."""
    out = []
    for ch in text:
        if ord(ch) > 127:
            out.append(f'<i class="g">{html.escape(ch)}</i>')
        else:
            out.append(html.escape(ch))
    return "".join(out)



# ---------------------------------------------------------------- annotations (shared with web.py)
# Frames are .frame elements (with a .badge) inside .stage; labels are .label[data-i] in .labels; the script
# stacks the labels next to .win, draws leader lines in svg.ov and dims everything outside the frames.
def annot_css(acc, glow, question, light, bg, lab_bg, lab_fg, lab_sub):
    return f""".frame{{position:absolute;border:2.5px solid {acc};border-radius:9px;box-sizing:border-box;
  box-shadow:0 0 0 1px {glow}.25),0 0 14px 2px {glow}.45),inset 0 0 10px {glow}.12)}}
.badge{{position:absolute;left:-16px;top:-15px;width:26px;height:26px;border-radius:50%;background:{acc};
  color:{"#ffffff" if light else "#0d1117"};font:800 15px/26px -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;text-align:center;
  box-shadow:0 0 0 2px {bg}}}
.labels{{position:relative;align-self:stretch;flex:none;z-index:2}}
.label{{position:absolute;left:0;right:0;display:flex;gap:14px;align-items:flex-start;background:{lab_bg};
  border:2px solid {acc};border-radius:12px;padding:14px 18px 16px 14px;
  box-shadow:0 10px 26px rgba(0,0,0,.35);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",sans-serif}}
.badge.big{{position:static;flex:none;width:34px;height:34px;font-size:19px;line-height:34px;box-shadow:none;margin-top:2px}}
.tag{{font:800 13px/1 -apple-system,sans-serif;letter-spacing:.12em;color:{acc};margin:2px 0 6px}}
.lt{{font-size:24px;font-weight:700;line-height:1.2;color:{lab_fg}}}
.ls{{font-size:19px;line-height:1.3;color:{lab_sub};margin-top:6px}}
{".frame{border-style:dashed;border-width:2px;box-shadow:none}.lt{font-size:36px;font-weight:600;font-style:normal;line-height:1.25}" if question else ""}
.ov{{position:absolute;left:0;top:0;pointer-events:none;z-index:1}}
"""


def annot_js(acc, dim, question):
    return """<script>
window.__ready = false;
document.fonts.ready.then(() => requestAnimationFrame(() => {
  if (window.__beforeAnnot) window.__beforeAnnot();   // web.py places its .frame elements here
  const stage = document.querySelector('.stage'), S = stage.getBoundingClientRect();
  const col = document.querySelector('.labels').getBoundingClientRect();
  const win = document.querySelector('.win').getBoundingClientRect();
  const its = [...document.querySelectorAll('.frame')].map(f => {
    const r = f.getBoundingClientRect(), l = document.querySelector('.label[data-i="' + f.dataset.i + '"]');
    const a = parseFloat(f.dataset.a);
    return {r, l, h: l.offsetHeight, y: r.top + a * r.height - S.top, a};
  }).sort((a, b) => a.y - b.y);
  let prev = -1e9;
  for (const it of its) { it.top = Math.max(it.y - it.h / 2, prev + __GAP__, win.top - S.top); prev = it.top + it.h; }
  const maxB = win.bottom - S.top, minT = win.top - S.top;
  if (prev > maxB) {           // pack from the bottom up, never above the window top
    let lim = maxB;
    for (const it of [...its].reverse()) { it.top = Math.min(it.top, lim - it.h); lim = it.top - __GAP__; }
    if (its[0].top < minT) { const tot = its.reduce((a, it) => a + it.h, 0), gap = (maxB - minT - tot) / Math.max(1, its.length - 1);
      let t = minT; its.forEach(it => { it.top = t; t += it.h + gap; }); }
  }
  its.forEach(it => { it.l.style.top = (it.top - (col.top - S.top)) + 'px'; });
  const NS = 'http://www.w3.org/2000/svg', svg = document.querySelector('.ov');
  svg.setAttribute('width', S.width); svg.setAttribute('height', S.height);
  const el = (n, a) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); svg.appendChild(e); return e; };
  const DIM = __DIM__;
  if (DIM > 0) {
    const rr = (x, y, w, h, r) => `M${x + r},${y}h${w - 2 * r}a${r},${r} 0 0 1 ${r},${r}v${h - 2 * r}a${r},${r} 0 0 1 -${r},${r}h-${w - 2 * r}a${r},${r} 0 0 1 -${r},-${r}v-${h - 2 * r}a${r},${r} 0 0 1 ${r},-${r}z`;
    let d = rr(win.left - S.left, win.top - S.top, win.width, win.height, 11);
    its.forEach(it => { d += rr(it.r.left - S.left - 2, it.r.top - S.top - 2, it.r.width + 4, it.r.height + 4, 9); });
    el('path', {d, fill: '#000', 'fill-opacity': DIM, 'fill-rule': 'evenodd'});
  }
  its.forEach((it, k) => {
    const lb = it.l.getBoundingClientRect();
    const lx = lb.left - S.left, ly = lb.top - S.top + 30;
    const fx = it.r.right - S.left, fy = Math.min(Math.max(ly, it.r.top - S.top + Math.min(14, it.r.height / 2)), it.r.bottom - S.top - Math.min(14, it.r.height / 2));
    const mx = Math.max(fx + 16, Math.min(lx - 12, win.right - S.left + 12 + k * 7));
    let d = `M${lx},${ly} H${mx} V${fy} H${fx}`, ex = fx, ey = fy;
    if (it.l && document.querySelector('.frame[data-i="' + it.l.dataset.i + '"]').dataset.route === 'top') {
      const cx = (it.r.left + it.r.right) / 2 - S.left, ty = it.r.top - S.top - 9;
      d = `M${lx},${ly} H${mx} V${ty} H${cx} V${it.r.top - S.top}`; ex = cx; ey = it.r.top - S.top;
    }
    el('path', {d, fill: 'none', stroke: '__ACC__', 'stroke-width': __SW__, 'stroke-linejoin': 'round'});
    el('circle', {cx: ex, cy: ey, r: 4.5, fill: '__ACC__'});
  });
  window.__ready = true;
}));
</script>""".replace("__DIM__", str(dim)).replace("__ACC__", acc).replace("__GAP__", "14" if question else "22").replace("__SW__", "4" if question else "2.5")

def to_html(g, meta, theme_name, font_px=15, line=LH, extra=None):
    """extra: {'mode': 'annotated'|'zoom', 'frames': [(rect, title, sub)], 'dim': 0.4,
               'crop': rect, 'label_w': px}"""
    extra = extra or {}
    mode = extra.get("mode", "")
    T = THEMES[theme_name]
    light = T["_light"]
    rows_html = []
    for y, row in enumerate(g.cells):
        spans = []
        for (fg, bg, bold, italic, dim, strike), text in runs_of(row):
            css = [f"color:{color(fg, T, T['fg'])}"]
            if bg: css.append(f"background:{color(bg, T, T['bg'])}")
            if bold: css.append("font-weight:700")
            if italic: css.append("font-style:italic")
            if dim: css.append("opacity:.6")
            if strike: css.append("text-decoration:line-through;text-decoration-thickness:1.5px")
            spans.append(f'<span style="{";".join(css)}">{cellsafe(text)}</span>')
        rows_html.append(f'<div class="r">{"".join(spans)}</div>')
    bands = ""
    for top, bot, bar, *rest in g.bands:
        bgtok = rest[0] if rest else "band"
        x0, x1 = (rest[1], rest[2]) if len(rest) > 2 else (1, g.cols)
        bands += (f'<div class="band" style="top:calc({top} * var(--lh));height:calc({bot - top} * var(--lh));'
                  f'left:calc({x0} * 1ch);width:calc({x1 - x0} * 1ch);right:auto;'
                  f'background:{color(bgtok, T, T["band"])}"></div>')
        if bar:
            bands += (f'<div class="bar" style="top:calc({top} * var(--lh));height:calc({bot - top} * var(--lh));'
                      f'left:calc({x0 - 1} * 1ch + .38ch);background:{color(bar, T, T["bar"])}"></div>')
    cur = ""
    if g.cursor and meta.get("cursor", "true") != "false":
        cy, cx = g.cursor
        cur = f'<div class="cur" style="top:calc({cy} * var(--lh));left:calc({cx} * 1ch);background:{T["fg"]}"></div>'
    frames_html, labels_html = "", ""
    question = extra.get("style") == "question"
    tag = extra.get("tag", "NEW")
    acc = T["annot"]  # question style uses the palette accent too (purple vanished on purple/lavender slide panels)
    for i, (rect, title_, sub) in enumerate(extra.get("frames", []), 1):
        r0, c0, r1, c1, frac, route = rect if len(rect) == 6 else (*rect[:4], rect[4] if len(rect) > 4 else 0.5, "")
        px = 6 if c1 - c0 < 20 else 14
        frames_html += (f'<div class="frame" data-i="{i}" data-a="{frac}" data-route="{route}" style="top:calc({r0} * var(--lh) - 4px);'
                        f'left:max(calc({c0} * 1ch - {px}px), -9px);width:calc({c1} * 1ch + {px - 2}px - max(calc({c0} * 1ch - {px}px), -9px));'
                        f'height:calc({r1 - r0} * var(--lh) + 8px)">' + ("" if question else f'<b class="badge">{i}</b>') + '</div>')
        badge = '<b class="badge big">?</b>' if question else f'<b class="badge big">{i}</b>'
        labels_html += (f'<div class="label" data-i="{i}">{badge}<div>'
                        + (f'<div class="tag">{html.escape(tag)}</div>' if tag else "")
                        + f'<div class="lt">{html.escape(title_)}</div>'
                        + (f'<div class="ls">{html.escape(sub)}</div>' if sub else "") + "</div></div>")
    grid_inner = f'{bands}{cur}<div style="position:relative">{"".join(rows_html)}</div>{frames_html}'
    crop = extra.get("crop")
    if crop:
        r0, c0, r1, c1 = crop
        grid = (f'<div class="vp" style="width:{c1 - c0}ch;height:calc({r1 - r0} * var(--lh))">'
                f'<div class="grid" style="transform:translate(calc({-c0} * 1ch), calc({-r0} * var(--lh)))">{grid_inner}</div></div>')
    else:
        grid = f'<div class="grid">{grid_inner}</div>'
    title = meta.get("title", f"{meta.get('app', 'acme')} — {g.cols}×{g.rows}").replace("{size}", f"{g.cols}×{g.rows}")
    sf = "/System/Applications/Utilities/Terminal.app/Contents/Resources/Fonts"
    pad = int(meta.get("pad", 28))
    label_w = int(extra.get("label_w", 380))
    glow = "rgba({},{},{},".format(*(int(acc[i:i + 2], 16) for i in (1, 3, 5)))
    lab_bg, lab_fg, lab_sub = ((T["bg"], T["fg"], T["muted"]) if T["_look"] == "shell" else
                               ("#ffffff", "#1f2328", "#59636e") if light else ("#161b22", "#f0f6fc", "#9198a1"))
    dim = float(extra.get("dim", 0))
    labels_col = f'<div class="labels" style="width:{label_w}px">{labels_html}</div><svg class="ov"></svg>' if mode == "annotated" else ""
    script = ""
    if mode == "annotated":
        script = annot_js(acc, dim, question)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:"TermFont";src:url("file://{sf}/SF-Mono-Regular.otf");font-weight:400}}
@font-face{{font-family:"TermFont";src:url("file://{sf}/SF-Mono-Bold.otf");font-weight:700}}
@font-face{{font-family:"TermFont";src:url("file://{sf}/SF-Mono-RegularItalic.otf");font-weight:400;font-style:italic}}
@font-face{{font-family:"TermFont";src:url("file://{sf}/SF-Mono-BoldItalic.otf");font-weight:700;font-style:italic}}
html,body{{margin:0;background:transparent}}
.stage{{display:inline-flex;align-items:flex-start;gap:56px;padding:{pad}px;position:relative}}
.win{{border-radius:11px;overflow:hidden;background:{T['bg']};flex:none;
  box-shadow:0 0 0 1px {T['chrome_border']},0 14px 30px rgba(0,0,0,.40),0 3px 8px rgba(0,0,0,.22)}}
.tb{{height:30px;background:{T['chrome']};position:relative;border-bottom:1px solid {T['chrome_border']};
  font:600 13px -apple-system,BlinkMacSystemFont,"SF Pro Text","Helvetica Neue",sans-serif;color:{T['chrome_fg']};
  display:flex;align-items:center;justify-content:center}}
.tl{{position:absolute;left:12px;top:9px;display:flex;gap:8px}}
.tl i{{width:12px;height:12px;border-radius:50%;display:block}}
.term{{--lh:{line}em;position:relative;font-family:"TermFont","SF Mono",Menlo,"DejaVu Sans Mono",Consolas,monospace;font-size:{font_px}px;
  line-height:var(--lh);color:{T['fg']};padding:10px 14px 12px;white-space:pre;
  font-variant-ligatures:none;-webkit-font-smoothing:antialiased}}
.vp{{overflow:hidden;position:relative}}
.grid{{position:relative;width:{g.cols}ch}}
.r{{height:var(--lh)}}
.g{{display:inline-block;width:1ch;text-align:center;font-style:inherit;overflow:visible}}
.band,.bar{{position:absolute;left:1ch;right:0}}
.bar{{left:.38ch;width:.24ch;right:auto}}
.cur{{position:absolute;width:1ch;height:var(--lh)}}
{annot_css(acc, glow, question, light, T["bg"], lab_bg, lab_fg, lab_sub)}
</style></head><body><div class="stage"><div class="win">
<div class="tb"><div class="tl"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>{html.escape(title)}</div>
<div class="term">{grid}</div>
</div>{labels_col}</div>{script}</body></html>"""


def to_svg(g, meta, theme_name, font_px=15, line=1.24):
    T = THEMES[theme_name]
    cw, lh = font_px * 0.6, font_px * line   # SF Mono advance = 0.6em
    padx, pady, tb = 14, 10, 30
    W = int(g.cols * cw + 2 * padx); H = int(g.rows * lh + pady + 12 + tb)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><clipPath id="w"><rect width="{W}" height="{H}" rx="11"/></clipPath></defs><g clip-path="url(#w)">',
         f'<rect width="{W}" height="{H}" fill="{T["bg"]}"/>',
         f'<rect width="{W}" height="{tb}" fill="{T["chrome"]}"/>']
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        o.append(f'<circle cx="{18 + i * 20}" cy="15" r="6" fill="{c}"/>')
    title = meta.get("title", f"{meta.get('app', 'acme')} — {g.cols}×{g.rows}").replace("{size}", f"{g.cols}×{g.rows}")
    o.append(f'<text x="{W / 2}" y="19.5" text-anchor="middle" font-family="-apple-system,Helvetica,sans-serif" '
             f'font-size="13" font-weight="600" fill="{T["chrome_fg"]}">{html.escape(title)}</text>')
    oy = tb + pady
    for top, bot, bar, *rest in g.bands:
        x0, x1 = (rest[1], rest[2]) if len(rest) > 2 else (1, g.cols)
        o.append(f'<rect x="{padx + x0 * cw}" y="{oy + top * lh}" width="{(x1 - x0) * cw}" height="{(bot - top) * lh}" fill="{color(rest[0] if rest else "band", T, T["band"])}"/>')
        if bar:
            o.append(f'<rect x="{padx + (x0 - 1 + .38) * cw}" y="{oy + top * lh}" width="{cw * .24}" height="{(bot - top) * lh}" fill="{color(bar, T, T["bar"])}"/>')
    if g.cursor:
        cy, cx = g.cursor
        o.append(f'<rect x="{padx + cx * cw}" y="{oy + cy * lh}" width="{cw}" height="{lh}" fill="{T["fg"]}"/>')
    sf = "/System/Applications/Utilities/Terminal.app/Contents/Resources/Fonts"
    o.append(f'<style>@font-face{{font-family:TermFont;src:url("file://{sf}/SF-Mono-Regular.otf")}}'
             f'@font-face{{font-family:TermFont;font-weight:700;src:url("file://{sf}/SF-Mono-Bold.otf")}}</style>')
    o.append(f'<g font-family="TermFont,SF Mono,Menlo,monospace" font-size="{font_px}" xml:space="preserve">')
    for y, row in enumerate(g.cells):
        x = 0
        for (fg, bg, bold, italic, dim, strike), text in runs_of(row):
            n = len(text)
            if bg:
                o.append(f'<rect x="{padx + x * cw}" y="{oy + y * lh}" width="{n * cw}" height="{lh}" fill="{color(bg, T, T["bg"])}"/>')
            lead = len(text) - len(text.lstrip(" "))
            core = text.strip(" ")
            if core:
                n2, x2 = len(core), x + lead
                attrs = f'fill="{color(fg, T, T["fg"])}"'
                if bold: attrs += ' font-weight="700"'
                if italic: attrs += ' font-style="italic"'
                if dim: attrs += ' opacity=".6"'
                o.append(f'<text x="{padx + x2 * cw:.2f}" y="{oy + y * lh + lh * 0.76:.2f}" textLength="{n2 * cw:.2f}" '
                         f'lengthAdjust="spacing" {attrs}>{html.escape(core)}</text>')
            x += n
    o.append("</g></g></svg>")
    return "\n".join(o)


SB = 40   # sidebar width incl. its │ divider


def build(meta, items, cols, rows):
    sb = [it for it in items if it[0] == "sidebar"]
    if sb:
        main = build(meta, [it for it in items if it[0] != "sidebar"], cols - SB, rows)
        g = Grid(cols, main.rows)
        for y in range(main.rows):
            for x in range(main.cols):
                g.cells[y][x + SB] = main.cells[y][x]
        for top, bot, bar, *rest in main.bands:
            bgtok = rest[0] if rest else "band"
            x0, x1 = (rest[1], rest[2]) if len(rest) > 2 else (1, main.cols)
            g.bands.append((top, bot, bar, bgtok, x0 + SB, x1 + SB))
        g.anchors = {k: (a, b + SB, c, d + SB) for k, (a, b, c, d) in main.anchors.items()}
        if main.cursor: g.cursor = (main.cursor[0], main.cursor[1] + SB)
        sidebar(g, sb[0][2])
        return g
    m = dict(meta); m["rows"] = str(rows); m["_items"] = items
    m.setdefault("_look", THEMES[meta.get("_theme", "paper")]["_look"])
    g = Grid(cols, 1)
    y = render_items(g, m, items)
    chrome_rows(g, y, m)
    return g


def sidebar(g, lines):
    """Left session sidebar: `sidebar:` block with `sel:` / `item:` lines (name | sub)."""
    g.put(0, 1, " ← ", S(fg="tab_fg", bg="tab_bg")); g.put(0, 5, " + ", S(fg="tab_fg", bg="tab_bg"))
    g.put(1, 1, "Sorted: ", S(fg="muted")); g.put(1, 9, "Recent", S(fg="fg", bold=True))
    for y in range(g.rows):
        g.put(y, SB - 1, "│", S(fg="border"))
    y = 3
    for l in lines:
        k, _, v = l.partition(":")
        name, _, sub = v.strip().partition(" | ")
        sel = k.strip() == "sel"
        if y + 2 >= g.rows: break
        if sel:
            g.bands.append((y - 0.5, y + 2.5, None, "tab_on_bg", 1, SB - 2))
            g.put(y, 2, "●", S(fg="ok")); g.put(y, 5, name, S(fg="tab_on_fg", bold=True))
            g.put_runs(y + 1, 5, parse_inline(sub, S(fg="tab_on_fg"))[: SB - 7])
        else:
            g.put(y, 2, "○", S(fg="muted")); g.put(y, 5, name, S(fg="fg", bold=True))
            g.put_runs(y + 1, 5, parse_inline(sub, S(fg="muted"))[: SB - 7])
        y += 3
    g.anchors["sidebar"] = (0, 0, g.rows, SB - 1)
    g.anchors["sidebar.list"] = (2, 1, y - 1, SB - 2)


def canvas(cols, rows, fp, pad, side=0):
    w = cols * CW * fp + 28 + 2 * pad + side
    h = rows * LH * fp + 53 + 2 * pad
    return w, h


def fit(meta, items, fp, pad, side=0, aspect=None):
    """Pick cols/rows so the whole canvas is close to `aspect` (default 2.4:1).
    Too tall -> widen (more cols); too wide -> add blank rows above the status line."""
    cols = int(meta.get("cols", 100))
    rows = int(meta.get("rows", 0) or 0)
    aspect = aspect or meta.get("aspect", "2.4")
    g = build(meta, items, cols, rows)
    if aspect == "none":
        return g
    a = float(aspect)
    for _ in range(6):
        w, h = canvas(g.cols, g.rows, fp, pad, side)
        if abs(w / h - a) < 0.03:
            break
        if w / h < a:
            if meta.get("fit") == "rows":
                break
            cols = int(round((a * h - 28 - 2 * pad - side) / (CW * fp)))
            g = build(meta, items, cols, 0)
        else:
            rows = int(round((w / a - 53 - 2 * pad) / (LH * fp)))
            g = build(meta, items, g.cols, rows)
    return g


def main():
    args = sys.argv[1:]
    theme = "paper"
    if "--theme" in args:
        i = args.index("--theme"); theme = args[i + 1]; del args[i:i + 2]
    want_svg = "--svg" in args
    mode = "annotated" if "--annotated" in args else "zoom" if "--zoom" in args else ""
    args = [a for a in args if a not in ("--svg", "--annotated", "--zoom")]
    extra = {}
    if True:
        spec, outdir = args[0], args[1]
        meta, items = parse_spec(spec)
        stem = os.path.splitext(os.path.basename(spec))[0]
        theme = meta.get("theme", theme) if "--theme" not in sys.argv else theme
        if theme not in THEMES: raise SystemExit(f"unknown theme {theme!r}; one of: {', '.join(THEMES)}")
        meta = dict(meta, _theme=theme)
        ann = {}
        frames = []
        for role, rest, block in items:
            if role == "annotate":
                for l in block:
                    k, _, v = l.partition(":")
                    v = v.strip()
                    if k.strip() == "frame":
                        target, _, label = v.partition(" | ")
                        t, _, sub = label.partition(" | ")
                        frames.append((target, t, sub))
                    else:
                        ann[k.strip()] = v
        if mode and not frames:
            raise SystemExit(f"{spec}: --{mode} needs an annotate: block with frame: lines")
        fp = int(meta.get("font_px", 15))
        pad = int(meta.get("pad", 28))
        plain_name = False
        if not mode and meta.get("render") == "annotated":
            mode, plain_name = "annotated", True
        if mode == "annotated":
            label_w = int(ann.get("label_w", 380))
            meta = dict(meta, cols=ann.get("cols", meta.get("cols", "100")))
            g = fit(meta, items, fp, pad, side=label_w + 56, aspect=ann.get("aspect", meta.get("aspect", "2.4")))
            extra = dict(mode=mode, label_w=label_w, dim=float(ann.get("dim", 0.14 if THEMES[theme]["_light"] else 0.4)),
                         tag=ann.get("tag", "NEW"), style=ann.get("style", ""),
                         frames=[((*resolve(g, t), float(t.split(' @')[1].rstrip(' ^')) if ' @' in t else 0.5, 'top' if t.rstrip().endswith('^') else ''), a, b) for t, a, b in frames])
        elif mode == "zoom":
            g = build(meta, items, int(ann.get("cols", meta.get("cols", 100))), 0)
            fp = int(ann.get("zoom_font", 22))
            rects = [resolve(g, t.strip()) for t in ann.get("crop", "welcome, item").split(",")]
            r0 = 0 if ann.get("zoom_tabs", "true") == "true" else max(0, min(r[0] for r in rects) - 1)
            r1 = min(g.rows, max(r[2] for r in rects) + 1)
            c0 = -2; c1 = min(g.cols, max(r[3] for r in rects) + 2)
            extra = dict(mode=mode, crop=(r0, c0, r1, c1),
                         frames=[((*resolve(g, t), float(t.split(' @')[1].rstrip(' ^')) if ' @' in t else 0.5, 'top' if t.rstrip().endswith('^') else ''), a, b) for t, a, b in frames])
            meta = dict(meta, cursor="false")
        else:
            g = fit(meta, items, fp, pad)
        name = stem + ("-" + mode if mode and not plain_name else "")
    suffix = THEMES[theme]["suffix"]
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{name}{suffix}.html")
    open(out, "w").write(to_html(g, meta, theme, fp, extra=extra))
    if want_svg and not mode:
        open(os.path.join(outdir, f"{name}{suffix}.svg"), "w").write(to_svg(g, meta, theme, fp))
    print(out)


if __name__ == "__main__":
    main()
