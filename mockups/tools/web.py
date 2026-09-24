#!/usr/bin/env python3
"""Web-app mockup renderer: spec (.md with `kind: web`) -> HTML page of a browser window with an app inside.

  web.py SPEC.md OUTDIR [--theme paper|paper-dark|dark|light] [--annotated]

Same themes, output names and annotate: block as render.py (paper -> <name>.html, dark -> <name>-copilot.html, ...);
PNGs come from shot.js via render.sh. Blocks, in page order:
  title: Page title | subtitle            button: Label  (button*: primary; buttons sit in the page header)
  stats: Label | value | note ¦ ...       table: Col ¦ Col ¦ ...   row: cell ¦ cell ¦ ...  ({ok}Done = status pill)
  chart: Title | Mon 3, Tue 5, ...        card: Title | body text  text: a paragraph     toast: message
  code: file name   (indented lines below = the file's text, shown with line numbers)
  slides: Panel title   (indented lines below = one thumbnail each: `Slide title | Updated`)
Front matter: app, url, tab, nav (Item*, Item (4), ...), user, width.
Annotation targets: a block name, or its n-th occurrence (row#2, stats#3, button#1, nav#2), e.g.
  frame: row#2 | Title | Subtitle
"""
import html, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import parse_spec, annot_css, annot_js  # noqa: E402

SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'
SERIF = '"Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif'

# Same names and output suffixes as render.py THEMES; values match the deck themes.
THEMES = {
    "paper": dict(light=True, suffix="", heading=SERIF,
                  canvas="#f7f4ee", surface="#fffdf8", side="#f1ebe0", border="#e2dacb", fg="#1f1c18", muted="#6d665c",
                  accent="#c2461c", accent_soft="#f7e1d4", primary_fg="#ffffff",
                  ok="#2f7d4f", ok_bg="#e3f1e6", warn="#9a6700", warn_bg="#fbefcf", err="#b42318", err_bg="#fbe6e3",
                  info="#b5461f", info_bg="#f7e1d4", chrome="#ebe4d8", chrome_fg="#6d665c", tab_bg="#f7f4ee", url_bg="#fffdf8",
                  toast_bg="#1f1c18", toast_fg="#f4efe6", annot="#c2461c"),
    "paper-dark": dict(light=False, suffix="-dark", heading=SERIF,
                       canvas="#1a1815", surface="#23201c", side="#1f1c18", border="#3a352f", fg="#f4efe6", muted="#a79f93",
                       accent="#f08a5d", accent_soft="#4a2d1f", primary_fg="#1f1c18",
                       ok="#7fc79a", ok_bg="#1f3326", warn="#e3b341", warn_bg="#3a2f14", err="#f47067", err_bg="#3d201c",
                       info="#f08a5d", info_bg="#4a2d1f", chrome="#2a2621", chrome_fg="#a79f93", tab_bg="#1a1815", url_bg="#23201c",
                       toast_bg="#f4efe6", toast_fg="#1f1c18", annot="#f08a5d"),
    "dark": dict(light=False, suffix="-copilot", heading=SANS,
                 canvas="#0d1117", surface="#151b23", side="#010409", border="#3d444d", fg="#f0f6fc", muted="#9198a1",
                 accent="#238636", accent_soft="#1f6feb33", primary_fg="#ffffff",
                 ok="#3fb950", ok_bg="#2ea04326", warn="#d29922", warn_bg="#bb800926", err="#f85149", err_bg="#f8514926",
                 info="#4493f8", info_bg="#388bfd26", chrome="#161b22", chrome_fg="#9198a1", tab_bg="#0d1117", url_bg="#010409",
                 toast_bg="#f0f6fc", toast_fg="#0d1117", annot="#3fb950"),
    "light": dict(light=True, suffix="-copilot-light", heading=SANS,
                  canvas="#ffffff", surface="#f6f8fa", side="#f6f8fa", border="#d1d9e0", fg="#1f2328", muted="#59636e",
                  accent="#1f883d", accent_soft="#ddf4ff", primary_fg="#ffffff",
                  ok="#1a7f37", ok_bg="#dafbe1", warn="#9a6700", warn_bg="#fff8c5", err="#d1242f", err_bg="#ffebe9",
                  info="#0969da", info_bg="#ddf4ff", chrome="#eaeef2", chrome_fg="#59636e", tab_bg="#ffffff", url_bg="#f6f8fa",
                  toast_bg="#1f2328", toast_fg="#ffffff", annot="#1a7f37"),
}


def inline(text):
    """{ok} {warn} {err} {info} {muted} {b} {code} ... {/} -> spans (status pills inside table cells)."""
    out, open_ = [], 0
    for part in re.split(r"(\{[\w/]+\})", text):
        m = re.fullmatch(r"\{([\w/]+)\}", part)
        if not m:
            out.append(html.escape(part)); continue
        if m.group(1) == "/":
            if open_: out.append("</span>"); open_ -= 1
        else:
            out.append(f'<span class="s-{m.group(1)}">'); open_ += 1
    return "".join(out) + "</span>" * open_


def code_line(l):
    """Light Markdown / YAML highlighting for the code panel."""
    e = html.escape(l) or "&nbsp;"
    if l.startswith("#"): return f'<b class="k-h">{e}</b>'
    if l.startswith("+"): return f'<span class="k-add">{e}</span>'
    if l.startswith("-") and not l.startswith("---"): return f'<span class="k-del">{e}</span>'
    if l.startswith("<!--") or l.strip() == "---": return f'<span class="k-c">{e}</span>'
    m = re.match(r"^(\s*[\w-]+:)(.*)$", l)
    if m: return f'<span class="k-k">{html.escape(m.group(1))}</span>{html.escape(m.group(2))}'
    return e


def cells(rest):
    return [c.strip() for c in rest.split("¦")]


def page(meta, items):
    count = {}
    def t(role):   # data-t / data-n let annotate: find the n-th block of a kind
        count[role] = count.get(role, 0) + 1
        return f'data-t="{role}" data-n="{count[role]}"'

    nav = ""
    for item in [n.strip() for n in meta.get("nav", "").split(",") if n.strip()]:
        active = "*" in item; item = item.replace("*", "").strip()
        m = re.match(r"(.*?)\s*\((\d+)\)$", item)
        label, badge = (m.group(1), m.group(2)) if m else (item, "")
        nav += (f'<div class="nav{" on" if active else ""}" {t("nav")}><i class="ico"></i>{html.escape(label)}'
                + (f'<b class="count">{badge}</b>' if badge else "") + "</div>")
    user = meta.get("user", "")
    user_html = (f'<div class="user"><i class="avatar">{html.escape(user[:1])}</i>{html.escape(user)}</div>' if user else "")

    title, sub, buttons, blocks, panels, toast = "", "", [], [], [], ""
    table = None
    for role, rest, block in items:
        if role == "title":
            a, _, b = rest.partition(" | "); title, sub = a, b
        elif role in ("button", "button*"):
            buttons.append(f'<span class="btn{" primary" if role == "button*" else ""}" {t("button")}>{inline(rest)}</span>')
        elif role == "stats":
            st = ""
            for c in cells(rest):
                label, value, note = (c.split(" | ") + ["", ""])[:3]
                st += (f'<div class="stat" {t("stats")}><div class="sl">{inline(label)}</div><div class="sv">{inline(value)}</div>'
                       + (f'<div class="sn">{inline(note)}</div>' if note else "") + "</div>")
            blocks.append(f'<div class="stats">{st}</div>')
        elif role == "table":
            table = {"head": cells(rest), "rows": [], "attr": t("table")}
            panels.append(table)
        elif role == "row" and table is not None:
            table["rows"].append((cells(rest), t("row")))
        elif role == "chart":
            name, _, data = rest.partition(" | ")
            pts = [(m.group(1), float(m.group(2))) for m in re.finditer(r"([^,\d]+?)\s+([\d.]+)", data)]
            top = max((v for _, v in pts), default=1) or 1
            bars = "".join(f'<div class="bar"><i style="height:{v / top * 100:.0f}%"></i><span>{html.escape(k.strip())}</span></div>' for k, v in pts)
            panels.append(f'<div class="panel chart" {t("chart")}><div class="ph">{inline(name)}</div><div class="bars">{bars}</div></div>')
        elif role == "card":
            a, _, b = rest.partition(" | ")
            panels.append(f'<div class="panel card" {t("card")}><div class="ph">{inline(a)}</div><p>{inline(b)}</p></div>')
        elif role == "text":
            blocks.append(f'<p class="text" {t("text")}>{inline(rest)}</p>')
        elif role == "code":
            lines = "".join(f'<div class="cl"><span class="ln">{n}</span>{code_line(l)}</div>' for n, l in enumerate(block, 1))
            panels.append(f'<div class="panel code" {t("code")}><div class="ph"><span class="file">{inline(rest)}</span></div><div class="src">{lines}</div></div>')
        elif role == "slides":
            thumbs = ""
            for n, l in enumerate(block, 1):
                name, _, flag = l.partition(" | ")
                thumbs += (f'<div class="thumb" {t("slide")}><span class="tn">{n}</span><i class="tk"></i><div class="tt">{inline(name)}</div>'
                           + (f'<span class="upd">{inline(flag)}</span>' if flag else "") + "</div>")
            panels.append(f'<div class="panel slides" {t("slides")}><div class="ph">{inline(rest)}</div><div class="thumbs">{thumbs}</div></div>')
        elif role == "toast":
            toast = f'<div class="toast" {t("toast")}><i class="dot"></i>{inline(rest)}</div>'

    def panel_html(p):
        if isinstance(p, str): return p
        head = "".join(f"<th>{inline(h)}</th>" for h in p["head"])
        rows = "".join(f'<tr {a}>' + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r, a in p["rows"])
        return f'<div class="panel table" {p["attr"]}><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    if panels:
        blocks.append('<div class="panels">' + "".join(panel_html(p) for p in panels) + "</div>")
    header = (f'<div class="ph1"><div><h1 {t("title")}>{inline(title)}</h1>' + (f'<div class="sub">{inline(sub)}</div>' if sub else "")
              + f'</div><div class="actions">{"".join(buttons)}</div></div>')
    app = html.escape(meta.get("app", "acme"))
    return f"""<div class="chrome"><div class="tl"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>
<div class="tab"><i class="fav"></i>{html.escape(meta.get("tab", meta.get("app", "acme")))}<span class="x">×</span></div></div>
<div class="addr"><span class="arrows">‹&nbsp;&nbsp;›&nbsp;&nbsp;↻</span><div class="url" {t("url")}><span class="lock">🔒︎</span>{html.escape(meta.get("url", "app.example.com"))}</div></div>
<div class="app"><aside class="side"><div class="logo"><i class="mark"></i>{app}</div>{nav}<div class="grow"></div>{user_html}</aside>
<main class="main"{' style="padding-bottom:84px"' if toast else ""}>{header}{"".join(blocks)}</main>{toast}</div>"""


def css(T, width):
    return f"""
html,body{{margin:0;background:transparent}}
.stage{{display:inline-flex;align-items:flex-start;gap:56px;padding:28px;position:relative}}
.win{{width:{width}px;border-radius:11px;overflow:hidden;background:{T['canvas']};flex:none;font-family:{SANS};color:{T['fg']};
  box-shadow:0 0 0 1px {T['border']},0 14px 30px rgba(0,0,0,.30),0 3px 8px rgba(0,0,0,.18);-webkit-font-smoothing:antialiased}}
.chrome{{height:40px;background:{T['chrome']};display:flex;align-items:flex-end;padding-left:84px;position:relative}}
.tl{{position:absolute;left:14px;top:14px;display:flex;gap:8px}} .tl i{{width:12px;height:12px;border-radius:50%;display:block}}
.tab{{background:{T['tab_bg']};border-radius:9px 9px 0 0;height:32px;padding:0 14px;display:flex;align-items:center;gap:8px;
  font-size:13px;color:{T['fg']};min-width:220px}}
.tab .x{{margin-left:auto;color:{T['chrome_fg']}}}
.fav,.mark{{width:14px;height:14px;border-radius:4px;background:{T['accent']};display:inline-block}}
.addr{{height:40px;background:{T['tab_bg']};display:flex;align-items:center;gap:14px;padding:0 14px;border-bottom:1px solid {T['border']}}}
.arrows{{color:{T['chrome_fg']};font-size:16px}}
.url{{flex:1;background:{T['url_bg']};border:1px solid {T['border']};border-radius:8px;height:26px;display:flex;align-items:center;gap:8px;
  padding:0 12px;font-size:13px;color:{T['muted']}}}
.lock{{font-size:11px;opacity:.7}}
.app{{display:flex;position:relative}}
.side{{width:210px;flex:none;background:{T['side']};border-right:1px solid {T['border']};padding:18px 12px;display:flex;flex-direction:column;gap:2px}}
.logo{{display:flex;align-items:center;gap:10px;font-weight:700;font-size:16px;padding:0 10px 18px}} .mark{{width:20px;height:20px;border-radius:6px}}
.nav{{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:7px;font-size:14px;color:{T['muted']}}}
.nav .ico{{width:14px;height:14px;border-radius:4px;border:1.5px solid currentColor;opacity:.7}}
.nav.on{{background:{T['accent_soft']};color:{T['fg']};font-weight:600}} .nav.on .ico{{border-color:{T['accent']};background:{T['accent']};opacity:1}}
.count{{margin-left:auto;font-size:11px;background:{T['border']};color:{T['fg']};border-radius:10px;padding:1px 7px}}
.grow{{flex:1}}
.user{{display:flex;align-items:center;gap:10px;font-size:13px;color:{T['muted']};padding:8px 10px}}
.avatar{{width:26px;height:26px;border-radius:50%;background:{T['accent']};color:{T['primary_fg']};font-style:normal;font-weight:700;
  font-size:12px;display:flex;align-items:center;justify-content:center}}
.main{{flex:1;padding:26px 32px 30px;display:flex;flex-direction:column;gap:20px;min-width:0}}
.ph1{{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}}
h1{{font-family:{T['heading']};font-size:28px;font-weight:{600 if T['heading'] == SERIF else 700};margin:0;letter-spacing:-.01em}}
.sub{{font-size:14px;color:{T['muted']};margin-top:4px}}
.actions{{display:flex;gap:10px}}
.btn{{font-size:14px;font-weight:600;padding:8px 16px;border-radius:7px;border:1px solid {T['border']};background:{T['surface']}}}
.btn.primary{{background:{T['accent']};border-color:{T['accent']};color:{T['primary_fg']}}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px}}
.stat,.panel{{background:{T['surface']};border:1px solid {T['border']};border-radius:10px}}
.stat{{padding:14px 16px}}
.sl{{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:{T['muted']}}}
.sv{{font-family:{T['heading']};font-size:30px;font-weight:600;margin-top:4px}}
.sn{{font-size:12px;color:{T['muted']};margin-top:2px}}
.panels{{display:flex;gap:14px;align-items:stretch}}
.panel{{padding:16px 18px;min-width:0}} .panel.table{{flex:2.2;padding:6px 0}} .panel.chart,.panel.card{{flex:1}}
.panel.code{{flex:1.3;padding:0;overflow:hidden}} .panel.slides{{flex:1.7}}
.panel.code .ph{{margin:0;padding:10px 16px;border-bottom:1px solid {T['border']};font-weight:600;font-size:13px}}
.file::before{{content:"";display:inline-block;width:10px;height:12px;margin-right:8px;border:1.5px solid {T['muted']};border-radius:2px;vertical-align:-1px}}
.src{{font:13px/1.65 ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace;padding:10px 0 12px;white-space:pre}}
.cl{{padding-right:16px}} .ln{{display:inline-block;width:38px;padding-right:14px;text-align:right;color:{T['muted']};opacity:.55}}
.k-h{{color:{T['fg']};font-weight:700}} .k-add{{color:{T['ok']}}} .k-del{{color:{T['err']}}} .k-c{{color:{T['muted']}}} .k-k{{color:{T['accent']}}}
.thumbs{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.thumb{{position:relative;aspect-ratio:16/9;background:{T['canvas']};border:1px solid {T['border']};border-radius:6px;padding:12px 12px 10px;box-sizing:border-box}}
.tn{{position:absolute;left:8px;bottom:6px;font-size:10px;color:{T['muted']}}}
.tk{{display:block;width:18px;height:2px;background:{T['accent']};margin-bottom:8px}}
.tt{{font-family:{T['heading']};font-size:13px;font-weight:600;line-height:1.25;color:{T['fg']}}}
.upd{{position:absolute;right:6px;top:6px;font-size:9px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:{T['primary_fg']};background:{T['accent']};padding:2px 6px;border-radius:10px}}
.ph{{font-size:14px;font-weight:700;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
th{{text-align:left;font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:{T['muted']};padding:10px 18px;border-bottom:1px solid {T['border']}}}
td{{padding:11px 18px;border-bottom:1px solid {T['border']};color:{T['muted']}}}
td:first-child{{color:{T['fg']};font-weight:600}} tr:last-child td{{border-bottom:0}}
td [class^="s-"]{{font-size:12px;font-weight:600;padding:3px 10px;border-radius:20px}}
.s-ok{{color:{T['ok']};background:{T['ok_bg']}}} .s-warn{{color:{T['warn']};background:{T['warn_bg']}}}
.s-err{{color:{T['err']};background:{T['err_bg']}}} .s-info{{color:{T['info']};background:{T['info_bg']}}}
.s-muted{{color:{T['muted']};background:{T['border']}}} .s-b{{font-weight:700;color:{T['fg']}}}
.bars{{display:flex;align-items:flex-end;gap:12px;height:150px;padding-top:6px}}
.bar{{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;height:100%;justify-content:flex-end}}
.bar i{{display:block;width:100%;border-radius:5px 5px 2px 2px;background:{T['accent']};opacity:.85}}
.bar span{{font-size:11px;color:{T['muted']}}}
.card p,.text{{font-size:14px;color:{T['muted']};margin:0;line-height:1.5}}
.toast{{position:absolute;right:24px;bottom:22px;background:{T['toast_bg']};color:{T['toast_fg']};font-size:14px;font-weight:500;
  padding:12px 16px;border-radius:9px;display:flex;align-items:center;gap:10px;box-shadow:0 10px 24px rgba(0,0,0,.25)}}
.toast .dot{{width:8px;height:8px;border-radius:50%;background:{T['ok']}}}
"""


PLACE_FRAMES = """<script>
window.__beforeAnnot = () => {
  const stage = document.querySelector('.stage'), S = stage.getBoundingClientRect();
  window.__frames.forEach((f, k) => {
    const [role, n] = f.target.split('#');
    const el = document.querySelector(`[data-t="${role}"][data-n="${n || 1}"]`);
    if (!el) { document.title = 'unknown target ' + f.target; return; }
    const r = el.getBoundingClientRect(), p = 7;
    const d = document.createElement('div');
    d.className = 'frame'; d.dataset.i = k + 1; d.dataset.a = 0.5; d.dataset.route = '';
    Object.assign(d.style, {left: (r.left - S.left - p) + 'px', top: (r.top - S.top - p) + 'px',
                            width: (r.width + 2 * p) + 'px', height: (r.height + 2 * p) + 'px', zIndex: 3});
    d.innerHTML = '<b class="badge">' + (k + 1) + '</b>';
    stage.appendChild(d);
  });
};
</script>"""


def main():
    args = sys.argv[1:]
    theme = "paper"
    if "--theme" in args:
        i = args.index("--theme"); theme = args[i + 1]; del args[i:i + 2]
    annotated = "--annotated" in args
    spec, outdir = [a for a in args if a != "--annotated"][:2]
    meta, items = parse_spec(spec)
    if theme not in THEMES: raise SystemExit(f"unknown theme {theme!r}; one of: {', '.join(THEMES)}")
    T = THEMES[theme]
    frames, ann = [], {}
    for role, rest, block in items:
        if role == "annotate":
            for l in block:
                k, _, v = l.partition(":")
                if k.strip() == "frame":
                    target, _, label = v.strip().partition(" | ")
                    title_, _, sub = label.partition(" | ")
                    frames.append((target.strip(), title_, sub))
                else:
                    ann[k.strip()] = v.strip()
    if annotated and not frames:
        raise SystemExit(f"{spec}: --annotated needs an annotate: block with frame: lines")
    body = page(meta, [it for it in items if it[0] != "annotate"])
    extra_css, labels, script = "", "", ""
    if annotated:
        acc = T["annot"]; question = ann.get("style") == "question"
        glow = "rgba({},{},{},".format(*(int(acc[i:i + 2], 16) for i in (1, 3, 5)))
        extra_css = annot_css(acc, glow, question, T["light"], T["canvas"], T["surface"], T["fg"], T["muted"])
        tag = ann.get("tag", "NEW")
        for i, (_, a, b) in enumerate(frames, 1):
            labels += (f'<div class="label" data-i="{i}"><b class="badge big">{i}</b><div>'
                       + (f'<div class="tag">{html.escape(tag)}</div>' if tag else "")
                       + f'<div class="lt">{html.escape(a)}</div>' + (f'<div class="ls">{html.escape(b)}</div>' if b else "") + "</div></div>")
        labels = f'<div class="labels" style="width:{int(ann.get("label_w", 380))}px">{labels}</div><svg class="ov"></svg>'
        import json
        dim = float(ann.get("dim", 0.14 if T["light"] else 0.4))
        script = (f"<script>window.__frames = {json.dumps([{'target': f[0]} for f in frames])};</script>"
                  + PLACE_FRAMES + annot_js(acc, dim, question))
    width = int(meta.get("width", 1400))
    doc = (f'<!doctype html><html><head><meta charset="utf-8"><style>{css(T, width)}{extra_css}</style></head>'
           f'<body><div class="stage"><div class="win">{body}</div>{labels}</div>{script}</body></html>')
    stem = os.path.splitext(os.path.basename(spec))[0] + ("-annotated" if annotated else "")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{stem}{T['suffix']}.html")
    open(out, "w").write(doc)
    print(out)


if __name__ == "__main__":
    main()
