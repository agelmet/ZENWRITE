const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});
await p.goto('file:///home/claude/zw/og.html');await p.waitForTimeout(800);
await p.screenshot({path:'/home/claude/zw/site/assets/img/zenwrite-akadimaiki-ypostirixi-og.jpg',type:'jpeg',quality:86});await b.close();})();
