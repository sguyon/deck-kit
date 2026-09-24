#!/usr/bin/env bash
# Fast slide screenshots from the already-rendered deck.live.html (no re-render).
#   ./shot.sh 1 5 6        -> shots/slide-1.png, shots/slide-5.png, shots/slide-6.png
#   OUT=/tmp ./shot.sh 2   -> /tmp/slide-2.png
#   THEME=copilot MODE=light ./shot.sh 3 -> copilot theme, light mode (THEME: paper|copilot, MODE: dark|light)
# Needs Playwright (npm install puts it in node_modules) and a Chromium
# (`npx playwright install chromium-headless-shell` once). PW_MODULE / PW_EXEC override both.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT:-$DIR/shots}"; mkdir -p "$OUT"
source "$DIR/mockups/find-playwright.sh"
[ -f "$DIR/deck.live.html" ] || { echo "deck.live.html not found: run ./watch.sh first" >&2; exit 1; }
DECK="$DIR/deck.live.html" OUT="$OUT" THEME="${THEME:-}" MODE="${MODE:-}" timeout 60 node -e '
const { chromium } = require(process.env.PW_MODULE);
(async () => {
  const opts = process.env.PW_EXEC ? { executablePath: process.env.PW_EXEC } : {};
  const b = await chromium.launch(opts);
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  for (const n of process.argv.slice(1)) {
    await p.goto("file://" + process.env.DECK + "?present" + (process.env.THEME ? "&theme=" + process.env.THEME : "") + (process.env.MODE ? "&mode=" + process.env.MODE : "") + "#" + n);
    await p.addStyleTag({ content: ".bespoke-marp-osc{display:none!important}" }); // Marp page-nav bar
    await p.waitForTimeout(400);
    const f = process.env.OUT + "/slide-" + n + ".png";
    await p.screenshot({ path: f });
    console.log(f);
  }
  await b.close();
})().catch(e => { console.error(e.message.split("\n")[0]); process.exit(1); });
' "$@"
