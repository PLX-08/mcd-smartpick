# MCP 集成说明（MCP_INTEGRATION）

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| 提供方 | 麦当劳中国（非官方产品，仅基于官方开放能力开发） |
| 官方仓库 | `M-China/mcd-mcp-server` |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP（JSON-RPC 2.0 over HTTP） |
| 鉴权方式 | `Authorization: Bearer <MCP Token>`（Token 来自 https://open.mcd.cn/mcp，免费，环境变量占位，**不硬编码**） |
| 限流 | 600 次 / 分钟（超频返回 429） |

> 配置示例见 `mcp-config.example.json`。完整 30+ 工具清单见 `references/tools.md`。

## 2. 实际使用的 Tool（本项目核心链路）

| 工具名 | 中文 | 在本项目的作用 |
|---|---|---|
| `query-nearby-stores` | 查询附近门店 | 确定 `storeCode`，作为后续菜单/券查询的入口 |
| `query-meals` | 查询门店可售餐品 | 获取实时菜单（分类、餐品编码、价格、标签） |
| `query-meal-detail` | 查询餐品详情 | 查看套餐组成 / 可替换项（可选增强） |
| `list-nutrition-foods` | 餐品营养信息 | 提供热量、蛋白质、脂肪、碳水、钠，支撑低卡/增肌目标 |
| `query-store-coupons` | 门店可用券 | 获取当前门店可用优惠券，喂给优惠引擎 |
| `calculate-price` | 商品价格计算 | 用选品 + 优惠券核算金额、优惠与应付总价（下单前确认） |
| `create-order` | 创建订单 | 用户确认后下单并返回支付链接（**需用户显式确认，默认不自动下单**） |

> 说明：优惠券领取类（`available-coupons` / `auto-bind-coupons` / `query-my-coupons`）、外送地址类（`delivery-*`）、积分商城类（`mall-*`）、订单查询类（`query-order` / `order-list` / `cancel-order`）、活动日历（`campaign-calendar`）等工具均已接入能力范围，可作为后续迭代方向（见第 5 节），本项目 v1 聚焦"目标导向点餐 + 优惠最优化"主链路。

## 3. 调用流程（Call Flow）

```
用户意图
  │  "我想增肌，预算 35，帮我点"
  ▼
[1] query-nearby-stores ──► storeCode
  ▼
[2] query-meals(storeCode) ──► 实时菜单（Item 列表：编码/价格/标签）
[3] list-nutrition-foods() ──► 营养数据（kcal/蛋白/脂肪/碳水/钠）
[4] query-store-coupons(storeCode) ──► 可用券列表
  ▼
[5] smart_pick(goal, budget, items, coupons)   ← 纯函数，代码算，不靠模型口算
       ├─ 必含项优先
       ├─ 约束内组合搜索：枚举预算 / 热量上限 / 件数内的所有合法组合
       ├─ 按目标排序键取最优（性价比 / 蛋白 / 蛋白热量比 / 解馋度，含确定性 tie-break）
       └─ best_coupon() 在作用域与门槛内选最优券（默认不叠加）
  ▼
[6] calculate-price(items) ──► 官方核算金额，与本地结果交叉校验
  ▼
Agent 把方案"讲成人话"：搭了什么、省了多少、营养如何
  ▼
[7] create-order()  ← 仅当用户明确说"下单"时执行，返回支付链接
```

## 4. 业务价值（Business Value）

1. **把"算账"交还给代码**：套餐/优惠券组合的最优解交给确定性算法，避免大模型口算出错（这是用户最痛、模型最弱的点）。
2. **目标驱动，而非菜单罗列**：用"省钱 / 增肌 / 低卡 / 解馋"四个目标直接对齐用户真实意图，降低决策成本。
3. **零门槛可验证**：提供 `--demo` 离线模式与 `demo/index.html` 交互页，评委/访客不填 Token 也能立即看到效果，利于拿 Star。
4. **安全默认**：交易类工具（`create-order` 等）需用户显式确认，默认只读与规划，不产生未授权订单。
5. **可扩展**：MCP 工具已覆盖菜单/营养/券/订单/外送/积分商城/活动日历，主链路跑通后可平滑扩展（拼单、积分兑换规划、团餐等）。

## 5. 后续可叠加的 Tool（迭代方向）

- `auto-bind-coupons` + `query-my-coupons`：自动归集"我有哪些券"，与门店券合并求全局最优。
- `delivery-query-addresses` / `delivery-create-address` / `delivery-query-stores`：扩展麦乐送（外送）场景。
- `mall-points-products` / `mall-product-detail` / `mall-create-order`：积分兑换规划（"我的积分怎么花最值"）。
- `campaign-calendar`：结合当月活动做"限时最优"。

## 6. 真实链路验证（Live Evidence）

本项目已对 `https://mcp.mcd.cn` 完成一次**真实端到端调用**，四段链路（门店 → 菜单 → 券 → 计价）全部跑通，明细见 **[`evidence-real.md`](evidence-real.md)**（含官方 `traceId`，可追溯）。

| 环节 | 工具 | 真实验证结果 |
|---|---|---|
| 门店 | `query-nearby-stores` | 宁波天一广场命中 5 家，最近 `3330480`（218 m） |
| 菜单 | `query-meals` | 13 个分类、实时价（巨无霸 `1100` = ¥25.5） |
| 券 | `query-store-coupons` | 2 张券：中薯条买一送一 / 王牌小食拼 |
| 计价 | `calculate-price` | 巨无霸+中薯条+可乐 = **¥49.00**；券品「中薯条买一送一」**¥27 → ¥13.50**；「王牌小食拼」**¥22 → ¥15.90** |

**由此得到的两条关键设计结论**（已落地到代码）：

1. **门店券是"券品"，不是"满减券"**：券对应**独立券品编码**，挂在普通商品上会被拒——
   `4810` + couponId → `{"code": 600012,"message":"促销规则不支持该商品"}`。
   因此 `_adapt_deal_items()` 逐张 `calculate-price` 取**券后实付价**，把券品作为候选加入组合优化。
2. **`query-meals` 不含营养字段**：live 模式对常见餐品用公开近似值兜底，营养结论以 `list-nutrition-foods` 为准（已在 `live_pick` 返回值与文档中显式标注，不夸大）。

真实回包已固化为离线 fixtures，回归测试不依赖 Token：
`tests/test_live_adapt.py`（20 项全绿），解析逻辑见 `scripts/mcsmart.py` 第 5b 节。
