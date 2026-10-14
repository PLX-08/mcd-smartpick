# 麦当劳 MCP 真实工具清单与注意事项

> 来源：https://open.mcd.cn/mcp/doc 与 `M-China/mcd-mcp-server`。
> 以下为已知 Tool 清单；实际可用工具以官方运行时 `tools/list` 返回为准。本项目 v1 主链路使用其中 7 个（见 `MCP_INTEGRATION.md` 第 2 节）。

## 菜单与餐品

| Tool | 中文 | 关键入参 | 说明 |
|---|---|---|---|
| `query-meals` | 查询门店可售餐品 | `storeCode`, `beCode`, `orderType` | 分类、餐品编码、标签、价格 |
| `query-meal-detail` | 查询餐品详情 | 餐品编码 | 套餐组成、可替换项 |
| `list-nutrition-foods` | 餐品营养信息 | — | 能量/蛋白/脂肪/碳水/钠/钙 |
| `query-nearby-stores` | 查询附近门店 | `searchType`, `beType`, `city`, `keyword` | 返回 `storeCode` |
| `query-store-coupons` | 门店可用券 | `storeCode`, `beCode`, `orderType` | 当前门店可用优惠 |

## 优惠券

| Tool | 中文 | 说明 |
|---|---|---|
| `query-my-coupons` | 我的优惠券 | 已领取的券 |
| `available-coupons` | 麦麦省券列表 | 可领取的券 |
| `auto-bind-coupons` | 麦麦省一键领券 | 自动领取所有可用券（交易类，需确认） |

## 计价与订单

| Tool | 中文 | 说明 |
|---|---|---|
| `calculate-price` | 商品价格计算 | 含优惠券核算金额/优惠/应付（**下单前确认用**） |
| `create-order` | 创建订单 | 返回订单详情与支付链接（**交易类，需确认**） |
| `cancel-order` | 取消订单 | — |
| `query-order` | 查询订单 | 状态/内容/配送 |
| `order-list` | 历史订单 | 到店/外送近期订单 |

## 外送（麦乐送）

| Tool | 中文 | 说明 |
|---|---|---|
| `delivery-query-addresses` | 配送地址列表 | `beType=2` |
| `delivery-create-address` | 新增配送地址 | — |
| `delivery-query-stores` | 可配送门店列表 | 收货地址附近门店 |

## 积分商城（麦麦商城）

| Tool | 中文 | 说明 |
|---|---|---|
| `query-my-account` | 积分查询 | 积分余额 |
| `mall-points-products` | 积分兑换商品 | 可兑换列表 |
| `mall-product-detail` | 积分商品详情 | — |
| `mall-create-order` | 积分兑换下单 | **交易类，需确认** |

## 其他

| Tool | 中文 | 说明 |
|---|---|---|
| `campaign-calendar` | 活动日历 | 当月营销活动 |
| `query-meal-assistance` | 助餐服务 | 仅企业团餐场景 |

## ⚠️ 注意事项（踩坑记录）

1. **金额单位**：所有金额单位为**分**，需 ÷100 得到元（部分接口已自动转换，以实际返回为准）。
2. **`calculate-price` / `create-order` 参数格式**：`items` 必须是 JSON 对象数组（不能是字符串），与 `storeCode` / `beCode` / `addressId` 一起作为顶层参数传入。
3. **优惠券作用域**：带 `scope`（如"甜品满15减5"）的券仅对含该品类的组合生效，引擎已在 `best_coupon()` 中按 `categories` 校验，避免误用。
4. **限流**：每个 Token 每分钟最多 600 次请求；超频返回 `429`，需降低频率。
5. **鉴权失败**：`401` 表示 Token 无效/过期/未提供，需到 open.mcd.cn/mcp 重新激活。
6. **MCP 版本**：Server 仅支持特定 MCP 版本，客户端需兼容；本项目用标准 `initialize` 握手。
7. **交易类工具默认禁用/需确认**：`create-order`、`auto-bind-coupons`、`mall-create-order` 等不得自动执行，必须用户显式确认。
