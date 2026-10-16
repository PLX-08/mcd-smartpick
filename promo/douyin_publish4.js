// v4：重新填好图文内容 → 保持页面 → 轮询 _do_publish.flag，出现后才点「发布」
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = __dirname;
const PROFILE = 'C:\\Users\\plx20\\WorkBuddy\\2026-10-14-07-07-07\\_edge_profile';
const STATUS = path.join(OUT, '_publish_status.txt');
const SHOT = path.join(OUT, '_screen.png');
const FLAG = path.join(OUT, '_do_publish.flag');
const POSTER = path.join(OUT, 'douyin_poster_1080x1920.png');

const TITLE = '我用 AI 做了个「麦当劳最优点餐器」';
const DESC = [
  '每次点麦当劳都纠结又心疼钱？我干脆写了个开源项目：麦门聪明点 McSmartPick。',
  '',
  '你说一句「我要增肌，预算 35 块」，它直接连上麦当劳官方接口，自动算出预算内蛋白质最多的组合，原价多少、券后多少、省多少、营养多少一次讲清。',
  '',
  '不是 AI「感觉上挺便宜」，而是真用代码把每种搭配都跑一遍，再用官方接口核算价格。',
  '',
  '它正在参加麦当劳 1024 程序员节大赛，榜单按 GitHub Star 数排名。觉得有用的话，去 GitHub 搜 McSmartPick 点个 Star 就能帮它冲榜。',
  '',
  '开源、免费、不收集任何个人信息。',
].join('\n');
const TAGS = ['麦当劳', 'AI工具', '开源', 'GitHub', '省钱攻略'];

const log = (s) => fs.appendFileSync(STATUS, s + '\n');
const shot = async (p) => { try { await p.screenshot({ path: SHOT }); } catch (e) {} };
const bodyText = async (p) => { try { return (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, 800); } catch (e) { return ''; } };
const clickText = async (p, txt) => {
  try {
    const el = await p.$(`text=${txt}`);
    if (el) { await el.click(); log('CLICK ' + txt); return true; }
    return false;
  } catch (e) { return false; }
};

(async () => {
  fs.writeFileSync(STATUS, 'V4 START ' + new Date().toISOString() + '\n');
  if (fs.existsSync(FLAG)) fs.unlinkSync(FLAG);
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
    await page.goto('https://creator.douyin.com/creator-micro/content/upload', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(6000);
    await clickText(page, '发布图文');
    await page.waitForTimeout(2500);
    await clickText(page, '上传图文');
    await page.waitForTimeout(4000);

    const inputs = await page.$$('input[type=file]');
    let chosen = null;
    for (const inp of inputs) {
      const acc = (await inp.getAttribute('accept')) || '';
      if (/image/i.test(acc)) chosen = inp;
    }
    if (!chosen && inputs.length) chosen = inputs[inputs.length - 1];
    if (chosen) { await chosen.setInputFiles(POSTER); log('FILE_SET_OK'); }
    await page.waitForTimeout(10000);

    const titleEl = await page.$('input[placeholder*="标题"]');
    if (titleEl) { await titleEl.click(); await titleEl.fill(TITLE); log('TITLE_FILLED'); }
    else log('NO_TITLE');

    const descEl = await page.$('[contenteditable="true"]');
    if (descEl) {
      await descEl.click();
      await page.keyboard.press('Control+A');
      await page.keyboard.press('Delete');
      await page.keyboard.type(DESC, { delay: 8 });
      await page.waitForTimeout(1000);
      for (const tg of TAGS) {
        await page.keyboard.type('#', { delay: 30 });
        await page.waitForTimeout(1300);
        await page.keyboard.type(tg, { delay: 55 });
        await page.waitForTimeout(1900);
        await page.keyboard.press('Enter');
        await page.waitForTimeout(700);
        await page.keyboard.type(' ', { delay: 20 });
      }
      log('DESC_AND_TAGS_DONE');
    } else log('NO_DESC');

    await page.waitForTimeout(2500);
    await shot(page);
    log('BODY_READY ' + (await bodyText(page)));
    log('WAITING_FOR_CONFIRM');

    // 轮询等待发布指令（最多 20 分钟）
    let published = false;
    for (let i = 0; i < 240; i++) {
      await page.waitForTimeout(5000);
      if (fs.existsSync(FLAG)) {
        log('FLAG_FOUND');
        let clicked = false;
        try {
          const btn = await page.$('button:text-is("发布")');
          if (btn) { await btn.click(); clicked = true; log('PUBLISH_CLICKED'); }
        } catch (e) { log('CLICK_ERR ' + e.message.slice(0, 80)); }
        if (!clicked) {
          try {
            const btns = await page.$$('button');
            for (const b of btns) {
              const t = ((await b.innerText().catch(() => '')) || '').trim();
              if (t === '发布') { await b.click(); clicked = true; log('PUBLISH_CLICKED_FALLBACK'); break; }
            }
          } catch (e) {}
        }
        if (!clicked) log('PUBLISH_BUTTON_NOT_FOUND');
        await page.waitForTimeout(8000);
        await shot(page);
        log('AFTER_PUBLISH_URL ' + page.url());
        log('AFTER_PUBLISH_BODY ' + (await bodyText(page)));
        published = true;
        break;
      }
    }
    if (!published) log('TIMEOUT_NO_FLAG');
  } catch (e) {
    log('ERROR ' + e.message.slice(0, 200));
  }
  await shot(page);
  await ctx.close();
  log('CLOSED');
})().catch((e) => log('FATAL ' + e.message));
