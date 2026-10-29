// Reuse the unchanged B5 integration oracle, redirect only its evidence output to B6.
const fs=require('fs');
const original=fs.readFileSync('analisis/reportes/b5/qa_browser.cjs','utf8');
const oldOutput="const OUT='analisis/reportes/b5';";
if(!original.includes(oldOutput))throw Error('B5 evidence output declaration changed; review the reuse wrapper');
new Function('require','process',original.replace(oldOutput,"const OUT='analisis/reportes/b6';"))(require,process);
