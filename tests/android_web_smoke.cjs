/* Run after prepare_android_assets.py with Playwright and a Chromium binary.
 * Network requests outside the local asset server are rejected, including fonts.
 * BROWSER_EXECUTABLE_PATH may select an existing Chromium executable.
 */
const {chromium} = require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES
  ? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES + '/playwright' : 'playwright');
const http = require('node:http'), fs = require('node:fs'), path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../android/build/assets/www');
const mime = {'.js':'application/javascript','.css':'text/css','.html':'text/html',
  '.wasm':'application/wasm','.json':'application/json','.svg':'image/svg+xml',
  '.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf'};
const missing = [], external = [];
const server = http.createServer((req,res) => {
  const url = new URL(req.url, 'http://localhost');
  const file = path.resolve(root, '.' + (url.pathname === '/' ? '/index.html' : url.pathname));
  if (!file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
  fs.readFile(file,(error,data) => {
    if(error) missing.push(url.pathname);
    res.writeHead(error ? 404 : 200, {'Content-Type': mime[path.extname(file)] || 'application/octet-stream'});
    res.end(error ? 'Missing' : data);
  });
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({headless:true,
    ...(process.env.BROWSER_EXECUTABLE_PATH ? {executablePath:process.env.BROWSER_EXECUTABLE_PATH} : {}),
    args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--disable-gpu']});
  try {
    const context = await browser.newContext({viewport:{width:1280,height:900}, reducedMotion:'reduce', serviceWorkers:'block'});
    await context.route('**/*', route => {
      if(new URL(route.request().url()).origin === origin) return route.continue();
      external.push(route.request().url());
      return route.abort();
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(origin);
    assert(await page.evaluate(() => !!window.katex), 'Bundled KaTeX did not load');
    const solve = async (expression, expectedError=false) => {
      await page.locator('#expression').fill(expression);
      await page.locator('#solveBtn').click();
      await page.locator(expectedError ? '.result-error' : '.result-top').waitFor({timeout:90000});
      assert.equal(await page.locator('.math-fallback,.katex-error').count(), 0, 'Formula rendering failed');
    };
    await solve('2x^2-5x+2=0');
    assert((await page.locator('.result-top').innerText()).includes('2'));
    await page.locator('[data-mode="derivee"]').click();
    await solve('sqrt(x^2+1)');
    assert(await page.locator('.result-top .mfrac').count() > 0, 'Missing vertical fraction');
    await page.locator('#extra-order').selectOption('2');
    await solve('sqrt(x^2+1)');
    assert.equal(await page.locator('.result-top .katex-display').count(), 3);
    await page.locator('#extra-order').selectOption('5');
    await solve('x^6');
    assert.equal(await page.locator('.result-top .katex-display').count(), 6);
    await page.locator('#extra-order').selectOption('1');
    await page.locator('#extra-point').fill('0');
    await solve('sqrt(x^2)', true);
    assert((await page.locator('.result-error').innerText()).includes('n’est pas dérivable'));
    await page.locator('#extra-point').fill('');
    await solve('sqrt(sqrt(x)+1)');
    await page.locator('#expression').fill('x^2+1');
    await page.locator('#expression').evaluate(element => element.setSelectionRange(0, element.value.length));
    await page.locator('[data-insert="sqrt()"]').click();
    assert.equal(await page.locator('#expression').inputValue(), 'sqrt(x^2+1)');
    for(const width of [320,360,390,760,1024]) {
      await page.setViewportSize({width,height:844});
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Page overflow at '+width);
    }
    if(process.env.ANDROID_SMOKE_SCREENSHOT) await page.screenshot({path:process.env.ANDROID_SMOKE_SCREENSHOT, fullPage:true});
    assert.deepEqual(external, [], 'Android bundle made external network requests');
    assert.deepEqual(missing, [], 'Android bundle is missing resources');
    assert.deepEqual(errors, [], 'Browser errors');
    console.log('PASS: bundled math worker, equations, roots, derivatives 1/2/5, invalid tangent, keypad, widths 320–1024, zero external requests.');
  } finally { await browser.close(); server.close(); }
})().catch(error => {console.error(error);server.close();process.exitCode=1;});
