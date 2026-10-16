// 检查抖音草稿箱里是否还留着刚填的图文
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = __dirname;
const PROFILE = 'C:\\Users\\plx20\\WorkBuddy\\2026-10-14-07-07-07\\_edge_profile';
const STATUS = path.join(OUT, '_check_status.txt');

const log = (s) => fs.appendFileSync(STATUS, s + '\n');
const bodyText = async (p) => { try { return (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, 1200); } catch (e) { return ''; } };

(async () => {
  fs.writeFileSync(STATUS, 'CHECK ' + new Date().toISOString() + '\n');
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
    await page.goto('https://creator.douyin.com/creator-micro/content/manage', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(7000);
    log('URL ' + page.url());
    log('BODY_MANAGE ' + (await bodyText(page)));

    // 尝试切到草稿 tab
    try {
      const el = await page.$('text=草稿');
      if (el) { await el.click(); log('CLICK 草稿'); await page.waitForTimeout(5000); log('BODY_DRAFT ' + (await bodyText(page))); }
      else log('NO_DRAFT_TAB');
    } catch (e) { log('DRAFT_ERR ' + e.message.slice(0, 80)); }
  } catch (e) {
    log('ERROR ' + e.message.slice(0, 200));
  }
  await ctx.close();
  log('CLOSED');
})().catch((e) => log('FATAL ' + e.message));
