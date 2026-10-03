// Render the generated portfolio HTML to PDF with headless Chromium.
// Usage: node render.js <input.html> <output.pdf>
const { chromium } = require("playwright");
const path = require("path");

(async () => {
  const [input, output] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + path.resolve(input), { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: output, preferCSSPageSize: true, printBackground: true });
  await browser.close();
})().catch((err) => { console.error(err); process.exit(1); });
