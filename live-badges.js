/* live-badges.js — helpers injected into the live Marp preview (deck.live.html):
 * change badges, theme + dark/light switcher, presenter-view styling, comment mode, shortcuts overlay.
 *
 * - Each slide is hashed (its rendered content). A slide whose hash you haven't
 *   "seen" gets an Updated pill + outline. Viewing it for >= 1.5s marks it seen.
 * - First load ever (no localStorage state): everything is marked seen, nothing flagged.
 * - Counter bottom-left ("3 slides updated") jumps to the next updated slide on click.
 * - Presenting mode: open with ?present (markers hidden, nothing rendered),
 *   or press Shift+M to toggle markers on/off (remembered across reloads).
 * - Themes: T cycles paper / terminal (?theme=paper|terminal); D toggles dark / light
 *   (?mode=dark|light; the old ?theme=light still works). Both persist (localStorage)
 *   and work with ?present too.
 */
(function () {
  'use strict'
  var DWELL_MS = 1500
  var KEY = 'marpLiveBadges:' + location.pathname
  var HIDE_KEY = 'marpLiveBadges:hidden'
  var params = new URLSearchParams(location.search)
  var inFrame = (function () { try { return window.self !== window.top } catch (e) { return true } })()
  var isOverview = /view=overview/.test(location.search)
  var presentParam = params.has('present') || (inFrame && !isOverview) || /view=presenter/.test(location.search)

  // --- Theme (T) and dark/light mode (D); runs in every mode, including ?present ---
  // Themes are Marp themes from theme.css / theme-terminal.css. Every <section> carries data-theme;
  // switching rewrites it, and the CSS scoped to that value takes over. Each theme has a natural mode
  // (paper = light, terminal = dark); the mode is remembered per theme.
  var THEMES = [{ id: 'deck-kit', name: 'paper', mode: 'light' }, { id: 'deck-kit-terminal', name: 'terminal', mode: 'dark' }]
  var STYLE_KEY = 'marpLiveStyle:v1', MODE_KEY = 'marpLiveMode:v1:'
  function store(k, v) { try { localStorage.setItem(k, v) } catch (e) {} }
  function stored(k) { try { return localStorage.getItem(k) } catch (e) { return null } }
  function byName(n) { if (n === 'copilot' || n === 'deck-kit-copilot') n = 'terminal'; return THEMES.filter(function (t) { return t.name === n || t.id === n })[0] }  // old name still accepted
  function applyTheme(theme, mode) {
    var dark = mode === 'dark'
    Array.prototype.forEach.call(document.querySelectorAll('section[data-theme]'), function (sec) {
      sec.setAttribute('data-theme', theme.id)
      sec.classList.toggle('light', !dark)
      sec.classList.toggle('dark', dark)
    })
    document.documentElement.style.colorScheme = mode
    swapMockups(theme, mode)
    store(STYLE_KEY, theme.name); store(MODE_KEY + theme.name, mode)
    window.__liveTheme = { theme: theme, mode: mode }
  }
  // Mockups follow the theme: mockups/out/<name>.png is paper, <name>-terminal.png the terminal look, and
  // -dark / -terminal-light the other mode (only rendered with `render.sh --all`). Missing file -> step back
  // to the theme's default image, then to the one written in deck.md.
  function swapMockups(theme, mode) {
    Array.prototype.forEach.call(document.querySelectorAll('img[src*="mockups/out/"]'), function (img) {
      var orig = img.getAttribute('data-src-orig') || img.getAttribute('src')
      img.setAttribute('data-src-orig', orig)
      var base = orig.replace(/(-terminal-light|-terminal|-dark)?\.png$/, '')
      var first = theme.name === 'terminal' ? '-terminal' : ''
      var tries = [base + first + (mode === theme.mode ? '' : (theme.name === 'terminal' ? '-light' : '-dark')) + '.png', base + first + '.png', orig]
      var i = 0
      img.onerror = function () { if (++i < tries.length) img.src = tries[i]; else img.onerror = null }
      if (img.getAttribute('src') !== tries[0]) img.src = tries[0]
    })
  }
  function modeFor(theme) { return stored(MODE_KEY + theme.name) || theme.mode }
  var themeParam = (params.get('theme') || '').toLowerCase(), modeParam = (params.get('mode') || '').toLowerCase()
  if (themeParam === 'dark' || themeParam === 'light') { modeParam = modeParam || themeParam; themeParam = '' } // old ?theme=light
  var first = document.querySelector('section[data-theme]')
  var startTheme = byName(themeParam) || byName(stored(STYLE_KEY)) || byName(first && first.getAttribute('data-theme')) || THEMES[0]
  applyTheme(startTheme, modeParam === 'dark' || modeParam === 'light' ? modeParam : modeFor(startTheme))
  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey || e.shiftKey) return
    var t = e.target
    if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return
    var cur = window.__liveTheme
    if (e.key === 'd' || e.key === 'D') applyTheme(cur.theme, cur.mode === 'dark' ? 'light' : 'dark')
    if (e.key === 't' || e.key === 'T') { var next = THEMES[(THEMES.indexOf(cur.theme) + 1) % THEMES.length]; applyTheme(next, modeFor(next)) }
  })

  function hash(str) { // FNV-1a 32-bit, hex
    var h = 0x811c9dc5
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i)
      h = Math.imul(h, 0x01000193)
    }
    return (h >>> 0).toString(16)
  }

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) } catch (e) { return null }
  }
  function save(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)) } catch (e) {}
  }

  var svgs = Array.prototype.slice.call(document.querySelectorAll('svg[data-marpit-svg]'))
  var slides = svgs.map(function (svg, i) {
    var section = svg.querySelector('section')
    return { idx: i, svg: svg, section: section, hash: hash(section ? section.innerHTML : '') }
  })

  var state = load()
  if (!state || !state.seen) {
    // First load: treat the current deck as the baseline.
    state = { seen: {} }
    slides.forEach(function (s) { state.seen[s.hash] = Date.now() })
  }
  // Prune: keep hashes of current slides + the 300 most recent others.
  var current = {}
  slides.forEach(function (s) { current[s.hash] = 1 })
  var others = Object.keys(state.seen).filter(function (h) { return !current[h] })
    .sort(function (a, b) { return state.seen[b] - state.seen[a] }).slice(0, 300)
  var pruned = {}
  others.concat(Object.keys(current)).forEach(function (h) { if (state.seen[h]) pruned[h] = state.seen[h] })
  state.seen = pruned
  save(state)

  // Expose for debugging / headless checks.
  window.__liveBadges = {
    updated: function () { return slides.filter(isUpdated).map(function (s) { return s.idx + 1 }) },
    key: KEY
  }

  if (presentParam) return // presenting: no markers, no DOM changes at all

  var css = document.createElement('style')
  css.textContent =
    'section.lb-updated{outline:3px solid rgba(218,145,0,.85)!important;outline-offset:-3px}' +
    '.lb-pill{position:absolute;top:14px;right:16px;z-index:10;font:600 15px/1 -apple-system,"Helvetica Neue",sans-serif;' +
    'color:#fff;background:#d98e00;border-radius:999px;padding:5px 10px;letter-spacing:.02em;pointer-events:none}' +
    '#lb-counter{position:fixed;left:12px;bottom:12px;z-index:99999;font:600 13px/1 -apple-system,"Helvetica Neue",sans-serif;' +
    'color:#fff;background:rgba(217,142,0,.92);border:0;border-radius:999px;padding:7px 12px;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.25)}' +
    'body.lb-hidden section.lb-updated{outline:none!important}' +
    'body.lb-hidden .lb-pill,body.lb-hidden #lb-counter{display:none!important}' +
    '@media print{.lb-pill,#lb-counter{display:none!important}section.lb-updated{outline:none!important}}'
  document.head.appendChild(css)

  var counter = document.createElement('button')
  counter.id = 'lb-counter'
  counter.title = 'Jump to next updated slide (Shift+M hides markers)'
  document.body.appendChild(counter)
  if (isOverview) { counter.style.display = 'none'; var oc = document.createElement('style'); oc.textContent = '.lb-pill{font-size:44px!important;padding:12px 24px!important;top:24px!important;right:28px!important}section.lb-updated{outline-width:10px!important;outline-offset:-10px!important}#lb-counter{display:none!important}'; document.head.appendChild(oc) }

  function isUpdated(s) { return !state.seen[s.hash] }

  function setHidden(h) {
    document.body.classList.toggle('lb-hidden', h)
    try { h ? localStorage.setItem(HIDE_KEY, '1') : localStorage.removeItem(HIDE_KEY) } catch (e) {}
  }
  setHidden(localStorage.getItem(HIDE_KEY) === '1')

  function paint() {
    var n = 0
    slides.forEach(function (s) {
      if (!s.section) return
      var up = isUpdated(s)
      if (up) n++
      s.section.classList.toggle('lb-updated', up)
      var pill = s.section.querySelector(':scope > .lb-pill')
      if (up && !pill) {
        pill = document.createElement('div')
        pill.className = 'lb-pill'
        pill.textContent = 'Updated'
        s.section.appendChild(pill)
      } else if (!up && pill) {
        pill.remove()
      }
    })
    counter.textContent = n + (n === 1 ? ' slide updated' : ' slides updated')
    counter.style.display = n ? '' : 'none'
  }

  function activeIndex() {
    for (var i = 0; i < svgs.length; i++) if (svgs[i].classList.contains('bespoke-marp-active')) return i
    var m = /^#(\d+)/.exec(location.hash)
    return m ? parseInt(m[1], 10) - 1 : 0
  }

  // Dwell tracking: slide must stay active for DWELL_MS while the tab is visible.
  var dwellIdx = -1, dwellStart = 0
  setInterval(function () {
    if (isOverview) return // overview only displays badges; seeing a thumbnail doesn't count as viewed
    var i = activeIndex()
    var now = Date.now()
    if (i !== dwellIdx || document.hidden) { dwellIdx = document.hidden ? -1 : i; dwellStart = now; return }
    var s = slides[i]
    if (s && isUpdated(s) && now - dwellStart >= DWELL_MS) {
      state.seen[s.hash] = now
      save(state)
      paint()
    }
  }, 250)

  counter.addEventListener('click', function () {
    var cur = activeIndex()
    var ups = slides.filter(isUpdated)
    if (!ups.length) return
    var next = ups.filter(function (s) { return s.idx > cur })[0] || ups[0]
    location.hash = '#' + (next.idx + 1)
  })

  document.addEventListener('keydown', function (e) {
    if (e.shiftKey && (e.key === 'M' || e.key === 'm') && !e.metaKey && !e.ctrlKey && !e.altKey) {
      setHidden(!document.body.classList.contains('lb-hidden'))
    }
  })

  paint()
})()

// Presenter view: readable speaker notes
;(function () {
  if (!/view=presenter/.test(location.search)) return
  var st = document.createElement('style')
  st.textContent =
    '.bespoke-marp-presenter-note-container{padding:24px 28px !important}' +
    '.bespoke-marp-note, .bespoke-marp-note p{font:400 17px/1.6 -apple-system,"Segoe UI",sans-serif !important;color:#e6edf3 !important;max-width:60ch}' +
    '.dk-notes-h{font:700 11px -apple-system,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#8b949e;margin:0 0 10px}' +
    '.dk-notes p{margin:0 0 .65em !important}' +
    '.dk-notes ul{margin:0 0 .65em;padding-left:1.1em}.dk-notes li{margin:.25em 0}' +
    '.dk-notes .lbl{display:block;font:700 11px -apple-system,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#8b949e;margin:1em 0 .3em}' +
    '.dk-notes code{font:14px ui-monospace,SFMono-Regular,Menlo,monospace;background:#ffffff14;border-radius:4px;padding:1px 5px}'
  document.head.appendChild(st)
  // Notes are HTML comments ("Speaker notes: ..."). Format them for reading while presenting:
  // drop the prefix, `code` spans, blank-line paragraphs, "- " bullets, ALL-CAPS lines as small labels.
  // A single long paragraph is split into one sentence per line so it can be read at a glance.
  function esc(t) { return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') }
  function inline(t) { return esc(t).replace(/`([^`]+)`/g, '<code>$1</code>') }
  function format(el) {
    if (el.dataset.dkFormatted) return
    var raw = (el.innerText || el.textContent).replace(/^\s*Speaker notes:?\s*/i, '').trim()
    if (!raw) return
    var lines = raw.split(/\n/)
    if (lines.length === 1) lines = raw.split(/(?<=[.!?])\s+(?=[A-Z`"“])/)
    var html = '', list = false
    lines.forEach(function (ln) {
      var t = ln.trim()
      var bullet = /^[-•*]\s+/.test(t)
      if (list && !bullet) { html += '</ul>'; list = false }
      if (!t) return
      if (bullet) { if (!list) { html += '<ul>'; list = true } html += '<li>' + inline(t.replace(/^[-•*]\s+/, '')) + '</li>' }
      else if (/^[A-Z][A-Z0-9 '’"“”?:/-]{2,}$/.test(t)) html += '<span class="lbl">' + inline(t) + '</span>'
      else html += '<p>' + inline(t) + '</p>'
    })
    if (list) html += '</ul>'
    el.innerHTML = '<div class="dk-notes-h">Speaker notes</div><div class="dk-notes">' + html + '</div>'
    el.dataset.dkFormatted = '1'
  }
  function run() { document.querySelectorAll('.bespoke-marp-note').forEach(format) }
  document.addEventListener('DOMContentLoaded', run); run(); setTimeout(run, 400)
})()

// Comment mode: press C, click any element, type a comment, Enter.
// Comments go to the local comment server (comment-server.py, port 8765) -> comments.md
;(function () {
  if (/view=presenter/.test(location.search) || window.self !== window.top) return
  var on = false, hover = null
  var st = document.createElement('style')
  st.textContent = '.cm-hover{outline:2px dashed #8cf2a6 !important;outline-offset:2px}' +
    '.cm-box{position:fixed;z-index:99999;background:#151b23;border:1px solid #8cf2a6;border-radius:8px;padding:8px;box-shadow:0 8px 24px #000a;font:14px -apple-system,sans-serif;color:#f0f6fc;width:340px}' +
    '.cm-box textarea{width:100%;height:70px;background:#0d1117;color:#f0f6fc;border:1px solid #3d444d;border-radius:6px;padding:6px;font:14px -apple-system,sans-serif;box-sizing:border-box}' +
    '.cm-flag{position:fixed;top:10px;right:10px;z-index:99999;background:#238636;color:#fff;font:600 13px -apple-system,sans-serif;padding:4px 10px;border-radius:12px}' +
    '.cm-pin{position:fixed;z-index:99998;width:14px;height:14px;border-radius:50%;background:#8cf2a6;box-shadow:0 0 0 3px #0d1117}'
  document.head.appendChild(st)
  var flag = document.createElement('div'); flag.className = 'cm-flag'; flag.textContent = 'Comment mode · click an element · Esc to exit'
  function slideNo() { var h = location.hash.match(/\d+/); return h ? +h[0] : 1 }
  function titleOf(el) { var s = el.closest('section'); var h = s && s.querySelector('h1,h2'); return h ? h.textContent.trim() : '' }
  function path(el) { var p = []; while (el && el.tagName !== 'SECTION' && p.length < 5) { var t = el.tagName.toLowerCase(); var i = el.parentNode ? Array.prototype.indexOf.call(el.parentNode.children, el) + 1 : 1; p.unshift(t + ':nth-child(' + i + ')'); el = el.parentNode } return p.join(' > ') }
  function toggle() { on = !on; document.body.classList.toggle('cm-on', on); if (on) document.body.appendChild(flag); else { flag.remove(); if (hover) hover.classList.remove('cm-hover') } }
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'TEXTAREA') return
    if ((e.key === 'c' || e.key === 'C') && !e.metaKey && !e.ctrlKey && !e.altKey) { toggle(); e.preventDefault() }
    if (e.key === 'Escape' && on) { toggle(); e.preventDefault(); e.stopImmediatePropagation() }
  }, true)
  document.addEventListener('mouseover', function (e) { if (!on) return; if (hover) hover.classList.remove('cm-hover'); hover = e.target; if (!hover.closest('.cm-box')) hover.classList.add('cm-hover') }, true)
  document.addEventListener('click', function (e) {
    if (!on || e.target.closest('.cm-box')) return
    e.preventDefault(); e.stopPropagation()
    var el = e.target, r = el.getBoundingClientRect()
    var open = document.querySelector('.cm-box')
    if (open) {
      if (open.__el === el) { var t0 = open.querySelector('textarea'); if (t0) t0.focus(); return }
      open.remove()
    }
    var box = document.createElement('div'); box.className = 'cm-box'; box.__el = el
    var big = r.left < 0 || r.right > innerWidth || r.bottom > innerHeight // element larger than the view (e.g. the .zoom close-up image): anchor at the click
    var bx = big ? e.clientX - 40 : r.left, by = big ? e.clientY + 36 : r.bottom + 6
    box.style.left = Math.max(8, Math.min(bx, innerWidth - 360)) + 'px'; box.style.top = Math.max(8, Math.min(by, innerHeight - 130)) + 'px'
    box.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;color:#9198a1"><span>Slide ' + slideNo() + ' · Enter to send · Esc to cancel</span><button class="cm-x" title="Cancel" style="all:unset;cursor:pointer;color:#9198a1;font:600 16px -apple-system,sans-serif;padding:0 4px;line-height:1">×</button></div><textarea></textarea>'
    box.querySelector('.cm-x').addEventListener('click', function (ev) { ev.stopPropagation(); box.remove() })
    document.body.appendChild(box); var ta = box.querySelector('textarea'); ta.focus()
    ta.addEventListener('keydown', function (k) {
      k.stopPropagation()
      if (k.key === 'Escape') { k.preventDefault(); k.stopImmediatePropagation(); box.remove(); return }
      if (k.key === 'Enter' && !k.shiftKey) {
        k.preventDefault()
        var payload = { slide: slideNo(), title: titleOf(el), target: path(el), text: (el.innerText || el.getAttribute('src') || '').trim(), comment: ta.value }
        box.querySelector('textarea').disabled = true
        var saveLocal = function (why) {
          var all = JSON.parse(localStorage.getItem('deckComments') || '[]'); all.push(payload); localStorage.setItem('deckComments', JSON.stringify(all))
          try { navigator.clipboard.writeText('Slide ' + payload.slide + ' · ' + payload.title + ' — on "' + payload.text.slice(0, 80) + '": ' + payload.comment) } catch (x) {}
          box.innerHTML = '<div style="color:#d29922">Server unreachable (' + why + '). Saved in the browser and copied to clipboard; paste it into your assistant.</div>'
          setTimeout(function () { box.remove() }, 3500)
        }
        var ctl = new AbortController(); var tm = setTimeout(function () { ctl.abort() }, 2500)
        fetch('http://127.0.0.1:8765/comment', { method: 'POST', headers: { 'Content-Type': 'text/plain' }, body: JSON.stringify(payload), signal: ctl.signal })
          .then(function () { box.innerHTML = '<div style="color:#8cf2a6">✓ Saved</div>'; var pin = document.createElement('div'); pin.className = 'cm-pin'; pin.style.left = ((big ? e.clientX : r.left) - 7) + 'px'; pin.style.top = ((big ? e.clientY : r.top) - 7) + 'px'; document.body.appendChild(pin); setTimeout(function () { box.remove() }, 700) })
          .catch(function (err) { saveLocal(err && err.name === 'AbortError' ? 'timeout' : 'blocked') })
          .finally(function () { clearTimeout(tm) })
      }
    })
  }, true)
})()

// Discreet hint for comment mode: flashes on load, then stays faint; clickable; hidden with ?present
;(function () {
  if (/view=presenter/.test(location.search) || /[?&]present/.test(location.search) || window.self !== window.top) return
  var h = document.createElement('div')
  h.textContent = '?'
  h.title = 'Press ? for all keyboard shortcuts, C to comment on any element'
  h.style.cssText = 'position:fixed;right:14px;bottom:14px;z-index:99990;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font:700 18px -apple-system,sans-serif;color:#8cf2a6;background:#0d1117cc;border:1px solid #238636;border-radius:50%;cursor:pointer;opacity:1;transition:opacity 1.2s ease'
  document.addEventListener('DOMContentLoaded', function () { document.body.appendChild(h) })
  if (document.body) document.body.appendChild(h)
  setTimeout(function () { h.style.opacity = '0.22' }, 2500)
  h.addEventListener('mouseenter', function () { h.style.opacity = '1' })
  h.addEventListener('mouseleave', function () { h.style.opacity = '0.22' })
  h.addEventListener('click', function () { window.__deckHelp && window.__deckHelp() })
})()


// Fullscreen button, top right: same as the F key, easier to find; hidden with ?present, in presenter view and in iframes
;(function () {
  if (/view=presenter/.test(location.search) || /[?&]present/.test(location.search) || window.self !== window.top) return
  var b = document.createElement('button')
  b.type = 'button'
  b.title = 'Fullscreen (F)'
  b.setAttribute('aria-label', 'Fullscreen')
  b.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>'
  b.style.cssText = 'position:fixed;right:14px;top:14px;z-index:99990;width:40px;height:40px;padding:0;display:flex;align-items:center;justify-content:center;color:#f0f6fc;background:#0d1117cc;border:1px solid #3d444d;border-radius:50%;cursor:pointer;opacity:1;transition:opacity 1.2s ease'
  function place() { if (document.body && !b.parentNode) document.body.appendChild(b) }
  document.addEventListener('DOMContentLoaded', place); place()
  setTimeout(function () { b.style.opacity = '0.3' }, 2500)
  b.addEventListener('mouseenter', function () { b.style.opacity = '1' })
  b.addEventListener('mouseleave', function () { b.style.opacity = '0.3' })
  b.addEventListener('click', function () {
    var d = document.documentElement
    if (document.fullscreenElement || document.webkitFullscreenElement) (document.exitFullscreen || document.webkitExitFullscreen).call(document)
    else (d.requestFullscreen || d.webkitRequestFullscreen).call(d)
  })
  function sync() { b.style.display = (document.fullscreenElement || document.webkitFullscreenElement) ? 'none' : 'flex' }
  document.addEventListener('fullscreenchange', sync); document.addEventListener('webkitfullscreenchange', sync)
})()

// Transitions: morph what repeats between slides (used with `transition:` in the front matter; Marp uses the View Transitions API).
// 0) The first h1/h2 of each slide is the title: it holds still or cross-fades in place.
// 1) Same image / table row / list item on consecutive slides -> same view-transition-name -> it moves instead of fading.
// 2) Zoom: a slide with <div class="zoom" data-zoom="X% Y%"> zooms from the previous slide's mockup panel into that point,
//    clipped to the panel (no spill), because the whole panel is one transition group with overflow hidden.
;(function () {
  function h(s) { var x = 0; for (var i = 0; i < s.length; i++) x = (x * 31 + s.charCodeAt(i)) | 0; return 'm' + (x >>> 0).toString(36) }
  function key(el) {
    if (el.tagName === 'IMG') return 'img:' + el.getAttribute('src')
    var t = el.textContent.replace(/\s+/g, ' ').trim()
    return t.length > 2 ? el.tagName + ':' + t : null
  }
  var sections = [].slice.call(document.querySelectorAll('svg[data-marpit-svg] > foreignObject > section'))
  var skip = new Set(), css = ''
  sections.forEach(function (sec) { var t = sec.querySelector('h1, h2'); if (t) t.style.viewTransitionName = 'dk-title' })
  sections.forEach(function (sec, i) {
    var z = sec.querySelector('.zoom'); if (!z || i === 0) return
    var prev = sections[i - 1].querySelector('p > img, .zoom'); if (!prev) return
    var n = 'dkzoom' + i, o = z.getAttribute('data-zoom') || '50% 50%'
    z.style.viewTransitionName = n; prev.style.viewTransitionName = n
    skip.add(prev); z.querySelectorAll('img').forEach(function (im) { skip.add(im) })
    css += '::view-transition-group(' + n + '){overflow:hidden;border-radius:12px;animation-duration:.45s}' +
      '::view-transition-old(' + n + '){animation:dkzOut .45s cubic-bezier(.4,0,.2,1) both;transform-origin:' + o + '}' +
      '::view-transition-new(' + n + '){animation:dkzIn .45s cubic-bezier(.4,0,.2,1) both;transform-origin:' + o + '}' +
      // zoom only between the two slides; arriving at the mockup from elsewhere (or leaving the close-up) = the normal quick fade
      '::view-transition-new(' + n + '):only-child{animation:dkzFadeIn .12s ease both}' +
      '::view-transition-old(' + n + '):only-child{animation:dkzFadeOut .12s ease both}'
  })
  if (css) {
    var st = document.createElement('style')
    st.textContent = css + '@keyframes dkzOut{to{transform:scale(1.9);opacity:0}}@keyframes dkzIn{from{transform:scale(.53);opacity:0}}@keyframes dkzFadeIn{from{opacity:0}}@keyframes dkzFadeOut{to{opacity:0}}'
    document.head.appendChild(st)
  }
  sections.forEach(function (sec) {
    var used = {}
    sec.querySelectorAll('img, tr, li').forEach(function (el) {
      if (skip.has(el) || el.closest('header, footer')) return
      var k = key(el); if (!k) return
      var n = h(k); if (used[n]) return
      used[n] = 1
      el.style.viewTransitionName = n
    })
  })
})()

// Keyboard shortcuts help: press ? (or click the corner hint)
;(function () {
  if (/view=presenter/.test(location.search)) return
  var keys = [
    ['→  Space  PageDown', 'next slide'], ['←  PageUp', 'previous slide'], ['Home  End', 'first / last slide'],
    ['O  or  Esc', 'slide overview'], ['F', 'fullscreen'], ['P', 'presenter view: notes + timer'],
    ['T', 'switch theme: paper / terminal'], ['D', 'dark / light mode'], ['Shift + M', 'hide or show the "updated" badges'], ['C', 'comment mode: click an element, type, Enter'],
    ['?', 'this help']]
  var ov = null
  function show() {
    if (ov) { ov.remove(); ov = null; return }
    ov = document.createElement('div')
    ov.style.cssText = 'position:fixed;inset:0;z-index:100000;background:#010409cc;display:flex;align-items:center;justify-content:center'
    var rows = keys.map(function (k) { return '<tr><td style="padding:6px 18px 6px 0;text-align:right;white-space:nowrap"><span style="font:600 14px ui-monospace,Menlo,monospace;color:#8cf2a6;background:#0d1117;border:1px solid #3d444d;border-radius:6px;padding:2px 8px">' + k[0] + '</span></td><td style="padding:6px 0;color:#f0f6fc">' + k[1] + '</td></tr>' }).join('')
    ov.innerHTML = '<div style="background:#151b23;border:1px solid #3d444d;border-radius:14px;padding:22px 28px;font:15px -apple-system,sans-serif;box-shadow:0 20px 60px #000"><div style="font:600 13px ui-monospace,Menlo,monospace;letter-spacing:.06em;color:#9198a1;margin-bottom:10px">KEYBOARD SHORTCUTS</div><table style="border-collapse:collapse">' + rows + '</table><div style="margin-top:12px;color:#9198a1;font-size:13px">URL: <code>?present</code> hides all helpers · <code>?theme=terminal</code> · <code>?mode=dark</code></div></div>'
    ov.addEventListener('click', function () { ov.remove(); ov = null })
    document.body.appendChild(ov)
  }
  window.__deckHelp = show
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'TEXTAREA') return
    if (e.key === '?') { show(); e.preventDefault(); e.stopImmediatePropagation(); return }
    if (ov && e.key === 'Escape') { ov.remove(); ov = null; e.preventDefault(); e.stopImmediatePropagation() }
  }, true)
})()

// Esc always closes any open comment box first (window capture = runs before everything else)
;window.addEventListener('keydown', function (e) {
  if (e.key !== 'Escape') return
  var boxes = document.querySelectorAll('.cm-box')
  if (!boxes.length) return
  boxes.forEach(function (b) { b.remove() })
  e.preventDefault(); e.stopImmediatePropagation()
}, true)
