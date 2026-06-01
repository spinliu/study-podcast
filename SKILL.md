---
name: study-podcast
description: 把一篇难读的专业论文/文档，变成一段"深入浅出、双人对话"的中文学习播客（MP3）+ 逐字稿飞书文档，用来提升认知带宽。Use when the user wants to turn a paper / report / Feishu doc into an audio podcast or spoken explainer, asks to "做成播客 / 讲解一篇论文 / 生成学习播客 / 把这篇读给我听 / paper to podcast", or shares a hard document and wants it explained深入浅出 in audio. Supports 精炼版 (concise) and 详细版 (detailed) modes.
---

# study-podcast · 学习播客生成

把硬核论文/文档 → 双人对话播客脚本 → CosyVoice 配音 MP3 + 飞书逐字稿。内核是**解读质量**，不是音频。比 NotebookLM 强的地方：脚本完全可定制（用户的语言/聚焦点/带判断地读）、中文母语级、产物直接进飞书系统、逐字稿可编辑、数据不出境。

## 关键第一步：先问模式

接到一篇内容，**先问用户要「精炼版」还是「详细版」**（这是固定流程，通过对话异步问，不阻塞）：
- **精炼版**：~2000 字、一条主线、≤10 分钟。
- **详细版**：逐个模块/概念讲透 + 每个名词用比喻记住 + 举一反三，时长跟干货走。

## 工作流

1. **取源文本**
   - 飞书 doc / wiki：`node scripts/fetch_feishu.mjs <docx或wiki节点token> /tmp/sp_source.txt`（wiki 节点 token 通常可直接当 docx id 用）。
   - PDF / 网页 / 已有文本：自行提取为纯文本。
2. **写脚本**（核心，由你来写，不要外包给摘要工具）
   - 严格按 `references/script-method.md`：5 条质量标准 + 选定模式 + 对话格式。
   - 输出 Markdown，每句台词格式 `**【小鹿】** …`（女声·提问）/ `**【老唐】** …`（男声·讲透）。写到 `/tmp/sp_script.md`。
3. **合成音频**
   ```
   python3 scripts/synthesize.py --script /tmp/sp_script.md --out /tmp/sp_podcast.mp3 \
       --model cosyvoice-v2 --female longxiaochun_v2 --male longcheng_v2 --segdir /tmp/sp_segs
   ```
   末行打印时长/字符数/成本。音色与成本见 `references/voices-and-cost.md`。
4. **逐字稿落飞书**
   ```
   node scripts/feishu_doc.mjs /tmp/sp_script.md "<标题·解读逐字稿> [owner_open_id]"
   ```
   打印飞书文档 URL（已设 tenant-readable + owner full_access）。
5. **回传用户**
   - MP3 用 comm-bridge 所在渠道的发文件能力发送（飞书：`feishu/src/cli.js send-file <chat_id> <mp3>`；c4-send 只能发文本）。
   - 一并发逐字稿文档链接 + 真实成本（字符数/时长/¥）。

## 依赖

- DashScope：`DASHSCOPE_API_KEY`（.env）。SDK：`pip install dashscope --break-system-packages`。
- ffmpeg（拼接）。
- 飞书：`FEISHU_APP_ID/SECRET`（建文档）、`FEISHU_USER_ACCESS_TOKEN`（读文档，docx:document:readonly）。

## 原则

- 脚本只基于源文本，不编造；拿不准标信心度。
- 时长跟干货走，不注水。
- 「带判断地读」那一段不能省 —— 这是和摘要工具的根本区别。

## 进阶（可选）

更自然的真人音色可接 MiniMax / 火山引擎（需各自 key），属增强项，不影响内核。见 `references/voices-and-cost.md`。
