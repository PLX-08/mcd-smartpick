// v8：验证作品是否已发布
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const PROFILE = 'C:\\Users\\plx20\\WorkBuddy\\2026-10-14-07-07-07\\_edge_profile';
const STATUS = path.join(__dirname, '_verify_status.txt');
const SHOT = path.join(__dirname, '_screen.png');

const log = (s) => { try { fs.appendFileSync(STATUS, s + '\n'); } catch (e) {} };
const bodyText = async (p) => { try { return (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, 1000); } catch (e) { return ''; } };

(async () => {
  fs.writeFileSync(STATUS, 'V8 ' + new Date().toISOString() + '\n');
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
    await page.waitForTimeout(8000);
    try { await page.screenshot({ path: SHOT }); } catch (e) {}
    let b = await bodyText(page);
    log('HOME_HAS_UNPUBLISHED=' + /未发布的作品|继续编辑/.test(b));
    log('HOME_BODY ' + b.slice(0, 500));

    await page.goto('https://creator.douyin.com/creator-micro/content/manage', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(8000);
    try { await page.screenshot({ path: SHOT }); } catch (e) {}
    b = await bodyText(page);
    log('MANAGE_BODY ' + b);
    log('HAS_TITLE=' + /麦当劳最优点餐器/.test(b));
    log('HAS_TODAY=' + /刚刚|分钟前|2026年10月15日/.test(b));
  } catch (e) {
    log('ERROR ' + e.message.slice(0, 150));
  }
  await ctx.close();
  log('CLOSED');
})().catch((e) => log('FATAL ' + e.message));
