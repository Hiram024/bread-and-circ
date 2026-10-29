const fs=require('fs'),path=require('path'),os=require('os');
const {chromium}=require(path.join(process.env.LOCALAPPDATA,'ms-playwright-go','1.57.0','package'));
(async()=>{
 const results=[];
 for(const factor of [1,2]){
  const profile=fs.mkdtempSync(path.join(os.tmpdir(),'qa-b6-zoom-profile-'));
  fs.mkdirSync(path.join(profile,'Default'));
  const level=Math.log(factor)/Math.log(1.2);
  fs.writeFileSync(path.join(profile,'Default','Preferences'),JSON.stringify({partition:{default_zoom_level:{x:level}}}));
  const context=await chromium.launchPersistentContext(profile,{executablePath:path.join(process.env.ProgramFiles,'Google','Chrome','Application','chrome.exe'),headless:false,viewport:null,args:['--window-size=1440,1050','--window-position=30,30']});
  try{
   const page=context.pages()[0]||await context.newPage();
   await page.goto('http://127.0.0.1:61286/',{waitUntil:'networkidle'});
   await page.waitForFunction(()=>document.querySelectorAll('#nationalRows tr').length===6);
   results.push({factor,level,metrics:await page.evaluate(()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,outerWidth,outerHeight,visualScale:visualViewport.scale,cssZoom:getComputedStyle(document.documentElement).zoom}))});
  }finally{await context.close();}
 }
 fs.writeFileSync('analisis/reportes/b6/qa_zoom_probe.json',JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(results,null,2));
})().catch(error=>{console.error(error);process.exit(1)});
