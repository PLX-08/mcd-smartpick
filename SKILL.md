---
name: mcd-smartpick
description: 麦当劳目标导向智能点餐 Skill。当用户提到麦当劳、麦门、麦乐送、麦当劳优惠券、点餐、怎么点最划算、低卡/增肌怎么吃麦当劳时触发。基于麦当劳官方 MCP 拉取实时菜单与优惠券，用代码算出在预算与目标（省钱/增肌/低卡/解馋）下的最优组合，并讲成人话。
---

# 麦门聪明点 · McSmartPick

基于麦当劳官方 MCP（https://mcp.mcd.cn）的「目标导向智能点餐」技能。核心原则：**取数交给 MCP，算术交给代码，表达交给 Agent。**

## 何时使用

用户表达以下任意意图时启用：
- 想吃麦当劳但纠结"吃什么 / 怎么点最划算 / 营养够不够"
- 提到省钱、增肌、高蛋白、低卡、控糖、解馋等目标 + 预算
- 提到麦当劳优惠券、麦麦省、怎么组合最便宜

## 前置要求

- 用户需先在 https://open.mcd.cn/mcp 手机号登录并激活领取免费 MCP Token。
- Token 通过环境变量 `MCD_MCP_TOKEN` 提供（**绝不硬编码、绝不写入仓库**）。配置见 `mcp-config.example.json`。

## 工作流（严格按此顺序）

1. **澄清目标**（最多问一次）：目标（省钱/增肌/低卡/解馋）+ 预算（元）+ 必含餐品（可选）。
2. **取数（MCP）**：
   - `query-nearby-stores` → 拿到 `storeCode`
   - `query-meals(storeCode)` → 实时菜单
   - `list-nutrition-foods()` → 营养数据
   - `query-store-coupons(storeCode)` → 门店可用券
3. **算术（代码，不要口算）**：调用 `scripts/mcsmart.py` 中的 `smart_pick(goal, budget, items, coupons)`：
   - 把 MCP 返回的菜单映射为内部 `Item`（code/name/category/price/tags/nutrition/crave），
     把券映射为 `Coupon`（id/name/kind/value/min_spend/scope）。
   - 运行 `python scripts/mcsmart.py --goal <goal> --budget <budget>` 获取离线基准，
     再用真实 MCP 数据复算（live 模式：`python scripts/mcsmart.py --live --goal <goal> --budget <budget>`）。
   - **价格与优惠一律以 `calculate-price` 的官方核算为准**，本地结果仅用于组合推荐。
4. **表达（讲人话）**：用中文告诉用户——搭了什么、原价多少、用了哪张券、省了多少、营养如何、为什么这么搭。
5. **下单（需确认）**：仅当用户明确说"下单/帮我点"时，才调用 `create-order`，并返回支付链接。**默认不自动下单。**

## 设计红线

- 交易类工具（`create-order`、`auto-bind-coupons`、`mall-create-order` 等）必须用户显式确认，默认只读与规划。
- 不泄露 Token / 账号 / 他人信息；配置文件只使用环境变量占位符。
- 餐品信息、价格、供应状态以麦当劳官方实时结果为准；输出不构成医疗/营养专业建议。

## 离线演示（无需 Token）

- `python scripts/mcsmart.py --demo`：CLI 演示四个目标。
- 打开 `demo/index.html`：网页交互演示（内置示例数据，零依赖、零 Token）。
- 离线样例输出见 `demo/sample_run.md`；引擎测试见 `tests/test_engine.py`。

## 参考

- MCP 工具清单与注意事项：`references/tools.md`
- MCP 调用流程与业务价值：`MCP_INTEGRATION.md`
