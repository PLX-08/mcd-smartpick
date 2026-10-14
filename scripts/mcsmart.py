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
        "items_codes": [i.code for i in sel],
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


# ============================================================
# 5b. 真实 MCP 回包解析（依据官方【实际返回结构】实现，并用真实回包回归测试）
#     见 tests/test_live_adapt.py：fixtures 取自 2026-10-14 对 mcp.mcd.cn 的真实调用。
#
#     MCP tools/call 原始返回为 JSON-RPC 2.0 信封，业务数据位于
#     result.content[0].text（JSON 字符串）；本模块统一解包为业务 dict 后再解析。
# ============================================================

# 官方菜单分类 / 标签 → 本引擎品类（近似映射，用于券作用域与目标打分）
_CATEGORY_HINTS = (
    ("dessert", ("甜品", "冰淇淋", "麦旋风", "新地", "圆筒", "派")),
    ("drink", ("饮品", "冷饮", "热饮", "可乐", "雪碧", "牛奶", "果汁", "咖啡", "茶", "柠")),
    ("side", ("小食", "薯条", "薯饼", "玉米", "苹果片", "麦乐鸡", "鸡翅", "鸡块",
              "鸡柳", "脆汁鸡", "沙拉", "鸡排", "买一送一")),
    ("breakfast", ("早餐", "麦满分")),
    ("main", ("汉堡", "堡", "卷", "巨无霸", "安格斯", "鳕鱼", "麦香鸡", "麦香鱼")),
)

# 常见餐品的公开近似营养值：MCP 的 query-meals 不含营养字段，
# live 模式在未取得官方营养数据时以此兜底（真实结果请以 list-nutrition-foods / 官方为准）。
_APPROX_NUTRITION = {
    "巨无霸": Nutrition(524, 25, 28, 42, 970),
    "麦辣鸡腿汉堡": Nutrition(500, 21, 26, 44, 980),
    "板烧鸡腿堡": Nutrition(440, 27, 18, 42, 1100),
    "双层吉士汉堡": Nutrition(440, 25, 23, 34, 1010),
    "麦香鸡": Nutrition(410, 17, 22, 36, 760),
    "麦香鱼": Nutrition(340, 15, 18, 33, 540),
    "薯条": Nutrition(340, 4, 17, 43, 440),
    "可乐": Nutrition(150, 0, 0, 39, 15),
    "雪碧": Nutrition(150, 0, 0, 39, 15),
    "圆筒冰淇淋": Nutrition(150, 3, 4, 25, 60),
    "派": Nutrition(250, 3, 11, 36, 230),
    "玉米杯": Nutrition(90, 3, 1, 18, 10),
    "苹果片": Nutrition(35, 0, 0, 8, 0),
    "纯牛奶": Nutrition(150, 8, 8, 12, 110),
    "鲜萃咖啡": Nutrition(5, 0, 0, 1, 5),
    "麦乐鸡": Nutrition(290, 15, 16, 17, 540),
    "麦辣鸡翅": Nutrition(230, 13, 13, 12, 480),
}


def _loads_loose(text: Any) -> Any:
    """宽松 JSON 解析：文本可能带前后说明文字，截取最外层 JSON 片段再解析。"""
    if not isinstance(text, str):
        return text
    s = text.strip()
    if s[:1] in "{[":
        try:
            return json.loads(s)
        except Exception:
            pass
    i, j = s.find("{"), s.rfind("}")
    if i != -1 and j > i:
        try:
            return json.loads(s[i:j + 1])
        except Exception:
            pass
    return {}


def _unwrap_mcp_result(res: Any) -> Dict[str, Any]:
    """
    把 MCP tools/call 的返回统一解包为业务 JSON（dict）。兼容：
      1) 原始 JSON-RPC 信封：{"result":{"content":[{"type":"text","text":"{...}"}]}}
      2) 已解包业务体：{"success":true,"data":...}
      3) content.text 夹带说明文字 → 宽松截取 JSON 片段
    """
    if res is None:
        return {}
    node = res
    if isinstance(node, dict) and "result" in node:
        node = node["result"]
    if isinstance(node, dict) and isinstance(node.get("content"), list) and node["content"]:
        for blk in node["content"]:
            if isinstance(blk, dict) and blk.get("type") == "text" and blk.get("text"):
                node = _loads_loose(blk["text"])
                break
    if isinstance(node, str):
        node = _loads_loose(node)
    return node if isinstance(node, dict) else {}


def _derive_category(group_name: str, tags: List[str], meal_name: str) -> str:
    """按「标签 > 餐品名 > 菜单分组名」的优先级推断品类，保持确定性。"""
    for source in (" ".join(tags or []), meal_name or "", group_name or ""):
        for cat, keys in _CATEGORY_HINTS:
            if any(k in source for k in keys):
                return cat
    return "main"


def _approx_nutrition(name: str) -> Nutrition:
    """公开近似营养值兜底（首次命中的关键词）。"""
    for k, v in _APPROX_NUTRITION.items():
        if k in (name or ""):
            return v
    return Nutrition()


def _crude_crave(category: str, name: str) -> float:
    """解馋满足度启发式（MCP 不提供该字段，用于 crave 目标是可复现的确定性映射）。"""
    base = {"dessert": 9.0, "side": 7.0, "main": 7.0, "drink": 5.0, "breakfast": 5.0}.get(category, 5.0)
    if any(k in (name or "") for k in ("辣", "脆", "炸", "买一送一")):
        base = min(10.0, base + 1.0)
    return base


def _extract_nearest_store(stores: Any) -> Dict[str, Any]:
    """从 query-nearby-stores 回包中取「距离最近」的门店。"""
    biz = _unwrap_mcp_result(stores)
    data = biz.get("data") or []
    if isinstance(data, dict):
        data = [data]
    cands = [s for s in data if isinstance(s, dict) and s.get("storeCode")]
    if not cands:
        raise RuntimeError("未在 query-nearby-stores 回包中找到门店（storeCode）")
    cands.sort(key=lambda s: (s.get("distance") is None, s.get("distance", 1 << 30)))
    s = cands[0]
    return {
        "storeCode": str(s["storeCode"]),
        "storeName": s.get("storeName"),
        "address": s.get("address"),
        "distance": s.get("distance"),
        "beCode": s.get("beCode") or None,
    }


def _adapt_menu(menu: Any) -> List[Item]:
    """把 query-meals 回包映射为内部 Item 列表（编码 / 名称 / 价格 / 品类 / 标签）。"""
    biz = _unwrap_mcp_result(menu)
    data = biz.get("data") or {}
    meals = data.get("meals") or {}
    if not isinstance(meals, dict):
        return []
    group_of: Dict[str, str] = {}
    tags_of: Dict[str, List[str]] = {}
    for c in data.get("categories") or []:
        gname = (c or {}).get("name") or ""
        for m in (c or {}).get("meals") or []:
            code = str((m or {}).get("code") or "")
            if not code:
                continue
            group_of.setdefault(code, gname)
            for t in (m or {}).get("tags") or []:
                tags_of.setdefault(code, [])
                if t not in tags_of[code]:
                    tags_of[code].append(t)
    items: List[Item] = []
    for code, m in meals.items():
        if not isinstance(m, dict):
            continue
        name = m.get("name") or str(code)
        try:
            price = float(m.get("currentPrice"))
        except (TypeError, ValueError):
            price = 0.0
        tags = tags_of.get(str(code), [])
        cat = _derive_category(group_of.get(str(code), ""), tags, name)
        items.append(Item(
            code=str(code), name=name, category=cat, price=price,
            tags=list(tags), nutrition=_approx_nutrition(name),
            crave=_crude_crave(cat, name),
        ))
    return items


def _adapt_coupon_records(coupons: Any) -> List[Dict[str, Any]]:
    """把 query-store-coupons 回包规整为券记录列表（保留 couponId/couponCode/商品编码）。"""
    biz = _unwrap_mcp_result(coupons)
    out: List[Dict[str, Any]] = []
    for c in biz.get("data") or []:
        if not isinstance(c, dict):
            continue
        products = c.get("products") or []
        prod = products[0] if products else {}
        code = str((prod or {}).get("productCode") or "")
        if not code:
            continue
        out.append({
            "title": c.get("title") or (prod or {}).get("productName") or code,
            "couponId": c.get("couponId"),
            "couponCode": c.get("couponCode"),
            "tradeDateTime": c.get("tradeDateTime"),
            "productCode": code,
            "productName": (prod or {}).get("productName"),
        })
    return out


def _adapt_deal_items(client: "McDMCPClient", store_code: str, coupons: Any,
                      order_type: int = 1, be_type: int = 1):
    """
    把门店券转成可参与组合优化的『券品』：
    对每张券，用其商品编码 + couponId 调一次 calculate-price 取【券后实付价】，
    作为该券品的价格纳入候选池（例：『中薯条买一送一』实付 ¥13.5，得 2 份中薯条）。

    返回 (deal_items, deal_of)：deal_of 以商品编码为键，供最终计价时回填 couponId/couponCode。
    """
    deal_items: List[Item] = []
    deal_of: Dict[str, Dict[str, str]] = {}
    for rec in _adapt_coupon_records(coupons):
        code = rec["productCode"]
        try:
            priced = _unwrap_mcp_result(client.call_tool("calculate-price", {
                "storeCode": store_code, "orderType": order_type, "beType": be_type,
                "items": [{"productCode": code, "quantity": 1,
                           "couponId": rec["couponId"], "couponCode": rec["couponCode"]}],
            }))
        except Exception:
            continue
        try:
            price = float((priced.get("data") or {}).get("price", 0)) / 100.0
        except (TypeError, ValueError):
            price = 0.0
        if price <= 0:
            continue
        cat = _derive_category("", [], rec["title"])
        deal_items.append(Item(code, rec["title"], cat, price, tags=["券品"],
                               nutrition=_approx_nutrition(rec["title"]),
                               crave=_crude_crave(cat, rec["title"])))
        deal_of[code] = {"couponId": rec["couponId"], "couponCode": rec["couponCode"],
                         "title": rec["title"]}
    return deal_items, deal_of


def live_pick(
    client: "McDMCPClient",
    goal: str,
    budget: float,
    city: str = "上海",
    keyword: str = "",
    max_items: int = 6,
) -> Dict[str, Any]:
    """
    真实链路（需 Token）：
      附近门店 -> 门店菜单 -> 门店券（转「券品」并逐张取券后价） -> 组合优化 -> 官方计价复核。
    返回与 smart_pick 同构的方案，并附 store / live_price_check / 建模说明。
    """
    client.initialize()

    stores_raw = client.call_tool(
        "query-nearby-stores", {"searchType": 2, "beType": 1, "city": city, "keyword": keyword})
    store = _extract_nearest_store(stores_raw)
    store_code = store["storeCode"]

    menu_raw = client.call_tool("query-meals", {"storeCode": store_code, "orderType": 1, "beType": 1})
    items = _adapt_menu(menu_raw)

    coupons_raw = client.call_tool("query-store-coupons", {"storeCode": store_code, "orderType": 1, "beType": 1})
    deal_items, deal_of = _adapt_deal_items(client, store_code, coupons_raw)

    plan = smart_pick(goal, budget, items + deal_items, [], max_items=max_items,
                      kcal_cap=800 if goal == "lowcal" else None)

    # 官方计价复核：把命中的「券品」带上 couponId/couponCode 再算一遍
    order_items: List[Dict[str, Any]] = []
    for code in plan.get("items_codes", []):
        row: Dict[str, Any] = {"productCode": code, "quantity": 1}
        if code in deal_of:
            row["couponId"] = deal_of[code]["couponId"]
            row["couponCode"] = deal_of[code]["couponCode"]
        order_items.append(row)
    if order_items:
        price_check = client.call_tool("calculate-price", {
            "storeCode": store_code, "orderType": 1, "beType": 1, "items": order_items})
        plan["live_price_check"] = _unwrap_mcp_result(price_check)

    plan["store"] = store
    plan["model_note"] = (
        "门店券按『券品』建模：逐张 calculate-price 取券后价后纳入候选池；"
        "query-meals 不含营养字段，营养使用公开近似值兜底。真实金额以 calculate-price 为准。"
    )
    return plan


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
    p.add_argument("--city", default="上海", help="live 模式：门店所在城市（如 宁波）")
    p.add_argument("--keyword", default="", help="live 模式：位置关键词（如 天一广场）")
    p.add_argument("--max-items", type=int, default=6, help="组合最多包含几件餐品")
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
            out = live_pick(client, args.goal, args.budget,
                            city=args.city, keyword=args.keyword, max_items=args.max_items)
            print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    required = [c.strip() for c in args.required.split(",") if c.strip()]
    plan = smart_pick(args.goal, args.budget, items, coupons,
                      required=required, kcal_cap=800 if args.goal == "lowcal" else None)
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
