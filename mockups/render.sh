#!/usr/bin/env bash
# Render mockups from text specs: terminal screens (tools/render.py) and, for specs with `kind: web`,
# browser-window app screens (tools/web.py).  Usage:
#   mockups/render.sh [--all] [--svg] [spec.md ...]    (no spec = all specs/*.md)
# Each spec renders in two looks, one per deck theme: out/<name>.png (paper: plain terminal)
# and out/<name>-terminal.png (CLI-assistant TUI). --all adds the other mode of each:
# <name>-dark.png and <name>-terminal-light.png.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
THEMES=(paper dark); SVG=""; SPECS=()
for a in "$@"; do
  case "$a" in
    --all) THEMES=(paper paper-dark dark light);;
    --svg) SVG="--svg";;
    *) SPECS+=("$a");;
  esac
done
[ ${#SPECS[@]} -eq 0 ] && SPECS=("$DIR"/specs/*.md)

source "$DIR/find-playwright.sh"

OUT="$DIR/out"; TMP="$DIR/.build"; mkdir -p "$OUT" "$TMP"
PAIRS=()
for s in "${SPECS[@]}"; do
  # kind: web -> browser-window app mockup (tools/web.py): plain + annotated, no zoom or svg
  if grep -q '^kind: *web' "$s"; then
    for t in "${THEMES[@]}"; do
      html=$(timeout 10 python3 "$DIR/tools/web.py" "$s" "$TMP" --theme "$t")
      PAIRS+=("$html" "$OUT/$(basename "$html" .html).png")
      if grep -q '^annotate:' "$s"; then
        h=$(timeout 10 python3 "$DIR/tools/web.py" "$s" "$TMP" --theme "$t" --annotated)
        PAIRS+=("$h" "$OUT/$(basename "$h" .html).png")
      fi
    done
    continue
  fi
  for t in "${THEMES[@]}"; do
    html=$(timeout 10 python3 "$DIR/tools/render.py" "$s" "$TMP" --theme "$t" $SVG)
    base=$(basename "$html" .html)
    PAIRS+=("$html" "$OUT/$base.png")
    [ -n "$SVG" ] && mv "$TMP/$base.svg" "$OUT/$base.svg"
    # specs with an annotate: block also get <name>-annotated.png and <name>-zoom.png
    if grep -q '^annotate:' "$s" && ! grep -q '^render: annotated' "$s"; then
      for m in annotated zoom; do
        h=$(timeout 10 python3 "$DIR/tools/render.py" "$s" "$TMP" --theme "$t" --$m)
        PAIRS+=("$h" "$OUT/$(basename "$h" .html).png")
      done
    fi
  done
done
echo "rendering $(( ${#PAIRS[@]} / 2 )) image(s)"
timeout $(( 15 + 8 * ${#PAIRS[@]} / 2 )) node "$DIR/tools/shot.js" "${PAIRS[@]}"
