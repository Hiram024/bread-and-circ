// QA-only: existing Playwright/Chrome, real browser, server and DB owned by QA.
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const { chromium } = require(path.join(process.env.LOCALAPPDATA, 'ms-playwright-go', '1.57.0', 'package'));

(async () => {
  const base = process.argv[2];
  const out = path.resolve('analisis/reportes/b4');
  const expected = JSON.parse(fs.readFileSync('ml/resultados/b3/perfiles_candidato.json', 'utf8'));
  const browser = await chromium.launch({executablePath:path.join(process.env.ProgramFiles, 'Google', 'Chrome', 'Application', 'chrome.exe'),headless:true});
  try {
    const context = await browser.newContext({viewport:{width:1440,height:1080}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base, {waitUntil:'networkidle'});
    await page.waitForFunction(() => document.querySelectorAll('#draftProfile option').length === 4);
    const options = await page.locator('#draftProfile option').evaluateAll(nodes => nodes.map(n => ({value:n.value,text:n.textContent})));
    assert.deepEqual(options.map(o=>o.value), ['1','2','3','4']);
    for (const profile of expected) assert(options.find(o=>o.value===String(profile.perfil_id)).text.includes(profile.nombre));
    assert.equal(await page.locator('#profileFilter option').count(),5);
    const body = await page.locator('body').innerText();
    assert(body.includes('ccpc-2009-2024-k4-v1'));
    assert(!body.includes('cinco perfiles') && !body.includes('k=5') && !body.includes('cinco centroides'));
    await page.locator('#nav button[data-tab="explorar"]').click();
    await page.locator('#profileFilter').selectOption('4');
    await page.waitForFunction(() => {
      const rows=[...document.querySelectorAll('#obsRows tr')];
      return rows.length>0 && rows.every(row=>row.cells.length===7 && row.cells[4].textContent==='P4');
    });
    await page.locator('#nav button[data-tab="fichas"]').click();
    await page.locator('#draftProfile').selectOption('1');
    await page.locator('#draftButton').click();
    await page.locator('#reviewArea').waitFor({state:'visible'});
    await page.locator('#reviewer').fill('QA_BROWSER_TEMPORAL');
    await page.locator('#reviewCheck').check();
    await page.locator('#draftProfile').selectOption('2');
    const invalidated = !await page.locator('#reviewCheck').isChecked() || !await page.locator('#reviewArea').isVisible();
    if (!invalidated) {
      const stale = page.waitForResponse(r=>r.url().endsWith('/api/approve')&&r.request().method()==='POST');
      await page.locator('#approveButton').click();
      assert.equal((await stale).status(),409);
    }
    await page.locator('#draftButton').click();
    await page.locator('#reviewArea').waitFor({state:'visible'});
    await page.locator('#reviewer').fill('QA_BROWSER_TEMPORAL');
    await page.locator('#reviewCheck').check();
    const approvedResponse = page.waitForResponse(r=>r.url().endsWith('/api/approve')&&r.request().method()==='POST');
    await page.locator('#approveButton').click();
    const response = await approvedResponse;
    assert.equal(response.status(),200);
    const approved = await response.json();
    await page.locator('#approvalStatus a').waitFor({state:'visible'});
    const pdf = await context.request.get(new URL(approved.download_url,base).href);
    assert.equal(pdf.status(),200);
    fs.writeFileSync(path.join(out,'qa_browser_approved.pdf'),await pdf.body());
    await page.screenshot({path:path.join(out,'qa_browser.png'),fullPage:true});
    assert.deepEqual(errors,[]);
    const result = {browser:browser.version(),base,options,real_browser:true,query_filter:true,
      selection_change_invalidated:invalidated,approval_status:response.status(),pdf_status:pdf.status(),page_errors:errors};
    fs.writeFileSync(path.join(out,'qa_browser_resultados.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify(result,null,2));
    await context.close();
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exit(1);});
