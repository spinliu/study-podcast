---
name: study-podcast
description: 把一篇难读的专业论文/文档，变成一段"深入浅出、双人对话"的中文学习播客（MP3）+ 逐字稿飞书文档，用来提升认知带宽。Use when the user wants to turn a paper / report / Feishu doc into an audio podcast or spoken explainer, asks to "做成播客 / 讲解一篇论文 / 生成学习播客 / 把这篇读给我听 / paper to podcast", or shares a hard document and wants it explained深入浅出 in audio. Supports 精炼版 (concise) and 详细版 (detailed) modes.
---

# study-podcast · 学习播客生成

把硬核论文/文档 → 双人对话播客脚本 → CosyVoice 配音 MP3 + 飞书逐字稿。内核是**解读质量**，不是音频。比 NotebookLM 强的地方：脚本完全可定制（用户的语言/聚焦点/带判断地读）、中文母语级、产物直接进飞书系统、逐字稿可编辑、数据不出境。

## 关键第一步：先问模式

接到一篇内容，**先问用户要哪种模式**（这是固定流程，通过对话异步问，不阻塞）：
- **精炼版**：~2000 字、一条主线、≤10 分钟。（解读，双人对话）
- **详细版**：逐个模块/概念讲透 + 每个名词用比喻记住 + 举一反三，时长跟干货走。（解读，双人对话）
- **无损版**：忠实完整朗读整本书/长文，**不改写不浓缩**，按时长切单元（默认 ~15 分钟/8500字，可选 ~30 分钟/16000字；CosyVoice 实测约 540字/分钟），每单元出逐字稿+朗读MP3，并带断点续传标记。**先问用户想要多长的单元。**（单人朗读，详见 `references/lossless-mode.md`）

## 工作流

1. **取源文本**
   - 飞书 doc / wiki：`node scripts/fetch_feishu.mjs <docx或wiki节点token> /tmp/sp_source.txt`（wiki 节点 token 通常可直接当 docx id 用）。
   - PDF / 网页 / 已有文本：自行提取为纯文本。
2. **写脚本**（核心，由你来写，不要外包给摘要工具）
   - 严格按 `references/script-method.md`：5 条质量标准 + 选定模式 + 对话格式。
   - 输出 Markdown，每句台词格式 `**【小鹿】** …`（女声·提问）/ `**【老唐】** …`（男声·讲透）。写到 `/tmp/sp_script.md`。
3. **合成音频** — **主引擎 MiniMax speech-02-HD**（默认，最自然；选型依据见 `references/voice-eval.md`）：
   ```
   python3 scripts/synthesize_minimax.py --script /tmp/sp_script.md --out /tmp/sp_podcast.mp3 \
       --female-voice female-shaonv --male-voice male-qn-badao --speed 1.3 \
       --female-pitch 1 --male-pitch 0 --segdir /tmp/sp_segs
   ```
   （女声以 happy 为主、问句自动切 surprised；男声磁性 neutral；逐句情绪。需 MINIMAX_API_KEY。）
   **备份引擎**（主引擎余额不足/故障时，或纯省钱）：CosyVoice v2 →
   `python3 scripts/synthesize.py --script ... --model cosyvoice-v2 --female longxiaochun_v2 --male longcheng_v2`
   末行均打印时长/字符数/成本。音色与成本见 `references/voices-and-cost.md`。
4. **逐字稿落飞书**
   ```
   node scripts/feishu_doc.mjs /tmp/sp_script.md "<标题·解读逐字稿> [owner_open_id]"
   ```
   打印飞书文档 URL（已设 tenant-readable + owner full_access）。
5. **回传用户**
   - MP3 用 comm-bridge 所在渠道的发文件能力发送（飞书：`feishu/src/cli.js send-file <chat_id> <mp3>`；c4-send 只能发文本）。
   - 一并发逐字稿文档链接 + 真实成本（字符数/时长/¥）。

## 无损版工作流（整书朗读 · 断点续传）

完整规范见 `references/lossless-mode.md`（含**断点续传标记格式**，必须严格照写）。要点：

1. **取全文** → 清洗成一份 `full_clean_text.txt`（轻清洗：修错字/补断句/去页眉页脚，**不删正文**）。记下 `source_id`（能唯一定位本书）。
2. **续读判断**：若已有 `resume_state.json`，读它拿 `next_start_char` + voice_params；否则从 0 开始、首单元估算 `total_units`。
3. **切一个单元**：`python3 scripts/chunk_book.py --text full_clean_text.txt --start <next_start_char> --chars 8500 --out /tmp/sp_unit.txt`（在段落边界切，输出 end/next_start/end_anchor/next_anchor）。
4. **朗读**：`python3 scripts/narrate.py --text /tmp/sp_unit.txt --out /tmp/sp_unit_K.mp3 --voice longxiaochun_v2 --model cosyvoice-v2`（整本书固定同一音色/语速）。
5. **逐字稿**：在单元文本末尾追加 **RESUME ANCHOR 标记块**（格式见 lossless-mode.md），再 `node scripts/feishu_doc.mjs` 落飞书文档。
6. **写状态**：覆盖更新 `resume_state.json`（schema=study-podcast.resume/v1）。
7. **回传**：MP3 + 逐字稿链接 + 一句进度（"第 K 单元，进度 PCT%"）。`next_start_char >= total_chars` 时标 `finished`，告知"全书朗读完成"。

> 续传契约：另一个 agent 接手时，只读 `resume_state.json`（或逐字稿结尾标记），用 `next_start_char`+`next_anchor` 双重校验定位，沿用相同 voice_params 续读下一个 30 分钟。两者不一致就停下报错，不硬续。

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
