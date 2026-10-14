# 麦门聪明点 · McSmartPick

> 基于 **麦当劳官方 MCP（https://mcp.mcd.cn）** 的「目标导向智能点餐」Agent Skill。
> 一句话：告诉它你的 **目标（省钱 / 增肌 / 低卡 / 解馋）+ 预算**，它调用麦当劳 MCP 拉取实时菜单与优惠券，用**代码算**出最优组合，再把结果**讲成人话**给你。

本项目为 **麦当劳中国 1024 程序员节创意开发大赛** 参赛作品（官方仓库 `M-China/mcd-developer-innovation-challenge`）。非麦当劳官方产品，与麦当劳官方无隶属关系。

---

## 项目介绍

点餐时我们常卡在三个问题：吃什么、怎么点最划算、营养够不够。大模型擅长"说人话"，但不擅长"算价格"——让它口算套餐组合，十次有八次算错。

**麦门聪明点**把这件事拆成三层（也是本项目的核心设计原则）：

| 层 | 谁来做 | 说明 |
|---|---|---|
| 取数 | 麦当劳 MCP | 实时菜单、营养、门店券、活动日历 |
| 算术 | 本项目代码（纯函数） | 在预算与目标约束下做组合优化，**可复现、可测试** |
| 表达 | Agent / SKILL.md | 把"省了多少、为什么这么搭"讲成人话 |

四个目标模式：

- **省钱 save**：预算内拿到最饱腹组合，叠加最优券后总价最低。
- **增肌高蛋白 protein**：预算内最大化蛋白质总量。
- **低卡控糖 lowcal**：预算内、热量上限内最大化"蛋白/热量"比。
- **解馋满足 crave**：预算内最大化"解馋满足度"。

---

## 安装方法

### 方式一：作为 WorkBuddy / 任意 MCP 客户端 Skill 使用（推荐参赛路径）

1. 领取麦当劳 MCP Token：登录 https://open.mcd.cn/mcp ，手机号验证后在「控制台」激活并复制 Token（免费）。
2. 按 `mcp-config.example.json` 配置 MCP（Token 用环境变量占位，切勿硬编码）。
3. 把本仓库克隆到本地，在 WorkBuddy 中加载 `SKILL.md` 即可对话式使用：
   > "我想增肌，预算 35 块，帮我点一份"

### 方式二：命令行直接跑（零依赖，无需 Token 也能演示）

```bash
# 需要 Python 3.8+
python scripts/mcsmart.py --demo          # 离线演示四个目标
python scripts/mcsmart.py --goal protein --budget 35   # 指定目标与预算
python scripts/mcsmart.py --live --goal save --budget 30   # 调用真实 MCP（需 Token）
```

环境变量：`MCD_MCP_TOKEN`（live 模式使用，也可用 `--token` 传入）。

---

## 使用示例

**离线（无需 Token）：**

```text
【目标：增肌高蛋白 ｜ 预算 ¥35】
  推荐搭配：板烧鸡腿堡 + 猪柳麦满分
  原价 ¥35.00，使用「满30减8」立减 ¥8.00
  👉 实付 ¥27.00，共省 ¥8.00（约 23%）
  营养参考：750.0 kcal ｜ 蛋白 44.0g ｜ 脂肪 34.0g ｜ 碳水 68.0g
```

**对话式（WorkBuddy + 真实 MCP）：**

> 用户：我想吃麦当劳，预算 30，要低卡的
> 麦门聪明点：拉取门店菜单与券 → 计算 →
> "推荐 田园脆鸡沙拉，实付 ¥16.20，约 180 kcal、蛋白 12g，比单点省 10%。"

完整离线样例见 `demo/sample_run.md`，可交互网页演示见 `demo/index.html`（**无需 Token**）。

---

## 目标用户

- **打工人 / 学生**：想吃麦当劳但不想翻 App 比价、算热量的人，核心诉求是**省钱、省时间、吃得明白**。
- **健身 / 控糖人群**：需要按蛋白质或热量规划餐食的人。
- **Agent / MCP 开发者**：想要一个接入真实商业 MCP 的参考实现（零依赖 Streamable HTTP 客户端 + SSE 解析 + 组合优化引擎 + 优惠券作用域处理）。

---

## 目录结构

```
mcd-smartpick/
├── README.md                  # 本文件
├── CONTEST_DECLARATION.md     # 参赛声明（官方原文，一字不改）
├── MCP_INTEGRATION.md         # MCP Server / Tool / 调用流程 / 业务价值
├── SKILL.md                   # 技能主体（Agent 运行时加载）
├── mcp-config.example.json    # 脱敏配置（仅环境变量占位）
├── workbuddy.md               # WorkBuddy 开发对话上下文（3000 积分核验）
├── references/
│   └── tools.md               # 真实工具清单与注意事项
├── scripts/
│   └── mcsmart.py             # 零依赖 MCP 客户端 + 聪明点引擎 + 离线演示 + CLI
├── demo/
│   ├── index.html             # 可交互网页演示（无需 Token）
│   └── sample_run.md          # 离线 CLI 演示输出样本
└── tests/
    └── test_engine.py         # 引擎纯函数测试（零依赖）
```

---

## 冲奖小贴士

榜单按 GitHub **Star 数**定名次（Star > 0 才进榜）。让评委/访客不填 Token 也能立刻看到效果是第一关：本项目提供 `--demo` 离线模式与 `demo/index.html` 交互页，打开即懂、打开即跑。

---

## 免责声明

参赛项目为麦当劳程序员节创意开发大赛参赛作品，由参赛者独立开发，非麦当劳官方产品。项目输出仅供参考，不构成医疗、营养或其他专业建议；餐品信息、价格及供应状态以麦当劳官方渠道的实时结果为准。
