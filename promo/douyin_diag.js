// v6：从首页「继续编辑」进入未发布作品，诊断发布按钮与必填项（不点发布）
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = __dirname;
const PROFILE = 'C:\\Users\\plx20\\WorkBuddy\\2026-10-14-07-07-07\\_edge_profile';
const STATUS = path.join(OUT, '_diag_status.txt');
const SHOT = path.join(OUT, '_screen.png');

const log = (s) => { try { fs.appendFileSync(STATUS, s + '\n'); } catch (e) {} };
const bodyText = async (p) => { try { return (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, 900); } catch (e) { return ''; } };

(async () => {
  fs.writeFileSync(STATUS, 'V6 ' + new Date().toISOString() + '\n');
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    executablePath: EDGE,
    headless: false,
    args: ['--start-maximized', '--disable-blink-features=AutomationControlled'],
    viewport: null,
    ignoreDefaultArgs: ['--enable-automation'],
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  page.setDefaultTimeout(30000);
  try {
    await page.goto('https://creator.douyin.com/creator-micro/home', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(7000);
    // 继续编辑
    let clicked = false;
    try {
      const el = await page.$('text=继续编辑');
      if (el) { await el.click(); clicked = true; log('CLICK 继续编辑'); }
    } catch (e) { log('CONTINUE_ERR ' + e.message.slice(0, 80)); }
    if (!clicked) {
      // 备选：直接进上传页
      await page.goto('https://creator.douyin.com/creator-micro/content/upload', { waitUntil: 'domcontentloaded' });
      log('GOTO_UPLOAD');
    }
    await page.waitForTimeout(9000);
    try { await page.screenshot({ path: SHOT }); } catch (e) {}
    log('URL ' + page.url());
    log('BODY ' + (await bodyText(page)));

    const btnInfo = await page.$$eval('button', (els) =>
      els.map((e) => ({ t: (e.innerText || '').trim().replace(/\n/g, '/').slice(0, 14), d: e.disabled, c: (e.className || '').slice(0, 40) }))
    );
    log('BTN_INFO ' + JSON.stringify(btnInfo));

    // 声明区域附近的元素
    const declInfo = await page.$$eval('*', (els) =>
      els.filter((e) => /自主声明|声明/.test((e.innerText || '')) && (e.innerText || '').length < 60)
         .map((e) => `${e.tagName}|${(e.className || '').toString().slice(0, 50)}|${(e.innerText || '').replace(/\n/g, '/').slice(0, 40)}`)
         .slice(0, 15)
    );
    log('DECL_INFO ' + JSON.stringify(declInfo));
  } catch (e) {
    log('ERROR ' + e.message.slice(0, 200));
  }
  await ctx.close();
  log('CLOSED');
})().catch((e) => log('FATAL ' + e.message));
