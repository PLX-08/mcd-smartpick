// 在抖音创作者平台填写图文作品（不点发布，停在待发布状态等用户确认）
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
  '你说一句「我要增肌，预算 35 块」，它直接连上麦当劳官方接口，自动算出预算内蛋白质最多的组合，告诉你原价多少、券后多少、省多少、营养多少。',
  '',
  '不是 AI「感觉上挺便宜」，而是真的用代码把每种搭配都跑一遍，再用官方接口核算价格，算错是不可能算错的。',
  '',
  '现在它正在参加麦当劳 1024 程序员节大赛，榜单按 GitHub Star 数排名。觉得有用的话，去 GitHub 搜 McSmartPick 点个 Star，就能帮它冲上榜单。',
  '',
  '开源、免费、不收集任何个人信息。',
].join('\n');
const TAGS = ['麦当劳', 'AI工具', '开源', 'GitHub', '省钱攻略', '程序员', '学生党'];

const log = (s) => { fs.appendFileSync(STATUS, s + '\n'); };
const shot = async (p) => { try { await p.screenshot({ path: SHOT }); } catch (e) {} };

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
  page.setDefaultTimeout(30000);

  try {
    await page.goto('https://creator.douyin.com/creator-micro/content/upload', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(5000);
    log('URL ' + page.url());
    await shot(page);

    // 1) 切到「发布图文」
    for (const t of ['发布图文', '图文', '发图文']) {
      try {
        const el = await page.$(`text=${t}`);
        if (el) { await el.click(); log('CLICK_TAB ' + t); break; }
      } catch (e) {}
    }
    await page.waitForTimeout(4000);
    await shot(page);

    // 2) 上传图片
    let fileInput = await page.$('input[type=file]');
    if (!fileInput) {
      log('NO_FILE_INPUT_TRY_WAIT');
      try { await page.waitForSelector('input[type=file]', { timeout: 20000 }); fileInput = await page.$('input[type=file]'); } catch (e) {}
    }
    if (fileInput) {
      await fileInput.setInputFiles(POSTER);
      log('FILE_SET');
    } else {
      log('FATAL_NO_FILE_INPUT');
    }
    await page.waitForTimeout(9000);
    await shot(page);
    log('URL_AFTER_UPLOAD ' + page.url());

    // 3) 列出可输入区域，便于定位标题/正文
    const fields = await page.$$eval('input, textarea, [contenteditable="true"]', (els) =>
      els.map((e, i) => `${i}|${e.tagName}|ph=${e.getAttribute('placeholder') || ''}|cls=${(e.className || '').toString().slice(0, 60)}`).slice(0, 30)
    );
    log('FIELDS:\n' + fields.join('\n'));

    // 4) 填标题
    let titleOk = false;
    const titleSels = [
      'input[placeholder*="标题"]',
      'input[placeholder*="作品标题"]',
      'input[placeholder*="填写"]',
      'textarea[placeholder*="标题"]',
    ];
    for (const s of titleSels) {
      try {
        const el = await page.$(s);
        if (el) { await el.click(); await el.fill(TITLE); titleOk = true; log('TITLE_OK ' + s); break; }
      } catch (e) {}
    }
    // 兜底：第一个可见 input
    if (!titleOk) {
      try {
        const el = await page.$('input:visible');
        if (el) { await el.click(); await el.fill(TITLE); titleOk = true; log('TITLE_FALLBACK'); }
      } catch (e) {}
    }

    // 5) 填正文
    let descOk = false;
    const descSels = [
      '[contenteditable="true"]',
      'textarea[placeholder*="简介"]',
      'textarea[placeholder*="描述"]',
      'div[contenteditable="true"]',
    ];
    for (const s of descSels) {
      try {
        const el = await page.$(s);
        if (el) {
          await el.click();
          await page.keyboard.type(DESC, { delay: 12 });
          descOk = true;
          log('DESC_OK ' + s);
          break;
        }
      } catch (e) {}
    }
    await page.waitForTimeout(1500);

    // 6) 加话题标签
    if (descOk) {
      for (const tg of TAGS) {
        try {
          await page.keyboard.type('#' + tg, { delay: 40 });
          await page.waitForTimeout(1800);
          await page.keyboard.press('Enter');
          await page.waitForTimeout(900);
          await page.keyboard.type(' ', { delay: 20 });
        } catch (e) {}
      }
      log('TAGS_DONE');
    }

    await page.waitForTimeout(3000);
    await shot(page);

    // 7) 找发布按钮（不点）
    const btns = await page.$$eval('button, [class*="button"]', (els) =>
      els.map((e) => (e.innerText || '').trim()).filter((t) => t && t.length < 12).slice(0, 40)
    );
    log('BUTTONS: ' + JSON.stringify(btns));
    let body = '';
    try { body = (await page.innerText('body')).replace(/\n+/g, ' | ').slice(0, 600); } catch (e) {}
    log('BODY: ' + body);
    log('READY_FOR_CONFIRM');
  } catch (e) {
    log('ERROR ' + e.message);
  }
  await shot(page);
  await ctx.close();
  log('CLOSED');
})().catch((e) => log('FATAL ' + e.message));
