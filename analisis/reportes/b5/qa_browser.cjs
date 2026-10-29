// Independent QA: real Chrome/HTTP/SQLite; only network faults use a controlled boundary.
const fs=require('fs'), path=require('path'), assert=require('assert/strict');
const {chromium}=require(path.join(process.env.LOCALAPPDATA,'ms-playwright-go','1.57.0','package'));
const OUT='analisis/reportes/b5';
const normalize=value=>value.replace(/[\s,]/g,'');
const hasNumber=(text,value)=>normalize(text).includes(String(value));
async function readyRows(page,count){await page.waitForFunction(n=>document.querySelectorAll('#obsRows button').length===n,count);}
async function cleared(page){await page.locator('#clearFilters').click();await readyRows(page,100);await page.waitForFunction(()=>document.querySelector('#pageRange').textContent.includes('1–100'));}
(async()=>{
 const base=process.argv[2], browser=await chromium.launch({executablePath:path.join(process.env.ProgramFiles,'Google','Chrome','Application','chrome.exe'),headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1080}}),page=await context.newPage(),errors=[],consoleErrors=[],external=[],httpErrors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',e=>{if(e.type()==='error')consoleErrors.push(e.text());});
  page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('blob:')&&!r.url().startsWith('data:'))external.push(r.url());});
  page.on('response',r=>{if(r.status()>=400)httpErrors.push({path:new URL(r.url()).pathname,status:r.status(),method:r.request().method()});});
  await page.goto(base,{waitUntil:'networkidle'});
  await page.waitForFunction(()=>document.querySelectorAll('#nationalRows tr').length===6&&document.querySelectorAll('#draftProfile option').length===4);
  const health=await (await context.request.get(base+'health')).json();
  assert.equal(health.package_version,'ccpc-2009-2024-k4-v1');assert.equal(health.k,4);
  const summary=await (await context.request.get(base+'api/summary')).json();
  const years=await page.locator('#nationalRows tr').evaluateAll(rows=>rows.map(row=>Number(row.cells[0].textContent.match(/20\d\d/)[0])));
  assert.deepEqual(years,[2009,2012,2015,2018,2021,2024]);
  for(const [i,row] of summary.historico.entries()){
   const text=await page.locator('#nationalRows tr').nth(i).innerText();
   assert(hasNumber(text,row.SV));assert(hasNumber(text,row.SV+row.NV));
   assert(text.includes(row.participacion_pct.toFixed(2))||text.includes(row.participacion_pct.toFixed(1)));
  }
  const plotted=await page.locator('#nationalChart').evaluate(el=>el.data.map(t=>({name:t.name,x:t.x,y:t.y,symbol:t.marker.symbol})));
  assert.equal(plotted.length,2);assert.notEqual(plotted[0].symbol,plotted[1].symbol);
  assert((await page.locator('#tab-resumen').innerText()).includes('No cambia con los filtros'));
  await page.screenshot({path:OUT+'/qa_panorama.png',fullPage:true});
  await page.locator('#nav button[data-tab="perfiles"]').focus();await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.querySelector('#tab-perfiles').classList.contains('active'));
  const candidates=JSON.parse(fs.readFileSync('ml/resultados/b3/perfiles_candidato.json','utf8'));
  for(const p of candidates){const text=await page.locator('#profileComparison').innerText();assert(text.includes(p.nombre));assert(hasNumber(text,p.n_unidades));}
  assert.equal(await page.locator('#profileComparison tr').count(),4);
  await page.waitForFunction(()=>document.querySelector('#changeChart').data?.length===2);
  await page.screenshot({path:OUT+'/qa_perfiles.png',fullPage:true});
  await page.locator('#nav button[data-tab="explorar"]').click();await readyRows(page,100);
  const all=await (await context.request.get(base+'api/observations')).json();
  assert(hasNumber(await page.locator('#pageRange').innerText(),8541));
  const wholeSummary=await page.locator('#selectionSummary').innerText();assert(hasNumber(wholeSummary,8541));assert(hasNumber(wholeSummary,1825));
  await page.locator('#selectionSummary summary').click();
  assert.equal(await page.locator('#selectionSummary tbody tr').count(),6);
  for(const [i,row] of all.analytics.historico.entries()){
   const text=await page.locator('#selectionSummary tbody tr').nth(i).innerText();
   assert(text.includes(row.media_tasa_pct.toFixed(1)));assert(hasNumber(text,8541));
  }
  await page.locator('#selectionSummary summary').click();
  assert(!await page.locator('#prevPage').isEnabled());assert(await page.locator('#nextPage').isEnabled());
  const firstKey=await page.locator('#obsRows button').first().getAttribute('data-key');
  await page.locator('#obsRows button').first().focus();await page.keyboard.press('Enter');
  await page.locator('#observationDetail').waitFor({state:'visible'});
  assert.equal(await page.locator('#detailRows tr').count(),6);
  const first=all.items[0];const detail=(await page.locator('#detailTitle').innerText())+' '+(await page.locator('#detailContext').innerText());
  assert(detail.includes(first.MPIONOM)&&detail.includes(first.grupo_edad));
  for(const [i,y] of [2009,2012,2015,2018,2021,2024].entries())assert((await page.locator('#detailRows tr').nth(i).innerText()).includes(first['tasa_'+y].toFixed(1)));
  await page.locator('#nextPage').click();await page.waitForFunction(()=>document.querySelector('#pageRange').textContent.includes('101–200'));
  await readyRows(page,100);assert(await page.locator('#observationDetail').isHidden());
  assert.equal(await page.locator('#selectionSummary').innerText(),wholeSummary);
  const secondFirst=await page.locator('#obsRows button').first().getAttribute('data-key');assert.notEqual(firstKey,secondFirst);
  await page.locator('#prevPage').click();await page.waitForFunction(()=>document.querySelector('#pageRange').textContent.includes('1–100'));
  await page.locator('#stateFilter').selectOption('1');
  await page.waitForFunction(()=>document.querySelectorAll('#obsRows button').length>0&&[...document.querySelectorAll('#obsRows tr')].every(r=>r.textContent.toUpperCase().includes('AGUASCALIENTES')));
  await page.locator('#profileFilter').selectOption('4');await page.locator('#ageFilter').selectOption('60+');await page.locator('#municipioSearch').fill('AGUAS');
  const combined=await (await context.request.get(base+'api/observations?estado=1&perfil=4&edad=60%2B&q=AGUAS')).json();
  await readyRows(page,combined.items.length);
  await page.waitForFunction(n=>document.querySelector('#obsCount').textContent.replace(/[\s,]/g,'').includes(String(n)),combined.total);
  assert((await page.locator('#obsRows').innerText()).includes('60+'));
  await page.locator('#municipioSearch').fill('QA_NO_MATCH_298129');
  await page.waitForFunction(()=>document.querySelector('#obsStatus').textContent.toLowerCase().includes('sin coincidencias'));
  await readyRows(page,0);
  assert((await page.locator('#obsStatus').innerText()).toLowerCase().includes('sin'));
  assert(await page.locator('#observationDetail').isHidden());
  assert(!await page.locator('#prevPage').isEnabled()&&!await page.locator('#nextPage').isEnabled());
  await cleared(page);
  // Hold an actual old response independently of AbortSignal, then deliver it after the new one.
  const old=await (await context.request.get(base+'api/observations?q=AGUAS')).json();
  await page.evaluate(payload=>{
   window.qaOriginalFetch=window.fetch.bind(window);
   window.fetch=(url,opts)=>new URL(url,location.href).searchParams.get('q')==='AGUAS'?
    new Promise(resolve=>{window.qaReleaseOld=()=>resolve(new Response(JSON.stringify(payload),{status:200,headers:{'Content-Type':'application/json'}}));}):window.qaOriginalFetch(url,opts);
  },old);
  await page.locator('#municipioSearch').fill('AGUAS');await page.waitForFunction(()=>typeof window.qaReleaseOld==='function');
  await page.locator('#municipioSearch').fill('Monterrey');
  const fresh=await (await context.request.get(base+'api/observations?q=Monterrey')).json();
  await readyRows(page,fresh.items.length);await page.waitForFunction(()=>document.querySelector('#obsRows').textContent.toUpperCase().includes('MONTERREY'));
  const freshText=await page.locator('#obsRows').innerText();
  await page.evaluate(async()=>{window.qaReleaseOld();await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));window.fetch=window.qaOriginalFetch;});
  assert.equal(await page.locator('#obsRows').innerText(),freshText);
  // A network error must clear counts, detail, rows and charts rather than retain old results.
  await page.evaluate(()=>{window.fetch=(url,opts)=>new URL(url,location.href).searchParams.get('q')==='QA_ERROR'?Promise.reject(new Error('QA controlled network failure')):window.qaOriginalFetch(url,opts);});
  await page.locator('#municipioSearch').fill('QA_ERROR');
  await page.waitForFunction(()=>document.querySelector('#obsStatus').textContent.includes('QA controlled'));
  assert.equal(await page.locator('#obsRows button').count(),0);assert(await page.locator('#selectionSummary').isHidden());assert(await page.locator('#observationDetail').isHidden());
  assert(!hasNumber(await page.locator('#obsCount').innerText(),fresh.total)||fresh.total===0);
  await page.evaluate(()=>window.fetch=window.qaOriginalFetch);await cleared(page);
  // Controlled null and HTML metacharacters at network boundary; production bytes remain intact.
  const nullable=structuredClone(all);nullable.items=nullable.items.slice(0,1);nullable.total=1;nullable.items[0].tasa_2009=null;nullable.items[0].MPIONOM='<img src=x onerror=alert(1)> QA';
  await page.evaluate(payload=>{window.fetch=(url,opts)=>new URL(url,location.href).searchParams.get('q')==='QA_NULL'?Promise.resolve(new Response(JSON.stringify(payload),{status:200})):window.qaOriginalFetch(url,opts);},nullable);
  await page.locator('#municipioSearch').fill('QA_NULL');await readyRows(page,1);await page.locator('#obsRows button').first().click();
  assert.equal(await page.locator('#obsRows img').count(),0);assert((await page.locator('#obsRows').innerText()).includes('<img'));
  const nullText=await page.locator('#detailRows tr').first().innerText();assert(!nullText.includes('0.0%'));
  assert(/—|Sin dato|sin dato|N\/D/.test(nullText));
  await page.evaluate(()=>window.fetch=window.qaOriginalFetch);await cleared(page);
  await page.screenshot({path:OUT+'/qa_explorador.png',fullPage:true});
  await page.locator('#nav button[data-tab="auditoria"]').click();await page.locator('#coverageContent').waitFor({state:'visible'});
  const auditText=await page.locator('#coverageContent').innerText();for(const n of [12385,8541,3844,81666826,98330348])assert(hasNumber(auditText,n));
  assert(auditText.includes('superponen'));assert((await page.locator('#tab-auditoria').innerText()).includes('no certifican'));
  assert.equal(await page.locator('#exclusionRows tr').count(),5);
  for(const link of await page.locator('#tab-auditoria a').evaluateAll(nodes=>nodes.map(n=>n.href)))assert.equal((await context.request.get(link)).status(),200);
  await page.screenshot({path:OUT+'/qa_auditoria.png',fullPage:true});
  // B4 regression: real CSV upload and real reviewed content/version-bound approval/PDF.
  await page.locator('#nav button[data-tab="clasificar"]').click();
  const template=await (await context.request.get(base+'api/template')).body();
  await page.locator('#csvFile').setInputFiles({name:'qa_valid.csv',mimeType:'text/csv',buffer:template});
  const downloaded=page.waitForEvent('download');await page.locator('#sendCsv').click();await downloaded;
  await page.waitForFunction(()=>document.querySelector('#csvFeedback').textContent.includes('Clasificación realizada'));
  await page.locator('#csvFile').setInputFiles({name:'qa_invalid.csv',mimeType:'text/csv',buffer:Buffer.from('unidad_id,tasa_2009\nQA,101\n')});
  await page.locator('#sendCsv').click();await page.waitForFunction(()=>document.querySelector('#csvFeedback').textContent.includes('Error de validación'));
  await page.locator('#nav button[data-tab="fichas"]').click();await page.locator('#draftProfile').selectOption('1');await page.locator('#draftButton').click();await page.locator('#reviewArea').waitFor({state:'visible'});
  await page.locator('#reviewCheck').check();
  await page.locator('#nav button[data-tab="perfiles"]').click();await page.locator('.exploreProfile[data-profile="4"]').click();
  await page.waitForFunction(()=>document.querySelector('#profileFilter').value==='4'&&document.querySelectorAll('#obsRows button').length===100);
  assert.equal(await page.locator('#draftProfile').inputValue(),'1');assert(await page.locator('#reviewCheck').isChecked());
  await page.locator('#nav button[data-tab="fichas"]').click();assert(await page.locator('#reviewArea').isVisible());
  await page.locator('#draftProfile').selectOption('2');assert(await page.locator('#reviewArea').isHidden());assert(!await page.locator('#reviewCheck').isChecked());
  await page.locator('#draftButton').click();await page.locator('#reviewArea').waitFor({state:'visible'});await page.locator('#reviewer').fill('QA_B5_TEMPORAL');await page.locator('#reviewCheck').check();
  const approvedResponse=page.waitForResponse(r=>r.url().endsWith('/api/approve')&&r.request().method()==='POST');await page.locator('#approveButton').click();
  const approved=await approvedResponse;assert.equal(approved.status(),200);const record=await approved.json();
  const pdf=await context.request.get(base+record.download_url.replace(/^\//,''));assert.equal(pdf.status(),200);fs.writeFileSync(OUT+'/qa_approved.pdf',await pdf.body());
  const shown=await (await context.request.get(base+'api/draft/2')).json();
  const stale=await context.request.post(base+'api/approve',{data:{profile_id:2,reviewer:'QA_B5_TEMPORAL',confirmed:true,package_version:'obsolete',package_digest:shown.package_digest,draft_digest:shown.draft_digest}});assert.equal(stale.status(),409);
  const widths=[],contrasts=[];
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1080});
   for(const tab of ['resumen','perfiles','explorar','auditoria']){
    await page.locator(`#nav button[data-tab="${tab}"]`).click();
    if(tab==='explorar')await readyRows(page,100);
    await page.waitForFunction(()=>[...document.querySelectorAll('.tab.active .js-plotly-plot')].filter(el=>el.getBoundingClientRect().width>0).every(el=>el._fullLayout&&el._fullLayout.width<=el.clientWidth+1));
    const dimensions=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
    assert(dimensions.scroll<=dimensions.width+1,`${width}/${tab} page overflow: ${dimensions.scroll}`);
    widths.push({tab,...dimensions});
    if(width===1440){
     const samples=await page.evaluate(()=>{
      const rgb=s=>s.match(/[\d.]+/g).map(Number),lum=values=>values.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
      return [...document.querySelectorAll('.tab.active .chartNote,.tab.active .stat .desc,.tab.active .hint,.tab.active .scope,.tab.active .filters label,.tab.active .softBadge')].filter(el=>el.getBoundingClientRect().height>0).map(el=>{
       const foreground=getComputedStyle(el).color;let node=el,background='rgb(255,255,255)';
       while(node){const bg=getComputedStyle(node).backgroundColor,parts=rgb(bg);if(parts.length===3||parts[3]!==0){background=bg;break;}node=node.parentElement;}
       const a=lum(rgb(foreground)),b=lum(rgb(background));return {text:el.textContent.trim().slice(0,80),foreground,background,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
      });
     });
     for(const sample of samples)assert(sample.ratio>=4.5,`Small text contrast ${sample.ratio.toFixed(2)}: ${sample.text}`);
     contrasts.push({tab,samples});
    }
   }
   await page.screenshot({path:OUT+`/qa_width_${width}.png`,fullPage:true});
  }
  await page.locator('#nav button[data-tab="explorar"]').focus();await page.keyboard.press('Enter');await readyRows(page,100);
  await page.locator('#municipioSearch').focus();const focus=await page.locator('#municipioSearch').evaluate(el=>({active:document.activeElement===el,outline:getComputedStyle(el).outlineStyle,shadow:getComputedStyle(el).boxShadow}));assert(focus.active&&(focus.outline!=='none'||focus.shadow!=='none'));
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  assert(httpErrors.every(e=>(e.path==='/favicon.ico'&&e.status===404)||(e.path==='/api/classify'&&e.status===422)));
  const result={status:'PASA',browser:browser.version(),base,real_browser:true,package_digest:health.package_digest,
   national_values:true,profiles_names_sizes:true,pagination_all_universe:true,detail_key_and_years:true,filters_and_clear:true,
   stale_response_ignored:true,network_error_clears_results:true,null_is_not_zero:true,html_escaped:true,
   audit_denominators:true,documentation_links:true,valid_csv:true,invalid_csv:true,draft_invalidated:true,approval_status:approved.status(),pdf_status:pdf.status(),stale_version_status:stale.status(),
   widths,contrasts,keyboard_focus:focus,page_errors:errors,console_errors:consoleErrors,http_errors:httpErrors,external_requests:external};
  fs.writeFileSync(OUT+'/qa_browser_resultados.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));await context.close();
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
