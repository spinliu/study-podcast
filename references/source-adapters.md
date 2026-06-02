# 输入源适配层（Source Adapters）

这个 skill 的内核（脚本生成 → 配音 → 逐字稿 → 回传）与"输入是什么"解耦。
前端挂一个**适配器**，职责只有一个：**把任意来源转成纯文本，写到 `/tmp/sp_source.txt`。**
之后所有步骤都一样。加新模态 = 加一个适配器，内核不动。

## 统一契约

```
adapter(<source>) ->  /tmp/sp_source.txt   # UTF-8 纯文本（正文，去掉无关页眉页脚/图片占位）
```

适配器只负责"取文本"，不负责"理解"。理解/解读由脚本生成那一步（见 script-method.md）完成。

## 适配器清单

| 模态 | 状态 | 脚本 | 说明 |
|---|---|---|---|
| 飞书文档 / wiki | ✅ 已实现 | `scripts/fetch_feishu.mjs <token>` | 最简单。wiki 节点 token 可直接当 docx id |
| PDF（论文/书） | ✅ 已实现 | `scripts/sources/from_pdf.py` | PyMuPDF4LLM 结构化 Markdown(主, 纯CPU秒级) + fitz 兜底; --plain 出朗读文本 |
| ePub（电子书） | 🔲 占位 | `scripts/sources/from_epub.py` | 计划用 ebooklib 解析章节 HTML→文本 |
| PPT（pptx） | 🔲 占位 | `scripts/sources/from_pptx.py` | 计划用 python-pptx 抽每页文本+备注 |
| 网页 URL | 🔲 占位 | （未建） | 计划用 readability 抽正文 |
| 纯文本/Markdown | ✅ 天然支持 | 直接写入 sp_source.txt | 无需适配器 |

## 长文档（书/PPT）的注意事项（未来实现时）

- 超长源（一本书）不要一次性塞进脚本生成。先**分章/分单元**，每单元产一段播客，或先做"全书地图"再按需深挖某章。
- 与"精炼/详细"模式正交：可以"整本书的精炼版"，也可以"某一章的详细版"。
- 成本随字符线性增长，仍是几块钱级，不是瓶颈。

> 当前只留结构与占位。需要哪个模态时，按统一契约实现对应适配器即可。
