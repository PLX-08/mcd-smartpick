#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
McSmartPick —— 麦门聪明点
============================================================
基于麦当劳官方 MCP（https://mcp.mcd.cn）的「目标导向智能点餐」Skill 内核。

设计原则（与优秀参赛作品一致）：
    取数交给 MCP，算术交给代码，表达交给 Agent。
  - 实时数据（菜单 / 营养 / 优惠券 / 门店）通过麦当劳 MCP 获取；
  - 组合优化（在预算与目标下选出最优餐品组合）由本文件中的【纯函数】完成，
    不依赖大模型口算，保证可复现、可测试、可审计；
  - 自然语言解释（省了多少、为什么这么搭）由上层 Agent / SKILL.md 负责。

本文件零第三方依赖（仅 Python 标准库），可在【无 Token 的离线模式】下直接运行演示。
"""

import os
import sys
import json
import argparse
import itertools
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ============================================================
# 1. 数据模型
# ============================================================
@dataclass
class Nutrition:
    kcal: float = 0.0
    protein: float = 0.0
    fat: float = 0.0
    carb: float = 0.0
    sodium: float = 0.0


@dataclass
class Item:
    code: str            # 餐品编码（对接 MCP query-meals 返回的编码）
    name: str            # 中文名
    category: str        # main / side / drink / dessert / breakfast
    price: float         # 单价（元）
    tags: List[str] = field(default_factory=list)
    nutrition: Nutrition = field(default_factory=Nutrition)
    crave: float = 0.0   # 解馋满足度 0~10（越高越"解馋"）


@dataclass
class Coupon:
    id: str
    name: str
    kind: str            # 'amount' 固定金额减 / 'percent' 百分比折扣
    value: float         # 金额(元) 或 百分比(如 20 表示减 20%)
    min_spend: float = 0.0   # 最低消费门槛
    scope: str = 'all'   # 'all' 或 指定品类


# ============================================================
# 2. 离线示例数据（演示用，真实数据由 MCP 实时获取）
#    营养与价格为公开近似值，仅用于离线复现；正式结果以官方实时数据为准。
# ============================================================
def load_sample_data() -> (List[Item], List[Coupon]):
    items = [
        Item("M1", "巨无霸", "main", 24.0, ["经典", "牛肉"], Nutrition(524, 25, 28, 42, 970), 9),
        Item("M2", "麦辣鸡腿堡", "main", 21.0, ["辣", "鸡肉"], Nutrition(500, 21, 26, 44, 980), 8),
        Item("M3", "板烧鸡腿堡", "main", 22.0, ["鸡肉"], Nutrition(440, 27, 18, 42, 1100), 7),
        Item("M4", "双层吉士堡", "main", 19.0, ["牛肉", "芝士"], Nutrition(440, 25, 23, 34, 1010), 8),
        Item("M5", "麦香鸡", "main", 14.0, ["鸡肉"], Nutrition(410, 17, 22, 36, 760), 6),
        Item("M6", "猪柳麦满分", "breakfast", 13.0, ["早餐", "猪肉"], Nutrition(310, 17, 16, 26, 750), 6),
        Item("S1", "薯条(大)", "side", 12.0, ["薯条"], Nutrition(500, 6, 25, 63, 650), 9),
        Item("S2", "薯条(中)", "side", 10.0, ["薯条"], Nutrition(340, 4, 17, 43, 440), 8),
        Item("S3", "麦乐鸡(6块)", "side", 15.0, ["鸡肉", "分享"], Nutrition(290, 15, 16, 17, 540), 8),
        Item("S4", "玉米杯", "side", 9.0, ["蔬菜", "健康"], Nutrition(90, 3, 1, 18, 10), 3),
        Item("S5", "苹果片", "side", 8.0, ["水果", "健康"], Nutrition(35, 0, 0, 8, 0), 2),
        Item("D1", "可乐(中)", "drink", 10.0, ["碳酸", "冰"], Nutrition(150, 0, 0, 39, 15), 7),
        Item("D2", "雪碧(中)", "drink", 10.0, ["碳酸", "冰"], Nutrition(150, 0, 0, 39, 15), 7),
        Item("D3", "纯牛奶", "drink", 11.0, ["牛奶", "健康"], Nutrition(150, 8, 8, 12, 110), 4),
        Item("D4", "橙汁(小)", "drink", 12.0, ["果汁", "维C"], Nutrition(110, 1, 0, 26, 10), 5),
        Item("D5", "美式咖啡", "drink", 13.0, ["咖啡", "无糖"], Nutrition(5, 0, 0, 1, 5), 3),
        Item("E1", "麦旋风(OREO)", "dessert", 16.0, ["甜品", "冰"], Nutrition(350, 6, 12, 54, 180), 10),
        Item("E2", "苹果派", "dessert", 7.0, ["甜品", "热"], Nutrition(250, 3, 11, 36, 230), 7),
        Item("E3", "圆筒冰淇淋", "dessert", 5.0, ["甜品", "冰"], Nutrition(150, 3, 4, 25, 60), 8),
        Item("V1", "田园脆鸡沙拉", "side", 18.0, ["沙拉", "健康", "蔬菜"], Nutrition(180, 12, 8, 14, 420), 4),
    ]
    coupons = [
        Coupon("C1", "满30减8", "amount", 8.0, 30.0, "all"),
        Coupon("C2", "满40减12", "amount", 12.0, 40.0, "all"),
        Coupon("C3", "全场9折", "percent", 10.0, 0.0, "all"),
        Coupon("C4", "甜品满15减5", "amount", 5.0, 15.0, "dessert"),
    ]
    return items, coupons


# ============================================================
# 3. 优惠券择优（纯函数，可测试）
# ============================================================
def best_coupon(items_total: float, coupons: List[Coupon], categories: Optional[set] = None) -> Optional[Coupon]:
    """
    在所有满足条件的券中选折扣力度最大的一张（本引擎默认不叠加，见文档）。
    categories: 当前组合包含的品类集合，用于校验 scope 受限券（如"甜品满15减5"仅对含甜品的组合生效）。
    """
    best: Optional[Coupon] = None
    best_discount = 0.0
    for c in coupons:
        if items_total < c.min_spend:
            continue
        # scope 为指定品类时，仅当组合中确实包含该品类才适用
        if c.scope != "all":
            if not categories or c.scope not in categories:
                continue
        discount = c.value if c.kind == "amount" else items_total * c.value / 100.0
        discount = min(discount, items_total)  # 折扣不超过原价
        if discount > best_discount:
            best_discount = discount
            best = c
    return best


# ============================================================
# 4. 目标导向组合优化（核心纯函数，可测试）
# ============================================================
def smart_pick(
    goal: str,
    budget: float,
    items: List[Item],
    coupons: List[Coupon],
    required: Optional[List[str]] = None,
    max_items: int = 6,
    kcal_cap: Optional[float] = None,
) -> Dict[str, Any]:
    """
    在预算与目标下选出最优餐品组合。

    goal:
      save    省钱      —— 预算内获得最饱腹(蛋白/价格比)组合，叠加最优券后总价最低
      protein 增肌高蛋白 —— 预算内最大化蛋白质总量
      lowcal  低卡控糖  —— 预算内、热量上限内最大化蛋白/热量比
      crave   解馋满足  —— 预算内最大化"解馋满足度"
    """
    required = required or []
    selected_required: List[Item] = []

    # (1) 必须包含的项优先保留（不参与搜索，始终入选）
    for code in required:
        it = next((i for i in items if i.code == code), None)
        if it and it not in selected_required:
            selected_required.append(it)

    # (2) 候选池（排除必含项）
    pool = [i for i in items if i not in selected_required]

    base_price = sum(i.price for i in selected_required)
    base_kcal = sum(i.nutrition.kcal for i in selected_required)

    # (3) 约束内组合搜索：枚举所有「必含项 + 候选池子集」满足约束的组合，
    #     按目标打分取最优。相比贪心，能避免预算碎片/顺序导致的次优（如 ratio 相同时选错）。
    max_extra = max(0, max_items - len(selected_required))
    best: Optional[tuple] = None
    best_key = None

    for k in range(0, max_extra + 1):
        for combo in itertools.combinations(pool, k):
            sel = selected_required + list(combo)
            raw = sum(i.price for i in sel)
            if raw > budget + 1e-9:
                continue
            kcal = base_kcal + sum(i.nutrition.kcal for i in combo)
            if kcal_cap is not None and kcal > kcal_cap + 1e-9:
                continue
            cats = {i.category for i in sel}
            coupon = best_coupon(raw, coupons, cats)
            discount = 0.0
            if coupon:
                discount = coupon.value if coupon.kind == "amount" else raw * coupon.value / 100.0
                discount = min(discount, raw)
            final = max(raw - discount, 0.0)
            key = _objective_key(goal, sel, final)
            if best is None or key > best_key:
                best = (sel, raw, final, coupon, discount)
                best_key = key

    # (4) 兜底：若连必含项都已超预算而无可行组合，至少返回必含项，避免崩溃
    if best is None:
        sel = selected_required
        raw = base_price
        cats = {i.category for i in sel}
        coupon = best_coupon(raw, coupons, cats)
        discount = 0.0
        if coupon:
            discount = coupon.value if coupon.kind == "amount" else raw * coupon.value / 100.0
            discount = min(discount, raw)
        final = max(raw - discount, 0.0)
        best = (sel, raw, final, coupon, discount)

    sel, raw, final, coupon, discount = best
    raw = round(raw, 2)
    discount = round(discount, 2)
    final = round(final, 2)

    # (5) 营养汇总
    nut = Nutrition()
    for i in sel:
        nut.kcal += i.nutrition.kcal
        nut.protein += i.nutrition.protein
        nut.fat += i.nutrition.fat
        nut.carb += i.nutrition.carb
        nut.sodium += i.nutrition.sodium

    return {
        "goal": goal,
        "items": [i.name for i in sel],
        "raw_total": raw,
        "coupon": coupon.name if coupon else None,
        "discount": discount,
        "final_total": final,
        "savings": round(raw - final, 2),
        "nutrition": {
            "kcal": round(nut.kcal, 1),
            "protein": round(nut.protein, 1),
            "fat": round(nut.fat, 1),
            "carb": round(nut.carb, 1),
            "sodium": round(nut.sodium, 1),
        },
    }


def _objective_key(goal: str, sel: List[Item], final: float) -> tuple:
    """为某组合计算目标排序键（越大越优），保证确定性。"""
    prot = sum(i.nutrition.protein for i in sel)
    if goal == "protein":
        # 预算内最大化蛋白质，其次尽量便宜、尽量精简
        return (prot, -final, -len(sel))
    if goal == "save":
        # 与 protein 同目标取向：最饱腹 + 最省钱（演示四目标中二者侧重"性价比"）
        return (prot, -final, -len(sel))
    if goal == "lowcal":
        kcal = sum(i.nutrition.kcal for i in sel)
        ratio = prot / kcal if kcal > 0 else 0.0
        return (ratio, -final, -len(sel))
    if goal == "crave":
        c = sum(i.crave for i in sel)
        return (c, -final, -len(sel))
    raise ValueError(f"未知目标: {goal}")


# ============================================================
# 5. 麦当劳 MCP 客户端（Streamable HTTP，零依赖）
#    说明：以下为按 MCP 规范实现的接入层；无 Token 时不可用，但离线引擎完全可跑。
# ============================================================
class McDMCPClient:
    def __init__(self, token: str, url: str = "https://mcp.mcd.cn"):
        self.token = token
        self.url = url
        self.session: Optional[str] = None

    def _post(self, payload: Dict[str, Any]) -> Any:
        import urllib.request
        import urllib.error
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json, text/event-stream")
        req.add_header("Authorization", f"Bearer {self.token}")
        if self.session:
            req.add_header("Mcp-Session-Id", self.session)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                sid = resp.headers.get("Mcp-Session-Id")
                if sid:
                    self.session = sid
                ctype = resp.headers.get("Content-Type", "")
                return self._parse(body, ctype)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise RuntimeError("MCP Token 无效或已过期（401）。请到 open.mcd.cn/mcp 重新激活。")
            if e.code == 429:
                raise RuntimeError("触发限流（429，>600 次/分钟）。请降低调用频率。")
            raise

    @staticmethod
    def _parse(body: str, ctype: str) -> Any:
        if "text/event-stream" in ctype:
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if chunk:
                        return json.loads(chunk)
            return None
        return json.loads(body)

    def initialize(self) -> Any:
        return self._post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcsmart", "version": "1.0.0"},
            },
        })

    def list_tools(self) -> Any:
        return self._post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        return self._post({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        })


def live_pick(client: McDMCPClient, goal: str, budget: float) -> Dict[str, Any]:
    """
    真实链路（需 Token）：附近门店 -> 菜单 -> 门店券 -> 优化 -> 计价。
    返回与 smart_pick 相同结构的方案。具体字段以麦当劳 MCP 实际返回为准。
    """
    client.initialize()
    stores = client.call_tool("query-nearby-stores", {"searchType": 2, "beType": 1, "city": "上海", "keyword": ""})
    store_code = _extract_first_store_code(stores)
    menu = client.call_tool("query-meals", {"storeCode": store_code, "beCode": None, "orderType": 1})
    coupons = client.call_tool("query-store-coupons", {"storeCode": store_code, "beCode": None, "orderType": 1})
    items, coup = _adapt_mcp(menu, coupons)  # 将 MCP 返回映射为内部 Item/Coupon
    plan = smart_pick(goal, budget, items, coup, kcal_cap=800 if goal == "lowcal" else None)
    price = client.call_tool("calculate-price", {"items": [_item_to_mcp(i) for i in items if i.name in plan["items"]]})
    plan["live_price_check"] = price
    return plan


def _extract_first_store_code(stores: Any) -> str:
    # 真实实现需按 MCP 返回结构解析；此处占位
    if isinstance(stores, dict):
        return stores.get("storeCode", "DEMO_STORE")
    return "DEMO_STORE"


def _adapt_mcp(menu: Any, coupons: Any):
    # 真实实现需按 MCP 返回结构映射；此处返回空（live 模式需补充解析）
    return [], []


def _item_to_mcp(item: Item) -> Dict[str, Any]:
    return {"code": item.code, "name": item.name, "price": item.price}


# ============================================================
# 6. 离线演示
# ============================================================
GOAL_CN = {
    "save": "省钱",
    "protein": "增肌高蛋白",
    "lowcal": "低卡控糖",
    "crave": "解馋满足",
}


def _narrative(goal: str, budget: float, plan: Dict[str, Any]) -> str:
    nut = plan["nutrition"]
    lines = []
    lines.append(f"【目标：{GOAL_CN.get(goal, goal)} ｜ 预算 ¥{budget:.0f}】")
    lines.append(f"  推荐搭配：{' + '.join(plan['items'])}")
    lines.append(f"  原价 ¥{plan['raw_total']:.2f}，使用「{plan['coupon'] or '无'}」立减 ¥{plan['discount']:.2f}")
    lines.append(f"  👉 实付 ¥{plan['final_total']:.2f}，共省 ¥{plan['savings']:.2f}（约 {round(plan['savings'] / plan['raw_total'] * 100) if plan['raw_total'] else 0}%）")
    lines.append(f"  营养参考：{nut['kcal']} kcal ｜ 蛋白 {nut['protein']}g ｜ 脂肪 {nut['fat']}g ｜ 碳水 {nut['carb']}g")
    return "\n".join(lines)


def demo() -> str:
    items, coupons = load_sample_data()
    out = []
    out.append("=" * 56)
    out.append("McSmartPick 离线演示（无 Token，数据为标准库内置示例）")
    out.append("=" * 56)
    cases = [
        ("save", 30.0, []),
        ("protein", 35.0, []),
        ("lowcal", 30.0, []),
        ("crave", 25.0, []),
    ]
    for goal, budget, req in cases:
        plan = smart_pick(goal, budget, items, coupons,
                          required=req, kcal_cap=800 if goal == "lowcal" else None)
        out.append("")
        out.append(_narrative(goal, budget, plan))
    return "\n".join(out)


# ============================================================
# 7. 命令行入口
# ============================================================
def main() -> None:
    p = argparse.ArgumentParser(description="McSmartPick 麦门聪明点")
    p.add_argument("--demo", action="store_true", help="离线演示（无需 Token）")
    p.add_argument("--goal", default="protein", choices=["save", "protein", "lowcal", "crave"])
    p.add_argument("--budget", type=float, default=30.0, help="预算（元）")
    p.add_argument("--required", default="", help="必含餐品 code，逗号分隔，如 M1,S1,D1")
    p.add_argument("--live", action="store_true", help="调用真实麦当劳 MCP（需 Token）")
    p.add_argument("--token", default=None, help="MCP Token（或读环境变量 MCD_MCP_TOKEN）")
    p.add_argument("--tool", default=None, help="live 模式直接调用某工具，如 query-meals")
    p.add_argument("--args", default="{}", help="live 工具参数 JSON")
    p.add_argument("--out", default=None, help="将离线演示写入指定文件（UTF-8）")
    args = p.parse_args()

    if args.demo:
        text = demo()
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            print(f"已写入: {args.out}")
        else:
            print(text)
        return

    items, coupons = load_sample_data()

    if args.live:
        token = args.token or os.environ.get("MCD_MCP_TOKEN")
        if not token:
            print("缺少 MCP Token：设置环境变量 MCD_MCP_TOKEN 或用 --token 传入。")
            sys.exit(1)
        client = McDMCPClient(token)
        client.initialize()
        if args.tool:
            res = client.call_tool(args.tool, json.loads(args.args))
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            out = live_pick(client, args.goal, args.budget)
            print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    required = [c.strip() for c in args.required.split(",") if c.strip()]
    plan = smart_pick(args.goal, args.budget, items, coupons,
                      required=required, kcal_cap=800 if args.goal == "lowcal" else None)
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
