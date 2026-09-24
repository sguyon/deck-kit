// shot.js OUT.png IN.html [IN2.html OUT2.png ...] — screenshot .stage at 2x, transparent bg.
// Usage: node shot.js <html> <png> [<html> <png> ...]
const path = require('path'), fs = require('fs');
const pwPath = process.env.PW_MODULE;
const { chromium } = require(pwPath);
(async () => {
  const opts = {};
  if (process.env.PW_EXEC) opts.executablePath = process.env.PW_EXEC;
  const browser = await chromium.launch(opts);
  const timer = setTimeout(() => { console.error('shot.js: timeout'); process.exit(2); }, 25000);
  try {
    const page = await browser.newPage({ deviceScaleFactor: 2, viewport: { width: 2400, height: 1600 } });
    const a = process.argv.slice(2);
    for (let i = 0; i < a.length; i += 2) {
      await page.goto('file://' + path.resolve(a[i]), { timeout: 8000 });
      await page.evaluate(() => document.fonts.ready);
      await page.waitForFunction(() => window.__ready !== false, null, { timeout: 5000 });
      const el = await page.$('.stage');
      await el.screenshot({ path: a[i + 1], omitBackground: true, timeout: 8000 });
      console.log('  ->', a[i + 1]);
    }
  } finally { clearTimeout(timer); await browser.close(); }
})().catch(e => { console.error('shot.js:', e.message.split('\n')[0]); process.exit(1); });
