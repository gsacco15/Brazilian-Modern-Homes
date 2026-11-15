// Print casa01/lookbook/print.html to a 16:9 PDF (1333x750 px pages) with headless Chromium.
//   node casa01/lookbook/make_pdf.js [out.pdf] [--png dir]
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const here = __dirname;
  const out = process.argv[2] || path.join(here, '..', 'Casa01_Lookbook.pdf');
  const pngIdx = process.argv.indexOf('--png');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1333, height: 750 } });
  await page.goto('file://' + path.join(here, 'print.html'), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: out, width: '1333px', height: '750px', printBackground: true,
                   margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  if (pngIdx > 0) {            // optional page previews
    const dir = process.argv[pngIdx + 1];
    const n = await page.$$eval('section.page', s => s.length);
    for (let i = 0; i < n; i++) {
      const el = (await page.$$('section.page'))[i];
      await el.screenshot({ path: path.join(dir, `page_${String(i + 1).padStart(2, '0')}.png`) });
    }
  }
  await browser.close();
  console.log('wrote', out);
})();
