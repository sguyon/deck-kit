# Sourced by render.sh and ../shot.sh. Sets PW_MODULE (playwright package dir) and,
# if a cached headless Chromium is found, PW_EXEC. Both can be set by the caller instead.
_KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -z "${PW_MODULE:-}" ]; then
  for c in "$_KIT/node_modules/playwright" $(ls -dt "$HOME"/.npm/_npx/*/node_modules/playwright 2>/dev/null); do
    [ -f "$c/package.json" ] && { PW_MODULE="$c"; break; }
  done
fi
[ -z "${PW_MODULE:-}" ] && { echo "playwright not found: run 'npm install' in the repo root" >&2; exit 1; }
# Prefer Playwright's own browser; fall back to any cached headless shell (macOS or Linux)
# only when Playwright's matching build is missing.
_need_fallback() {  # true when Playwright's own headless-shell build is not downloaded
  local rev
  rev=$(node -e 'const b=require(require("path").join(process.argv[1],"../playwright-core/browsers.json"));const x=b.browsers.find(b=>b.name==="chromium-headless-shell");console.log(x?x.revision:"")' "$PW_MODULE" 2>/dev/null || true)
  [ -z "$rev" ] && return 0
  local d
  for d in "${PLAYWRIGHT_BROWSERS_PATH:-}" "$HOME/Library/Caches/ms-playwright" "$HOME/.cache/ms-playwright"; do
    [ -n "$d" ] && [ -d "$d/chromium_headless_shell-$rev" ] && return 1
  done
  return 0
}
if [ -z "${PW_EXEC:-}" ] && _need_fallback; then
  PW_EXEC="$(ls -dt "$HOME"/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell \
                    "$HOME"/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-*/chrome-headless-shell 2>/dev/null | head -1 || true)"
  [ -z "$PW_EXEC" ] && { echo "no Chromium found: run 'npx playwright install chromium-headless-shell' once" >&2; exit 1; }
fi
export PW_MODULE PW_EXEC
# macOS has no `timeout` unless coreutils is installed: fall back to running without one.
command -v timeout >/dev/null 2>&1 || timeout() { shift; "$@"; }
