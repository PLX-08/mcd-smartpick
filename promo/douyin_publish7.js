// v7：从首页「继续编辑」进入未发布作品 → 点击发布（用户已授权）→ 验证结果
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = __dirname;
const PROFILE = 'C:\\Users\\plx20\\WorkBuddy\\2026-10-14-07-07-07\\_edge_profile';
const STATUS = path.join(OUT, '_publish_status.txt');
const SHOT = path.join(OUT, '_screen.png');

const log = (s) => { try { fs.appendFileSync(STATUS, s + '\n'); } catch (e) {} };
const bodyText = async (p) => { try { return (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, 900); } catch (e) { return ''; } };

(async () => {
  fs.writeFileSync(STATUS, 'V7 ' + new Date().toISOString() + '\n');
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
    let ok = false;
    try {
      const el = await page.$('text=继续编辑');
      if (el) { await el.click(); ok = true; log('CLICK 继续编辑'); }
    } catch (e) { log('ERR ' + e.message.slice(0, 60)); }
    if (!ok) { await page.goto('https://creator.douyin.com/creator-micro/content/post/image?enter_from=home_draft', { waitUntil: 'domcontentloaded' }); log('GOTO_DIRECT'); }
    await page.waitForTimeout(9000);
    log('EDIT_URL ' + page.url());
    try { await page.screenshot({ path: SHOT }); } catch (e) {}

    // 点击「发布」
    let clicked = false;
    const btns = await page.$$('button');
    for (const b of btns) {
      let t = '';
      try { t = ((await b.innerText()) || '').trim(); } catch (e) {}
      if (t === '发布') {
        try {
          await b.scrollIntoViewIfNeeded();
          await b.click({ force: true, timeout: 20000 });
          clicked = true;
          log('PUBLISH_CLICKED');
          break;
        } catch (e) { log('CLICK_ERR ' + e.message.slice(0, 100)); }
      }
    }
    if (!clicked) log('NOT_CLICKED');

    // 可能的二次确认弹窗
    await page.waitForTimeout(4000);
    const popBtns = await page.$$eval('button', (els) => els.map((e) => (e.innerText || '').trim()).filter((t) => t && t.length < 14));
    log('POP_BUTTONS ' + JSON.stringify(popBtns.slice(0, 30)));
    for (const t of ['确认发布', '确定', '确认']) {
      try {
        const el = await page.$(`text=${t}`);
        if (el) { await el.click({ force: true }); log('CONFIRM_CLICK ' + t); break; }
      } catch (e) {}
    }

    await page.waitForTimeout(15000);
    try { await page.screenshot({ path: SHOT }); } catch (e) {}
    log('AFTER_URL ' + page.url());
    log('AFTER_BODY ' + (await bodyText(page)));
  } catch (e) {
    log('ERROR ' + e.message.slice(0, 200));
  }
  await ctx.close();
  log('CLOSED');
})().catch((e) => log('FATAL ' + e.message));
