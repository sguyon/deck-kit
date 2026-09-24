#!/usr/bin/env bash
# Live preview for deck.md.
#   ./watch.sh          start watcher in background (detached), renders deck.live.html
#   ./watch.sh stop     stop it
#   ./watch.sh status   show whether it runs
# Open: deck.live.html in the browser (add ?present to hide the Updated markers).
# Log: watch.log   PID: .watch.pid
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
PIDFILE="$DIR/.watch.pid"
MARP="$DIR/node_modules/.bin/marp"

running() { [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

case "${1:-start}" in
  stop)
    if running; then kill "$(cat "$PIDFILE")" && echo "Stopped watcher (PID $(cat "$PIDFILE"))."; else echo "Watcher not running."; fi
    rm -f "$PIDFILE" ;;
  status)
    if running; then echo "Running, PID $(cat "$PIDFILE"). Log: $DIR/watch.log"; else echo "Not running."; fi ;;
  start)
    if running; then echo "Already running (PID $(cat "$PIDFILE"))."; exit 0; fi
    [[ -x "$MARP" ]] || { echo "Installing local marp-cli..."; npm i --no-audit --no-fund >/dev/null; }
    # --no-config: ignore any marp config file; --engine injects live-badges.js;
    # --theme-set loads both themes; --html allows the raw-HTML layouts (metrics, opps tags).
    nohup "$MARP" --no-config --engine ./live-engine.js --theme-set ./theme.css ./theme-copilot.css --html \
      --watch deck.md -o deck.live.html \
      > "$DIR/watch.log" 2>&1 < /dev/null &
    echo $! > "$PIDFILE"
    disown || true
    sleep 1
    if running; then
      echo "Watcher started (PID $(cat "$PIDFILE"))."
      echo "Open: file://$DIR/deck.live.html"
      echo "Stop: $DIR/watch.sh stop"
    else
      echo "Watcher failed to start; see $DIR/watch.log"; exit 1
    fi ;;
  *) echo "usage: $0 [start|stop|status]"; exit 2 ;;
esac
