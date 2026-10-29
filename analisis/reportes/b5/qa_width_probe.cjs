const fs=require('fs'),path=require('path');
const {chromium}=require(path.join(process.env.LOCALAPPDATA,'ms-playwright-go','1.57.0','package'));
(async()=>{
 const browser=await chromium.launch({executablePath:path.join(process.env.ProgramFiles,'Google','Chrome','Application','chrome.exe'),headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:1080}});
  await page.goto(process.argv[2],{waitUntil:'networkidle'});
  await page.waitForFunction(()=>document.querySelectorAll('#nationalRows tr').length===6);
  const result=await page.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth,nodes:[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().width&&el.getBoundingClientRect().right>innerWidth+1).map(el=>({tag:el.tagName,id:el.id,class:typeof el.className==='string'?el.className:'svg',x:el.getBoundingClientRect().x,width:el.getBoundingClientRect().width,scroll:el.scrollWidth,display:getComputedStyle(el).display,minWidth:getComputedStyle(el).minWidth,text:el.textContent.trim().slice(0,50)})).slice(0,35)}));
  fs.writeFileSync('analisis/reportes/b5/qa_width_probe.json',JSON.stringify(result,null,2)+'\n');
  await page.screenshot({path:'analisis/reportes/b5/qa_width_probe.png',fullPage:true});console.log(JSON.stringify(result,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
