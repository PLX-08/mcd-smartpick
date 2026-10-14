#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
McSmartPick 引擎纯函数测试（零依赖，直接用 python 运行）。
运行：python tests/test_engine.py
"""
import sys
import os

# 允许直接运行：把 scripts/ 加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from mcsmart import load_sample_data, smart_pick, best_coupon, Item, Nutrition  # noqa: E402


def run():
    items, coupons = load_sample_data()
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

    # 1) 必含项必须出现
    plan = smart_pick("protein", 40.0, items, coupons, required=["M1"])
    check("required item included", "巨无霸" in plan["items"])

    # 2) 实付不超过预算
    for goal, budget in [("save", 30), ("protein", 35), ("lowcal", 30), ("crave", 25)]:
        p = smart_pick(goal, float(budget), items, coupons,
                       kcal_cap=800 if goal == "lowcal" else None)
        check(f"{goal}: final <= budget", p["final_total"] <= budget + 1e-6)

    # 3) 省钱数 = 原价 - 实付
    plan = smart_pick("protein", 35.0, items, coupons)
    check("savings math", abs(plan["savings"] - (plan["raw_total"] - plan["final_total"])) < 1e-6)

    # 4) 优惠券作用域：无甜品的组合不应套用"甜品满15减5"
    no_dessert = [i for i in items if i.category != "dessert"]
    raw = sum(i.price for i in no_dessert[:3])
    c = best_coupon(raw, coupons, {i.category for i in no_dessert[:3]})
    check("dessert coupon not applied without dessert",
          not (c is not None and c.scope == "dessert"))

    # 5) 满减门槛：低于门槛不应触发
    cheap = best_coupon(10.0, coupons, {"main"})
    check("min_spend gating (满30减8 not triggered at 10)",
          not (cheap is not None and cheap.id == "C1"))

    # 6) 确定性：相同输入得到相同结果
    a = smart_pick("crave", 25.0, items, coupons)
    b = smart_pick("crave", 25.0, items, coupons)
    check("deterministic", a == b)

    # 7) 低卡目标确实压低热量
    lc = smart_pick("lowcal", 30.0, items, coupons, kcal_cap=800)
    check("lowcal under kcal cap", lc["nutrition"]["kcal"] <= 800 + 1e-6)

    # 8) 组合搜索应优于贪心：构造能"骗过"贪心的小菜单
    #    B(10元,蛋白10) A(6元,蛋白6) C(9元,蛋白9)，预算15，目标 protein
    #    贪心按 ratio(均=1) 取首序 B，余 5 元加不进任何项 → 蛋白仅 10
    #    搜索应找到 A+C=15元、蛋白 15 的最优组合
    small = [
        Item("B", "B", "main", 10.0, [], Nutrition(0, 10, 0, 0, 0)),
        Item("A", "A", "main", 6.0, [], Nutrition(0, 6, 0, 0, 0)),
        Item("C", "C", "main", 9.0, [], Nutrition(0, 9, 0, 0, 0)),
    ]
    sp = smart_pick("protein", 15.0, small, [])
    check("search beats greedy (protein 15 vs 10)", sp["nutrition"]["protein"] == 15.0)

    # 9) max_items 约束：限制为 1 时入选餐品不超过 1
    mo = smart_pick("protein", 100.0, items, coupons, max_items=1)
    check("max_items respected", len(mo["items"]) <= 1)

    # ---- 边界用例（回归保护，引擎需保持"安全不崩溃"）----

    # 10) 空菜单：不崩溃，返回空方案、零金额
    empty = smart_pick("protein", 30.0, [], [])
    check("empty menu safe", empty["items"] == [] and empty["final_total"] == 0.0)

    # 11) 极小预算：所有单品均超预算，返回空方案而非崩溃
    tiny = smart_pick("protein", 1.0, items, coupons)
    check("tiny budget safe", tiny["final_total"] <= 1.0 + 1e-6)

    # 12) 券不叠加：多张可用券只选折扣最大的一张（而非金额累加）
    #     C1(满30减8) / C2(满40减12) / C3(9折) 对 50 元均可用，最优应为 C2(减12)
    c_best = best_coupon(50.0, coupons, {"main"})
    check("best coupon is single largest (no stacking)",
          c_best is not None and c_best.id == "C2")

    # 13) 满减门槛边界：恰好达到门槛（=30）即应触发，而非 >30 才触发
    c_edge = best_coupon(30.0, coupons, {"main"})
    check("min_spend boundary triggers at exactly 30",
          c_edge is not None and c_edge.id == "C1")

    # 14) 必含项超预算兜底：不崩溃，仍返回必含项（上层应向用户提示超预算）
    over = smart_pick("protein", 10.0, items, coupons, required=["M1"])
    check("over-budget required fallback safe", "巨无霸" in over["items"])

    # 15) 低卡严格上限：即便预算宽松（100元），热量仍不超过 tight cap(100)
    lc_tight = smart_pick("lowcal", 100.0, items, coupons, kcal_cap=100)
    check("lowcal respects tight kcal cap", lc_tight["nutrition"]["kcal"] <= 100 + 1e-6)

    # 16) 确定性（save 分支）：相同输入得到相同结果
    a_save = smart_pick("save", 30.0, items, coupons)
    b_save = smart_pick("save", 30.0, items, coupons)
    check("deterministic (save)", a_save == b_save)

    # ---- 一致性守卫：演示层不得与引擎"各说各话"（防文档/演示漂移）----

    # 17) demo/index.html 必须使用与 Python 相同的「约束内组合搜索」，且不得回退为旧贪心
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "demo", "index.html"), encoding="utf-8") as f:
        html = f.read()
    check("demo uses same objective-key search as engine",
          "objectiveKey" in html and "combinations(pool" in html)
    check("demo no longer uses greedy scoring",
          "(it.n.protein+2)/it.price" not in html)

    # 18) demo/sample_run.md 必须与引擎 --demo 输出逐字一致
    from mcsmart import demo as _demo
    with open(os.path.join(root, "demo", "sample_run.md"), encoding="utf-8") as f:
        sample = f.read().strip()
    check("sample_run.md matches engine --demo output", sample == _demo().strip())

    print(f"\n结果：{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
