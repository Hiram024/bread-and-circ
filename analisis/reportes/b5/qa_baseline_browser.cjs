const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const {chromium} = require(path.join(process.env.LOCALAPPDATA,'ms-playwright-go','1.57.0','package'));
(async()=>{
 const browser=await chromium.launch({executablePath:path.join(process.env.ProgramFiles,'Google','Chrome','Application','chrome.exe'),headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1080}}), errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.argv[2],{waitUntil:'networkidle'});
  await page.waitForFunction(()=>document.querySelectorAll('#draftProfile option').length===4);
  const screens={};
  for(const tab of ['resumen','perfiles','explorar','auditoria']){
   await page.locator(`#nav button[data-tab="${tab}"]`).click();
   if(tab==='explorar') await page.waitForFunction(()=>document.querySelectorAll('#obsRows tr').length===100);
   if(tab==='auditoria') await page.waitForFunction(()=>document.querySelectorAll('#auditCards .stat').length>0);
   screens[tab]=await page.locator(`#tab-${tab}`).innerText();
  }
  await page.locator('#nav button[data-tab="explorar"]').click();
  await page.waitForFunction(()=>document.querySelectorAll('#obsRows tr').length===100);
  await page.screenshot({path:'analisis/reportes/b5/qa_baseline_browser.png',fullPage:true});
  assert.deepEqual(errors,[]);
  fs.writeFileSync('analisis/reportes/b5/qa_baseline_browser.json',JSON.stringify({browser:browser.version(),viewport:{width:1440,height:1080},screens,errors},null,2)+'\n');
  console.log(JSON.stringify({browser:browser.version(),screens:Object.keys(screens),errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
