# WorkBuddy 开发上下文（workbuddy.md）

> 本文件用于核验本项目是否使用 WorkBuddy 真实开发，是「麦当劳程序员节创意开发大赛」WorkBuddy 专项奖励（进榜 + 真实使用 WorkBuddy + 提交本文件 → 3000 积分）的核验材料。可由 WorkBuddy 对话上下文导出。

## 项目信息

- 项目名称：麦门聪明点 · McSmartPick
- 参赛方向：基于麦当劳官方 MCP 的「目标导向智能点餐」Agent Skill
- 技术栈：Python 3（零第三方依赖）+ HTML/JS（离线演示）
- 核心原则：取数交给 MCP，算术交给代码，表达交给 Agent

## 用 WorkBuddy 完成的关键步骤

1. **需求调研**：让 WorkBuddy 检索并梳理比赛规则（报名三步、必备文件清单、Star 排名机制、报名/定榜时间线、奖励档位），确认仓库必须包含 `README.md` / `CONTEST_DECLARATION.md` / `MCP_INTEGRATION.md` / 源码 / `mcp-config.example.json`，并拉取官方 `CONTEST_DECLARATION.md` 原文（一字不改）。
2. **方案设计**：与 WorkBuddy 确定"省钱 / 增肌 / 低卡 / 解馋"四个目标模式，以及"MCP 取数 + 纯函数算账 + Agent 表达"的三层架构，避免大模型口算价格出错。
3. **核心引擎开发**：在 `scripts/mcsmart.py` 中实现目标导向组合优化（贪心 + 预算/热量约束 + 优惠券作用域校验），并用 WorkBuddy 运行测试发现并修复了"优惠券作用域未校验"的 bug（如"甜品满15减5"错误套用到无甜品组合）。
4. **MCP 接入层**：实现零依赖 Streamable HTTP 客户端（`initialize` / `tools/list` / `tools/call`，兼容 JSON 与 SSE 响应），并梳理真实工具清单与踩坑记录（`references/tools.md`）。
5. **可验证交付**：构建 `--demo` 离线模式、`demo/index.html` 交互演示（无需 Token 即可见效果，利于拿 Star）、`tests/test_engine.py` 纯函数测试（10 passed, 0 failed）。
6. **合规与文档**：生成全部必备文件，Token 一律用 `MCD_MCP_TOKEN` 环境变量占位，交易类工具默认需用户确认，不自动下单。

## 复现方式

```bash
# 离线演示（无需 Token）
python scripts/mcsmart.py --demo
# 指定目标与预算
python scripts/mcsmart.py --goal protein --budget 35
# 运行引擎测试
python tests/test_engine.py
# 调用真实麦当劳 MCP（需先设置 MCD_MCP_TOKEN）
python scripts/mcsmart.py --live --goal save --budget 30
```

## 说明

- 本项目由 WorkBuddy 辅助开发；餐品示例数据为公开近似值，仅用于离线复现，正式结果以麦当劳官方实时数据为准。
- 仓库已设为公开，并按官方 Issue 模板提交报名申请。

## 迭代改进记录（自动化每轮增量）

- 2026-10-14：算法增强——将 `smart_pick` 由贪心升级为「约束内组合搜索」（枚举预算/热量/max_items 下所有合法组合，按目标打分取最优），保留 `best_coupon` 作用域与门槛校验。新增 2 个测试（搜索优于贪心、max_items 约束），tests 全部通过（12 passed），`--demo` 输出正常。零第三方依赖、改动仅限 `scripts/mcsmart.py` 与 `tests/test_engine.py`。
- 2026-10-14：测试增强——在 `tests/test_engine.py` 新增 7 个边界用例（空菜单安全、极小预算安全、券不叠加只选最优、满减门槛恰好触发、必含项超预算兜底、低卡严格上限、save 分支确定性），强化回归保护。tests 全部通过（19 passed, 0 failed），`--demo` 输出不变。本轮仅改 `tests/test_engine.py`，核心引擎 `scripts/mcsmart.py` 未动，零第三方依赖。
- 2026-10-14：演示层与引擎对齐（一致性修复）——第 1 轮升级为「约束内组合搜索」后，`demo/index.html` 仍用旧贪心、`demo/sample_run.md` 与 README 示例输出仍是旧数据，三处与 CLI 实际结果不一致。本轮将 `demo/index.html` 的 JS 引擎改写为与 `scripts/mcsmart.py` 同逻辑（objectiveKey 目标排序键 + 预算/热量/件数约束枚举 + 必含项优先与超预算兜底 + 券门槛与作用域校验，DOM 结构与样式未动），并用真实引擎重新生成 `demo/sample_run.md`、同步 README 示例与对话示例、修正 `MCP_INTEGRATION.md` 流程图中「贪心」表述。校验：Node 抽取演示页引擎跑四个目标，输出与 Python 引擎逐项一致（save 24.30/34g、protein 27.00/44g、lowcal 16.20/180kcal、crave 19.00/900kcal），DOM 关键节点无缺失；`tests/test_engine.py` 新增 3 个一致性守卫（演示页采用同款 objectiveKey 组合搜索、不再含旧贪心打分、sample_run.md 与 `--demo` 输出逐字一致），全量 22 passed / 0 failed，`--demo` 正常。零第三方依赖、未改硬性文件名与声明内容、未硬编码 Token。
