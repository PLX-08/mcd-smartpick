---
name: mcd-smartpick
description: 麦当劳目标导向智能点餐 Skill。当用户提到麦当劳、麦门、麦乐送、麦当劳优惠券、点餐、怎么点最划算、低卡/增肌/儿童营养怎么吃麦当劳时触发。基于麦当劳官方 MCP 拉取实时菜单与优惠券，用代码算出在预算与目标（省钱/增肌/低卡/解馋/儿童营养）下的最优组合，并讲成人话。
---

# 麦门聪明点 · McSmartPick

基于麦当劳官方 MCP（https://mcp.mcd.cn）的「目标导向智能点餐」技能。核心原则：**取数交给 MCP，算术交给代码，表达交给 Agent。**

## 三句话看懂

1. **你做什么**：用户说目标（省钱 / 增肌高蛋白 / 低卡控糖 / 解馋满足 / 儿童营养）+ 预算（元），你帮他算出"最划算"的一餐搭配。
2. **怎么做**：取数交给官方 MCP（`mcp.mcd.cn`）；**算术**交给纯函数 `scripts/mcsmart.py` 的 `smart_pick` / `group_pick`（不靠大模型口算，可复现可审计）；**表达**交给自然语言（讲清搭了什么、省了多少、为什么这么搭）。
3. **红线**：价格与优惠一律以 `calculate-price` 官方核算为准；`create-order`、`auto-bind-coupons`、`mall-create-order` 等**交易类工具绝不自动执行**，必须用户明确确认。

## 快速开始（无需 Token 也能跑）

```bash
# 1) 离线演示五目标（省钱 / 增肌 / 低卡 / 解馋 / 儿童营养），零依赖、零 Token
python scripts/mcsmart.py --demo

# 2) 指定目标与预算，看看引擎怎么算
python scripts/mcsmart.py --goal protein --budget 35

# 3) 真实麦当劳数据（需先 export MCD_MCP_TOKEN=... 领取免费 Token）
python scripts/mcsmart.py --live --goal save --budget 30 --city 宁波 --keyword 天一广场
```

网页交互演示见 `demo/index.html`（内置示例数据，浏览器打开即用，零依赖）。

## 何时使用

用户表达以下任意意图时启用：
- 想吃麦当劳但纠结"吃什么 / 怎么点最划算 / 营养够不够"
- 提到省钱、增肌、高蛋白、低卡、控糖、解馋、儿童营养等目标 + 预算
- 提到麦当劳优惠券、麦麦省、怎么组合最便宜

## 前置要求

- 用户需先在 https://open.mcd.cn/mcp 手机号登录并激活领取免费 MCP Token。
- Token 通过环境变量 `MCD_MCP_TOKEN` 提供（**绝不硬编码、绝不写入仓库**）。配置见 `mcp-config.example.json`。

## 工作流（严格按此顺序）

1. **澄清目标**（最多问一次）：目标（省钱/增肌/低卡/解馋/儿童营养）+ 预算（元）+ 必含餐品（可选）。
2. **取数（MCP）**：
   - `query-nearby-stores` → 拿到 `storeCode`
   - `query-meals(storeCode)` → 实时菜单
   - `list-nutrition-foods()` → 营养数据（**注意**：`query-meals` 不含营养字段，缺营养时按公开近似值兜底并在回复中说明）
   - `query-store-coupons(storeCode)` → 门店可用券
   - **门店券要按"券品"处理**：券对应独立券品编码，挂在普通商品上会被拒（`code 600012`）。
     正确做法是先用券品编码 + `couponId` 调一次 `calculate-price` 拿券后实付价，再把券品当候选参与组合。
3. **算术（代码，不要口算）**：调用 `scripts/mcsmart.py` 中的 `smart_pick(goal, budget, items, coupons)`：
   - 把 MCP 返回的菜单映射为内部 `Item`（code/name/category/price/tags/nutrition/crave），
     把券映射为 `Coupon`（id/name/kind/value/min_spend/scope）。
   - 运行 `python scripts/mcsmart.py --goal <goal> --budget <budget>` 获取离线基准，
     再用真实 MCP 数据复算：`python scripts/mcsmart.py --live --goal <goal> --budget <budget> --city <城市> --keyword <地标>`
     （`live_pick()` 已内置真实的门店/菜单/券品解析，无需手写适配层）。
   - **价格与优惠一律以 `calculate-price` 的官方核算为准**，本地结果仅用于组合推荐。
   - **拼单（组队点餐）**：当用户说"和朋友一起点 / 拼单"，把每个人的目标与预算组成 `diners` 列表，调用 `group_pick(diners, items, coupons)`（或 CLI `--diners "[{...},{...}]"`）。它先为每人算最优方案，再合并成一笔订单匹配更优的券，并按各自原始金额占比公平分摊券后总价；返回的 `total_savings_vs_alone` 如实表示拼单相对各自下单省了多少（可能为负）。拼单**不自动下单**。
4. **表达（讲人话）**：用中文告诉用户——搭了什么、原价多少、用了哪张券、省了多少、营养如何、为什么这么搭。
5. **下单（需确认）**：仅当用户明确说"下单/帮我点"时，才调用 `create-order`，并返回支付链接。**默认不自动下单。**

## 进阶可选链路（外送 / 积分商城 / 活动日历）

v1 主链路只用 `query-nearby-stores` / `query-meals` / `list-nutrition-foods` / `query-store-coupons` / `calculate-price`。以下能力为可选项，**默认不进入主链路**：

- `campaign-calendar`：只读，顺手展示当月营销活动；
- `delivery-query-addresses` / `delivery-query-stores`：只读，切换「外送」场景前查可配送门店；
- `query-my-account` / `mall-points-products` / `mall-product-detail`：只读，查积分与兑换；
- 交易类 `mall-create-order`（积分兑换下单）**需用户显式确认**，绝不自动执行。

完整调用示例见 `references/tools.md` 的「进阶可选链路」一节。接入时务必保持主链路不变、交易类工具需确认。

## 设计红线

- 交易类工具（`create-order`、`auto-bind-coupons`、`mall-create-order` 等）必须用户显式确认，默认只读与规划。
- 不泄露 Token / 账号 / 他人信息；配置文件只使用环境变量占位符。
- 餐品信息、价格、供应状态以麦当劳官方实时结果为准；输出不构成医疗/营养专业建议。

## 离线演示（无需 Token）

- `python scripts/mcsmart.py --demo`：CLI 演示五个目标（含儿童营养）。
- 打开 `demo/index.html`：网页交互演示（内置示例数据，零依赖、零 Token）。
- 离线样例输出见 `demo/sample_run.md`；引擎测试见 `tests/test_engine.py`。
- 真实回包解析回归：`python tests/test_live_adapt.py`（零依赖、无需 Token）。

## 常见问题（FAQ）

- **Q：没有 Token 能演示吗？** 可以。`python scripts/mcsmart.py --demo` 与打开 `demo/index.html` 都完全离线，内置公开近似示例数据，便于直接体验与拿 Star。
- **Q：优惠券会叠加使用吗？** 默认不叠加。引擎 `best_coupon` 在满足条件的券里只挑**折扣力度最大的一张**（金额或百分比取更优者），符合"一次只用一张最优券"的常规。
- **Q：能和朋友拼单吗？** 能。把每个人的目标与预算组成 `diners` 列表，调用 `group_pick`（或 CLI `--diners "[{...},{...}]"`）：先各自算最优方案，再合并成一笔订单匹配更优券，并按各自原价占比公平分摊券后总价；`total_savings_vs_alone` 如实给出拼单相对各自下单省（或亏）多少。
- **Q：营养数据准吗？** `query-meals` 不含营养字段，live 模式在缺数据时用**公开近似营养值兜底**，并在回复中说明；正式营养以官方 `list-nutrition-foods` / 麦当劳官方为准。本工具输出不构成医疗或营养专业建议。
- **Q：定制空间大吗？** 支持 `required`（必含项）、`exclude`（忌口排除，如 `辣`/`香菜`）、`kcal-cap`（自定义热量上限，对所有目标生效）。

## 参考

- MCP 工具清单与注意事项：`references/tools.md`
- MCP 调用流程与业务价值：`MCP_INTEGRATION.md`
- 真实调用记录（含官方 traceId）：`evidence-real.md`
