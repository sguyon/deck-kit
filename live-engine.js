// Marp engine used ONLY by watch.sh (passed via --engine). It renders exactly like
// the default Marp engine, then appends one <script> tag that loads live-badges.js.
// deck.md is untouched; the plain `marp deck.md -o deck.html` render is unaffected.
const { Marp } = require('@marp-team/marp-core')

class LiveMarp extends Marp {
  render(markdown, env) {
    const out = super.render(markdown, env)
    // Cache-bust so a reload always picks up the latest live-badges.js.
    out.html += `<script src="live-badges.js?v=${Date.now()}"></script>`
    return out
  }
}

module.exports = LiveMarp
