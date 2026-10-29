// B6-only: real Chrome browser zoom preferences and keyboard acceptance, no production edits.
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert/strict');
const {chromium}=require(path.join(process.env.LOCALAPPDATA,'ms-playwright-go','1.57.0','package'));
const OUT=path.resolve('analisis/reportes/b6');
const REUSED=JSON.parse(fs.readFileSync('analisis/reportes/b5/qa_numerical.json','utf8'));
const metrics=page=>page.evaluate(()=>({innerWidth,innerHeight,outerWidth,outerHeight,dpr:devicePixelRatio,visualScale:visualViewport.scale,cssZoom:getComputedStyle(document.documentElement).zoom,scroll:document.documentElement.scrollWidth}));
async function readyPlots(page){await page.waitForFunction(()=>[...document.querySelectorAll('.tab.active .js-plotly-plot')].filter(e=>e.clientWidth>0).every(e=>e._fullLayout&&e._fullLayout.width<=e.clientWidth+1));}
async function activate(page,selector){await page.locator(selector).focus();await page.keyboard.press('Enter');}
async function capture(page,name,selector){
 if(selector)await page.locator(selector).scrollIntoViewIfNeeded();
 await readyPlots(page);
 const session=await page.context().newCDPSession(page);
 const result=await session.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false,fromSurface:true});
 const png=Buffer.from(result.data,'base64'),m=await metrics(page);
 assert(Math.abs(png.readUInt32BE(16)-m.innerWidth*m.dpr)<20,'Screenshot must capture the full native zoomed viewport');
 fs.writeFileSync(path.join(OUT,name),png);await session.detach();
}
async function tabTo(page,id){
 for(let i=0;i<30;i++){
  if(await page.evaluate(id=>document.activeElement?.id===id,id))return;
  await page.keyboard.press('Tab');
 }
 throw Error('Keyboard did not reach '+id);
}
(async()=>{
 const base=process.argv[2]||'http://127.0.0.1:61286/',results=[];
 for(const factor of [1,2]){
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'qa-b6-zoom-'));
  const prefpath=path.join(profile,'Default','Preferences');fs.mkdirSync(path.dirname(prefpath));
  const level=Math.log(factor)/Math.log(1.2);
  fs.writeFileSync(prefpath,JSON.stringify({partition:{default_zoom_level:{x:level}}}));
  const context=await chromium.launchPersistentContext(profile,{executablePath:path.join(process.env.ProgramFiles,'Google','Chrome','Application','chrome.exe'),headless:false,viewport:null,args:['--window-size=1440,1050','--window-position=30,30']});
  const errors=[],external=[];
  try{
   const page=context.pages()[0]||await context.newPage();
   page.on('pageerror',e=>errors.push(e.message));
   page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('blob:')&&!r.url().startsWith('data:'))external.push(r.url());});
   await page.goto(base,{waitUntil:'networkidle'});
   await page.waitForFunction(()=>document.querySelectorAll('#nationalRows tr').length===6);
   const before=await metrics(page),steps=[],navFocus=[];
   await page.locator('#nav button').first().focus();
   for(let i=0;i<6;i++){
    const focus=await page.evaluate(()=>{const e=document.activeElement,r=e.getBoundingClientRect();return {tab:e.dataset.tab,top:r.top,bottom:r.bottom,viewport:innerHeight,outline:getComputedStyle(e).outlineStyle};});
    assert(focus.top>=0&&focus.bottom<=focus.viewport,`Focused navigation ${focus.tab} outside viewport at zoom ${factor}`);
    assert(focus.outline!=='none');navFocus.push(focus);if(i<5)await page.keyboard.press('Tab');
   }
   assert.equal(before.cssZoom,'1');assert.equal(before.visualScale,1);
   await activate(page,'#nav button[data-tab="resumen"]');await readyPlots(page);
   for(const [i,row] of REUSED.annual.entries()){
    const cells=await page.locator('#nationalRows tr').nth(i).locator('td').allTextContents();
    assert.equal(cells[2],row.participacion_pct.toFixed(1)+'%');assert.equal(cells[3],row.ns_pct.toFixed(1)+'%');
   }
   assert((await page.locator('#nationalInsights').innerText()).includes('+7.78 pp'));
   assert((await page.locator('#nationalInsights').innerText()).includes('-2.41 pp'));
   const national=await page.locator('#nationalChart').evaluate(e=>({years:e._fullLayout.xaxis.categoryarray,axis:e._fullLayout.yaxis.title.text,symbols:e.data.map(t=>t.marker.symbol),names:e.data.map(t=>t.name)}));
   console.log('National chart actual:', JSON.stringify(national));
   assert.deepEqual(national.years,['2009','2012','2015','2018','2021','2024']);assert(national.axis.includes('%'));assert((await page.locator('#distributionChart').evaluate(e=>e._fullLayout.xaxis.title.text)).includes('Unidades'));
   assert.deepEqual(national.symbols,['circle','diamond']);steps.push({screen:'Panorama',metrics:await metrics(page),chart:national});
   await capture(page,`qa_zoom_${factor*100}_panorama.png`,'#nationalChart');
   await page.keyboard.press('Tab');await page.keyboard.press('Enter');
   await page.waitForFunction(()=>document.querySelector('#tab-perfiles').classList.contains('active'));await readyPlots(page);
   const profileText=await page.locator('#profileCards').innerText();
   for(const p of REUSED.profiles)assert(profileText.includes(p.nombre));
   const changes=await page.locator('#changeChart').evaluate(e=>({axis:e._fullLayout.yaxis.title.text,values:e.data.map(t=>t.y),names:e.data.map(t=>t.name)}));
   assert(changes.axis.includes('pp'));assert((await page.locator('#profileChart').evaluate(e=>e._fullLayout.yaxis.title.text)).includes('%'));assert(changes.values[0][0]<0&&changes.values[0][1]>0);
   steps.push({screen:'Perfiles',metrics:await metrics(page),chart:changes});await capture(page,`qa_zoom_${factor*100}_perfiles.png`,'#changeChart');
   await page.keyboard.press('Tab');await page.keyboard.press('Enter');
   await page.waitForFunction(()=>document.querySelector('#pageRange').textContent.includes('1–100'));
   await tabTo(page,'stateFilter');await page.keyboard.press('Home');await page.keyboard.press('ArrowDown');
   await page.waitForFunction(()=>document.querySelector('#stateFilter').value==='1'&&document.querySelector('#pageRange').textContent.includes('de 55'));
   await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'profileFilter');
   await page.keyboard.press('End');
   await page.waitForFunction(()=>document.querySelector('#profileFilter').value==='4'&&document.querySelectorAll('#obsRows button').length>0);
   await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'ageFilter');
   await page.keyboard.press('End');
   await page.waitForFunction(()=>document.querySelector('#ageFilter').value==='60+'&&document.querySelectorAll('#obsRows button').length>0);
   await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'municipioSearch');
   await page.keyboard.type('AGUAS');
   await page.waitForFunction(()=>document.querySelector('#pageRange').textContent==='1–1 de 1');
   const selected=await page.locator('#obsRows tr').innerText();assert(selected.includes('60+')&&selected.includes('P4'));
   await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'clearFilters');await page.keyboard.press('Enter');
   await page.waitForFunction(()=>document.querySelector('#pageRange').textContent==='1–100 de 8,541');
   for(let i=0;i<6&&await page.evaluate(()=>document.activeElement.className!=='rowDetail');i++)await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.className),'rowDetail');
   const key=await page.evaluate(()=>document.activeElement.dataset.key);await page.keyboard.press('Enter');
   await page.waitForFunction(()=>!document.querySelector('#observationDetail').classList.contains('hidden'));
   assert.equal(await page.evaluate(()=>document.activeElement.id),'observationDetail');
   assert.equal(await page.locator('#detailRows tr').count(),6);
   const firstDetail=await page.locator('#detailTitle').innerText();
   await page.keyboard.press('Shift+Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'nextPage');await page.keyboard.press('Enter');
   await page.waitForFunction(()=>document.querySelector('#pageRange').textContent==='101–200 de 8,541');
   assert(await page.locator('#observationDetail').isHidden());
   await page.keyboard.press('Shift+Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'prevPage');await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelector('#pageRange').textContent==='1–100 de 8,541');
   await page.locator('#obsRows button').first().focus();await page.keyboard.press('Enter');await readyPlots(page);
   assert.equal(await page.locator('#detailTitle').innerText(),firstDetail);assert((await page.locator('#detailChart').evaluate(e=>e._fullLayout.yaxis.title.text)).includes('%'));
   const focus=await page.locator('#observationDetail').evaluate(e=>({active:document.activeElement===e,outline:getComputedStyle(e).outlineStyle}));assert(focus.active&&focus.outline!=='none');
   steps.push({screen:'Explorador',metrics:await metrics(page),key,detail:firstDetail,keyboard_filters:true,keyboard_clear:true,keyboard_pagination:true,keyboard_detail:true,focus});
   await capture(page,`qa_zoom_${factor*100}_explorador.png`,'#observationDetail');
   await activate(page,'#nav button[data-tab="auditoria"]');await page.locator('#coverageContent').waitFor({state:'visible'});
   const text=await page.locator('#coverageContent').innerText();assert(text.includes('3,844')&&text.includes('81,666,826')&&text.includes('98,330,348'));
   await page.locator('#coverageContent summary').first().focus();await page.keyboard.press('Enter');
   assert.equal(await page.locator('#overlapRows tr').count(),15);
   steps.push({screen:'Auditoría',metrics:await metrics(page),keyboard_disclosure:true});await capture(page,`qa_zoom_${factor*100}_auditoria.png`,'#coverageRows');
   for(const step of steps)assert(step.metrics.scroll<=step.metrics.innerWidth+1,`${factor}/${step.screen} page overflow`);
   assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
   results.push({factor,level,before,navFocus,steps,page_errors:errors,external_requests:external,browser:context.browser().version(),preferences_written:{partition:{default_zoom_level:{x:level}}}});
  }finally{
   await context.close();
   // Only the freshly created QA profile under the OS temp root may be removed.
   if(path.dirname(profile)!==os.tmpdir()||!path.basename(profile).startsWith('qa-b6-zoom-'))throw Error('Unsafe QA profile cleanup');
   fs.rmSync(profile,{recursive:true,force:true,maxRetries:5,retryDelay:200});
  }
 }
 assert.equal(results[1].before.outerWidth,results[0].before.outerWidth);
 assert.equal(results[1].before.outerHeight,results[0].before.outerHeight);
 assert.equal(results[1].before.dpr/results[0].before.dpr,2);
 assert(Math.abs(results[0].before.innerWidth/results[1].before.innerWidth-2)<.01);
 const output={status:'PASA',method:'Native Chrome browser zoom persisted in isolated temporary profile, not CSS/pageScale/device-scale/viewport emulation',results};
 fs.writeFileSync(path.join(OUT,'qa_zoom_resultados.json'),JSON.stringify(output,null,2)+'\n');console.log(JSON.stringify(output,null,2));
})().catch(error=>{console.error(error);process.exit(1)});
