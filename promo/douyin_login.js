// 打开抖音创作者服务平台，等待扫码登录；每 3 秒刷新一次截图供用户扫码
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = path.join(__dirname);
const PROFILE = 'C:\\Users\\plx20\\WorkBuddy\\2026-10-14-07-07-07\\_edge_profile';
const STATUS = path.join(OUT, '_login_status.txt');
const SHOT = path.join(OUT, '_screen.png');

const log = (s) => fs.appendFileSync(STATUS, s + '\n');

(async () => {
  fs.writeFileSync(STATUS, 'START ' + new Date().toISOString() + '\n');
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    executablePath: EDGE,
    headless: false,
    args: ['--start-maximized', '--disable-blink-features=AutomationControlled'],
    viewport: null,
    ignoreDefaultArgs: ['--enable-automation'],
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  try {
    await page.goto('https://creator.douyin.com/creator-micro/content/upload', {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    });
  } catch (e) {
    log('GOTO_ERR ' + e.message);
  }
  log('URL0 ' + page.url());

  let done = false;
  for (let i = 0; i < 110; i++) {
    await page.waitForTimeout(3000);
    try {
      await page.screenshot({ path: SHOT });
    } catch (e) {}
    let url = '';
    try { url = page.url(); } catch (e) {}
    let hasFile = false;
    try { hasFile = !!(await page.$('input[type=file]')); } catch (e) {}
    let bodyText = '';
    try { bodyText = (await page.innerText('body')).slice(0, 300); } catch (e) {}
    log(`tick=${i} url=${url} fileInput=${hasFile}`);
    if (hasFile || /upload|发布作品|发布视频/i.test(bodyText)) {
      log('LOGGED_IN');
      done = true;
      break;
    }
  }
  if (!done) log('TIMEOUT_NOT_LOGGED_IN');
  try { await page.screenshot({ path: SHOT }); } catch (e) {}
  await ctx.close();
  log('CLOSED');
})().catch((e) => {
  log('FATAL ' + e.message);
});
