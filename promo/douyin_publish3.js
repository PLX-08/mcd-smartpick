// v3：清理正文尾部乱码话题 + 重新写入正文与已验证可用的话题（不点发布）
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
const TAGS = ['麦当劳', 'AI工具', '开源', 'GitHub', '省钱攻略'];

const log = (s) => fs.appendFileSync(STATUS, s + '\n');
const shot = async (p) => { try { await p.screenshot({ path: SHOT }); } catch (e) {} };
const bodyText = async (p) => { try { return (await p.innerText('body')).replace(/\n+/g, ' | ').slice(0, 800); } catch (e) { return ''; } };
const clickText = async (p, txt) => {
  try {
    const el = await p.$(`text=${txt}`);
    if (el) { await el.click(); log('CLICK ' + txt); return true; }
    log('NOT_FOUND ' + txt);
    return false;
  } catch (e) { log('CLICK_ERR ' + txt + ' ' + e.message.slice(0, 60)); return false; }
};

(async () => {
  fs.writeFileSync(STATUS, 'V3 START ' + new Date().toISOString() + '\n');
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
    let b = await bodyText(page);
    log('BODY0 ' + b);

    // 若当前不是图文编辑态，走一次入口点击
    if (!/已添加\d+张图片|作品描述/.test(b)) {
      await clickText(page, '发布图文');
      await page.waitForTimeout(2500);
      await clickText(page, '上传图文');
      await page.waitForTimeout(4000);
      b = await bodyText(page);
      log('BODY1 ' + b);
    }

    // 若图片没恢复，重新上传
    if (!/已添加\d+张图片/.test(b)) {
      const inputs = await page.$$('input[type=file]');
      let chosen = null;
      for (const inp of inputs) {
        const acc = (await inp.getAttribute('accept')) || '';
        if (/image/i.test(acc)) chosen = inp;
      }
      if (!chosen && inputs.length) chosen = inputs[inputs.length - 1];
      if (chosen) { await chosen.setInputFiles(POSTER); log('FILE_SET_OK'); } else { log('NO_FILE_INPUT'); }
      await page.waitForTimeout(9000);
    } else {
      log('IMAGE_ALREADY_THERE');
    }
    b = await bodyText(page);
    log('BODY2 ' + b);

    // 标题
    const titleEl = await page.$('input[placeholder*="标题"]');
    if (titleEl) {
      const cur = await titleEl.inputValue().catch(() => '');
      log('TITLE_CURRENT=' + cur);
      if (!cur || cur.trim() === '') {
        await titleEl.click();
        await titleEl.fill(TITLE);
        log('TITLE_FILLED');
      }
    }

    // 正文：整段清空重写，去掉乱码话题
    const descEl = await page.$('[contenteditable="true"]');
    if (descEl) {
      await descEl.click();
      await page.waitForTimeout(500);
      await page.keyboard.press('Control+A');
      await page.waitForTimeout(300);
      await page.keyboard.press('Delete');
      await page.waitForTimeout(500);
      await page.keyboard.type(DESC, { delay: 8 });
      await page.waitForTimeout(1000);
      log('DESC_REWRITTEN');

      for (const tg of TAGS) {
        await page.keyboard.type('#', { delay: 30 });
        await page.waitForTimeout(1300);
        await page.keyboard.type(tg, { delay: 55 });
        await page.waitForTimeout(1900);
        await page.keyboard.press('Enter');
        await page.waitForTimeout(700);
        await page.keyboard.type(' ', { delay: 20 });
      }
      log('TAGS_DONE');
    } else {
      log('NO_DESC_ELEMENT');
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
