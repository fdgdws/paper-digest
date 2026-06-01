# paper-digest

[English](README.md) | 中文

一个 [Agent Skill](https://www.anthropic.com/news/skills)，将研究论文转化为**结构化的批判性解读**——不是摘要。它同时输出人类可读的 Markdown 报告和机器可读的 JSON 对象，JSON 可以导入笔记数据库或作为下一步 agent 的输入。

它与"帮我总结这篇论文"的区别：摘要是把摘要复述一遍；解读做的是一个敏锐审稿人在五分钟内做的事——指出真正的贡献、定位论文最关键的表格、发现缺失的实验、告诉你能否复现。

## 输出什么

固定 schema 的十段式解读：元数据、一句话总结（TL;DR）、问题与动机、方法、证据（数据集 / 基线 / 引用结果）、提炼的贡献、**优势 / 不足 / 开放性问题的批判**、可复现性评估、与先前工作的定位、延伸阅读。同一内容以 JSON（英文键名）输出，便于组合使用；正文语言跟随用户使用的语言。

实际效果参见 [`examples/`](examples/)，其中是对 IEEE TEVC 2023 论文的真实解读。

## 为什么这么设计

该 skill 采用了 **渐进式加载**——Agent Skill 的标准模式：

```
paper-digest/
├── SKILL.md                  # 工作流 + 输出规范（触发时始终加载）
├── scripts/
│   ├── parse_paper.py        # 确定性 PDF → 信号 + 清洁文本
│   └── check_digest.py       # 客观质量检查（可运行的 eval 门禁）
├── references/
│   ├── reading_lenses.md     # 按论文类型的审读清单（按需加载）
│   └── output_schema.md      # JSON schema + Markdown 模板 + 依据规则
└── evals/
    └── evals.json            # 测试提示词 + 断言
```

模型仅在真正需要时才为参考文件支付 token 成本。确定性工作——提取标题、arXiv ID、DOI、代码链接、章节标题、图表/引用数量——由 Python 完成，而非模型。将**已验证的**信号加上清洁文本喂给模型，才能避免解读中编造结果数字或虚构代码发布链接。

## 快速开始

```bash
# 1. 从 PDF 中提取结构化信息
python scripts/parse_paper.py paper.pdf --out-dir ./out
#    → out/paper.meta.json（已验证的信号）+ out/paper.txt（清洁文本）

# 2. （skill 按照 references/output_schema.md 撰写解读）

# 3. 用客观检查门禁验证输出质量
python scripts/check_digest.py out/paper.digest.json --meta out/paper.meta.json
```

将整个文件夹放入你的 skills 目录即可安装使用。

## 评估——大多数 skill 缺失的部分

`scripts/check_digest.py` 使质量门槛**可运行**。它验证那些无需人工判断即可检查的内容，exit code 非零，可接入 CI：

| 检查项 | 防止的问题 |
|---|---|
| `all_required_sections_present` | 截断/偷懒的输出 |
| `critique_has_strengths_and_weaknesses` | 冒充批判的摘要 |
| `key_results_cite_sources` | 无出处、手摇的结果 |
| `code_claim_matches_parser` | **幻觉出的**代码发布链接（或遗漏真实链接） |
| `*_consistent_with_parser` | 编造的 arXiv ID / DOI |

示例论文的通过运行，以及故意破坏后的被拒运行：

```
[PASS] critique_has_strengths_and_weaknesses  — strengths=4, weaknesses=5
[PASS] code_claim_matches_parser              — digest=False, parser=False
9/9 checks passed.

# 注入一个假的 GitHub 链接并删除所有 weaknesses 后：
[FAIL] critique_has_strengths_and_weaknesses  — strengths=4, weaknesses=0
[FAIL] code_claim_matches_parser              — digest=True, parser=False
7/9 checks passed.   (exit code 1)
```

负向测试很重要：一个永远只通过的 eval 证明不了任何事情。

## 工程笔记

解析器针对真实的 IEEE 双栏期刊 PDF 进行了强化，发现了两个干净的 arXiv 风格论文永远不会暴露的 bug：

- **罗马数字表格。** IEEE 使用 `TABLE I … TABLE VII` 作为表格标签，而 PDF 文本层去掉了空格（`TABLEVII`）。一个只匹配阿拉伯数字、要求有空格的的正则表达式数出了 0/7 个表。修复方式是同时匹配阿拉伯和罗马数字、分隔符可选。
- **页眉过滤中的大小写不敏感 bug。** 页眉过滤器（`^\d+\s+[A-Z]{4,}`，用于丢弃 `186 IEEE TRANSACTIONS…`）编译时使用了 `IGNORECASE`，于是 `[A-Z]{4,}` 也匹配了 `1 Introduction` 的前四个字母，静默删除了真实的章节标题。修复方式是让全大写页眉模式大小写敏感并增加长度守卫。

两个回归问题通过在干净合成论文和密集 IEEE 论文上并排测试得到了覆盖。

## 许可证

MIT — 参见 [LICENSE](LICENSE)。
