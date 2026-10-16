// v2：先点「发布图文」→ 再点「上传图文」→ 上传海报 → 填标题正文话题（不点发布）
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const OUT = __dirname;
const PROFILE = 'C:\\Users\\plx20\\WorkBuddy\\2026-10-14-07-07-07\\_edge_profile';
const STATUS = path.join(OUT, '_publish_status.txt');
const SHOT = path.join(OUT, '_screen.png');
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
const TAGS = ['麦当劳', 'AI工具', '开源', 'GitHub', '省钱攻略', '程序员', '学生党'];

const log = (s) => fs.appendFileSync(STATUS, s + '\n');
const shot = async (p) => { try { await p.screenshot({ path: SHOT, fullPage: false }); } catch (e) {} };
const bodyText = async (p) => { try { return (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, 700); } catch (e) { return ''; } };

(async () => {
  fs.writeFileSync(STATUS, 'V2 START ' + new Date().toISOString() + '\n');
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
    log('URL ' + page.url());
    await shot(page);

    // 1) 发布图文 -> 上传图文
    const clickText = async (txt) => {
      try {
        const el = await page.$(`text=${txt}`);
        if (el) { await el.click(); log('CLICK ' + txt); return true; }
        log('NOT_FOUND ' + txt);
        return false;
      } catch (e) { log('CLICK_ERR ' + txt + ' ' + e.message.slice(0, 80)); return false; }
    };
    await clickText('发布图文');
    await page.waitForTimeout(2500);
    await shot(page);
    await clickText('上传图文');
    await page.waitForTimeout(4000);
    await shot(page);
    log('BODY1 ' + (await bodyText(page)));

    // 2) 选正确的 file input（accept 含 image 优先）
    const inputs = await page.$$('input[type=file]');
    log('FILE_INPUT_COUNT ' + inputs.length);
    let chosen = null;
    for (let i = 0; i < inputs.length; i++) {
      const acc = (await inputs[i].getAttribute('accept')) || '';
      log(`input${i} accept=${acc}`);
      if (/image/i.test(acc)) chosen = inputs[i];
    }
    if (!chosen && inputs.length) chosen = inputs[inputs.length - 1];
    if (chosen) {
      await chosen.setInputFiles(POSTER);
      log('FILE_SET_OK');
    } else {
      log('FATAL_NO_FILE_INPUT');
    }

    // 3) 等上传完成：等待出现标题输入框
    let titleEl = null;
    for (const s of ['input[placeholder*="标题"]', 'input[placeholder*="作品标题"]', 'input[placeholder*="填写"]']) {
      try {
        await page.waitForSelector(s, { timeout: 25000 });
        titleEl = await page.$(s);
        if (titleEl) { log('TITLE_INPUT ' + s); break; }
      } catch (e) {}
    }
    await page.waitForTimeout(2000);
    await shot(page);
    log('BODY2 ' + (await bodyText(page)));

    const fields = await page.$$eval('input, textarea, [contenteditable="true"]', (els) =>
      els.map((e, i) => `${i}|${e.tagName}|ph=${e.getAttribute('placeholder') || ''}`).slice(0, 30)
    );
    log('FIELDS:\n' + fields.join('\n'));

    // 4) 填标题
    if (titleEl) {
      try { await titleEl.click(); await titleEl.fill(TITLE); log('TITLE_FILLED'); } catch (e) { log('TITLE_ERR ' + e.message.slice(0, 80)); }
    } else {
      log('NO_TITLE_INPUT');
    }

    // 5) 正文
    let descOk = false;
    for (const s of ['[contenteditable="true"]', 'textarea', 'div[contenteditable="true"]']) {
      try {
        const el = await page.$(s);
        if (el) {
          await el.click();
          await page.keyboard.type(DESC, { delay: 10 });
          descOk = true; log('DESC_FILLED ' + s); break;
        }
      } catch (e) {}
    }
    await page.waitForTimeout(1200);

    // 6) 话题
    if (descOk) {
      for (const tg of TAGS) {
        try {
          await page.keyboard.type('#' + tg, { delay: 35 });
          await page.waitForTimeout(1600);
          await page.keyboard.press('Enter');
          await page.waitForTimeout(800);
          await page.keyboard.type(' ', { delay: 15 });
        } catch (e) {}
      }
      log('TAGS_DONE');
    }

    await page.waitForTimeout(2500);
    await shot(page);
    const btns = await page.$$eval('button', (els) => els.map((e) => (e.innerText || '').trim()).filter((t) => t && t.length < 14).slice(0, 40));
    log('BUTTONS ' + JSON.stringify(btns));
    log('BODY3 ' + (await bodyText(page)));
    log('READY_FOR_CONFIRM');
  } catch (e) {
    log('ERROR ' + e.message.slice(0, 200));
  }
  await shot(page);
  await ctx.close();
  log('CLOSED');
})().catch((e) => log('FATAL ' + e.message));
