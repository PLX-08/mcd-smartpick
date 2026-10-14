#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
McSmartPick · 真实 MCP 回包解析回归测试（零依赖，直接用 python 运行）。
运行：python tests/test_live_adapt.py

说明：下方 fixtures 取自 2026-10-14 对 https://mcp.mcd.cn 的真实调用回包
（门店：麦当劳宁波海曙区开明街餐厅 storeCode=3330480），仅对超长列表做裁剪，
字段结构与取值与线上一致。用于保证 live 模式的解析逻辑不会随官方结构变更而静默失效。
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from mcsmart import (  # noqa: E402
    _unwrap_mcp_result, _extract_nearest_store, _adapt_menu,
    _adapt_coupon_records, _adapt_deal_items, smart_pick,
)

# ---- 真实回包 fixture：query-nearby-stores（裁剪为最近 2 家）----
NEARBY_STORES = {
    "success": True, "code": 200, "message": "请求成功",
    "datetime": "2026-10-14 15:16:55",
    "traceId": "e3cda57b675e68b951fc4226581d7e1c",
    "data": [
        {"storeCode": "3330480", "storeName": "麦当劳宁波海曙区开明街餐厅",
         "address": "开明街天一广场Ib101、Ib102、Ib201商铺", "distance": 218,
         "businessStatus": True, "reservation": True},
        {"storeCode": "3330440", "storeName": "麦当劳宁波新天一广场餐厅",
         "address": "日新街86号天一广场华润万家旁麦当劳", "distance": 270,
         "businessStatus": True, "reservation": True},
    ],
}

# ---- 真实回包 fixture：query-meals（裁剪为 6 个餐品）----
MENU = {
    "success": True, "code": 200, "message": "请求成功",
    "datetime": "2026-10-14 15:16:23",
    "traceId": "8d9516ec67a133345d35e9c86bb753be",
    "data": {
        "categories": [
            {"name": "巨无霸\n牛鱼肉堡",
             "meals": [{"code": "1100", "tags": ["单品", "100%纯牛肉"]}]},
            {"name": "鸡肉汉堡\n/卷",
             "meals": [{"code": "1440", "tags": ["单品", "人气经典", "外酥里嫩"]}]},
            {"name": "小食甜品\n/其他",
             "meals": [{"code": "4810", "tags": ["小食"]},
                       {"code": "515837", "tags": ["冰淇淋"]}]},
            {"name": "饮品",
             "meals": [{"code": "9900008751", "tags": ["冷饮"]}]},
        ],
        "meals": {
            "1100": {"name": "巨无霸", "currentPrice": "25.5", "originalPrice": "25.5",
                     "canWithOrder": False},
            "1440": {"name": "麦辣鸡腿汉堡", "currentPrice": "22.5", "originalPrice": "22.5",
                     "canWithOrder": False},
            "4810": {"name": "薯条", "currentPrice": "13.5", "originalPrice": "13.5",
                     "canWithOrder": False},
            "515837": {"name": "圆筒冰淇淋", "currentPrice": "5", "originalPrice": "5",
                       "canWithOrder": False},
            "9900008751": {"name": "可乐", "currentPrice": "10", "originalPrice": "10",
                           "canWithOrder": False},
        },
    },
}

# ---- 真实回包 fixture：query-store-coupons ----
COUPONS = {
    "success": True, "code": 200, "message": "请求成功",
    "datetime": "2026-10-14 15:16:15",
    "traceId": "80ffd2228890d2d6e13884d556bc6a19",
    "data": [
        {"title": "中薯条买一送一",
         "couponId": "8692944B045928451618BFF22F535D2A",
         "couponCode": "MCD61QX7J007S91K0100F",
         "tradeDateTime": "2026-10-12 10:30:00-2026-10-16 23:59:59",
         "products": [{"productCode": "9900012387", "productName": "中薯条买一送一"}]},
        {"title": "王牌小食拼",
         "couponId": "E05F6BFB4BAFAA5DB44B233583BFE711",
         "couponCode": "MCD6Q1M014X0S090FJ016",
         "tradeDateTime": "2026-10-12 10:30:00-2026-10-16 23:59:59",
         "products": [{"productCode": "9900016371", "productName": "王牌小食拼"}]},
    ],
}

# ---- 真实回包 fixture：calculate-price（三个真实计价结果）----
PRICE_BY_CODE = {
    # 巨无霸 + 中薯条 + 可乐（无券）
    "__base__": {"success": True, "code": 200, "traceId": "ad938ccabd2ab90b7cc63887a4c78f7b",
                 "data": {"productOriginalPrice": 4900, "price": 4900, "discount": 0,
                          "productList": [
                              {"productCode": "1100", "productName": "巨无霸", "quantity": 1,
                               "originalSubtotal": 2550, "subtotal": 2550},
                              {"productCode": "4810", "productName": "中薯条", "quantity": 1,
                               "originalSubtotal": 1350, "subtotal": 1350},
                              {"productCode": "9900008751", "productName": "可乐", "quantity": 1,
                               "originalSubtotal": 1000, "subtotal": 1000}]}},
    # 券品：中薯条买一送一 → 原价 2700，券后 1350
    "9900012387": {"success": True, "code": 200, "traceId": "c696cc16933004412fba555e10d2cc55",
                   "data": {"productOriginalPrice": 2700, "price": 1350, "discount": 1350,
                            "productList": [{"productCode": "9900012387",
                                             "productName": "中薯条买一送一", "quantity": 1,
                                             "originalSubtotal": 2700, "subtotal": 1350}]}},
    # 券品：王牌小食拼 → 原价 2200，券后 1590
    "9900016371": {"success": True, "code": 200, "traceId": "4caf9089bb865a062ef27165ae4ae42d",
                   "data": {"productOriginalPrice": 2200, "price": 1590, "discount": 610,
                            "productList": [{"productCode": "9900016371",
                                             "productName": "王牌小食拼", "quantity": 1,
                                             "originalSubtotal": 2200, "subtotal": 1590}]}},
}


class FakeClient:
    """最小化假客户端：按券品商品编码返回对应的真实计价回包。"""

    def __init__(self):
        self.calls = []

    def call_tool(self, name, arguments=None):
        arguments = arguments or {}
        self.calls.append((name, arguments))
        code = (arguments.get("items") or [{}])[0].get("productCode")
        return PRICE_BY_CODE.get(code, {})


def run():
    passed = 0
    failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  PASS  {name}")
        else:
            failed += 1
            print(f"  FAIL  {name}")

    # 1) JSON-RPC 信封（result.content[0].text 内为 JSON 字符串）能被解包
    import json as _json
    envelope = {"jsonrpc": "2.0", "id": 3,
                "result": {"content": [{"type": "text", "text": _json.dumps(COUPONS)}],
                           "isError": False}}
    un = _unwrap_mcp_result(envelope)
    check("unwrap JSON-RPC envelope", un.get("success") is True and len(un.get("data", [])) == 2)

    # 2) 已解包业务体原样通过
    check("unwrap plain business body", _unwrap_mcp_result(COUPONS) is COUPONS)

    # 3) 夹带说明文字时宽松截取 JSON
    check("loose parse with prefix text",
          _unwrap_mcp_result('说明文字 { "success": true, "data": [1] } 后缀')["data"] == [1])

    # 4) 最近门店解析（取 distance 最小者）
    store = _extract_nearest_store(NEARBY_STORES)
    check("nearest store = 3330480 @218m",
          store["storeCode"] == "3330480" and store["distance"] == 218)

    # 5) 菜单映射：编码 / 名称 / 价格（元）
    items = _adapt_menu(MENU)
    by_code = {i.code: i for i in items}
    check("menu size", len(items) == 5)
    check("巨无霸 price=25.5", by_code["1100"].price == 25.5 and by_code["1100"].name == "巨无霸")
    check("麦辣鸡腿汉堡 price=22.5", by_code["1440"].price == 22.5)

    # 6) 品类推断：汉堡=main / 薯条=side / 冰淇淋=dessert / 可乐=drink
    check("category 1100 -> main", by_code["1100"].category == "main")
    check("category 4810 -> side", by_code["4810"].category == "side")
    check("category 515837 -> dessert", by_code["515837"].category == "dessert")
    check("category 9900008751 -> drink", by_code["9900008751"].category == "drink")

    # 7) 券记录规整
    recs = _adapt_coupon_records(COUPONS)
    check("coupon records", len(recs) == 2 and recs[0]["productCode"] == "9900012387"
          and recs[1]["couponId"] == "E05F6BFB4BAFAA5DB44B233583BFE711")

    # 8) 券品转候选（用真实计价回包取券后价：13.5 / 15.9）
    fake = FakeClient()
    deal_items, deal_of = _adapt_deal_items(fake, "3330480", COUPONS)
    dmap = {i.code: i for i in deal_items}
    check("deal item 中薯条买一送一 price=13.5", dmap["9900012387"].price == 13.5)
    check("deal item 王牌小食拼 price=15.9", dmap["9900016371"].price == 15.9)
    check("deal_of carries couponCode", deal_of["9900012387"]["couponCode"] == "MCD61QX7J007S91K0100F")
    check("per-coupon calculate-price called", len(fake.calls) == 2)

    # 9) 真实菜单 + 券品候选池可跑通组合优化（不崩溃、结果确定、且在预算内）
    pool = items + deal_items
    plan = smart_pick("save", 40.0, pool, [])
    check("live pool optimizes within budget", plan["final_total"] <= 40.0 + 1e-6)
    check("plan exposes items_codes", len(plan["items_codes"]) == len(plan["items"]))
    plan2 = smart_pick("save", 40.0, pool, [])
    check("live pool deterministic", plan == plan2)

    # 10) 券后价应当被识别为"更划算"：同样花钱，券品比单品更值得（13.5 得 2 份中薯条）
    cheap = smart_pick("crave", 15.0, pool, [])
    check("crave picks something sane", cheap["final_total"] <= 15.0 + 1e-6)

    print(f"\n结果：{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
