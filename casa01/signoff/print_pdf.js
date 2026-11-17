// node casa01/signoff/print_pdf.js <in.html> <out.pdf> [--png dir]  (17 x 11 in sheets)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [src, out, flag, dir] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1632, height: 1056 } });
  await p.goto('file://' + path.resolve(src), { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: out, width: '17in', height: '11in', printBackground: true, preferCSSPageSize: true });
  if (flag === '--png') {
    const els = await p.$$('section.page');
    for (let i = 0; i < els.length; i++) await els[i].screenshot({ path: `${dir}/signoff_${i + 1}.png` });
  }
  await b.close();
  console.log('wrote', out);
})();
