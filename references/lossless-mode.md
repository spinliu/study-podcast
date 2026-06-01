# 无损版（Lossless / 整书朗读）模式

第三种模式，和「精炼版 / 详细版」并列。区别：

| 模式 | 本质 | 内容 | 形态 |
|---|---|---|---|
| 精炼版 | 解读 | 浓缩、改写、深入浅出 | 双人对话，≤10 分钟 |
| 详细版 | 解读 | 逐点展开、举一反三 | 双人对话，跟干货走 |
| **无损版** | **忠实朗读** | **不改写、不浓缩，整本读完** | **单人朗读（有声书），按 30 分钟切单元** |

无损版**不是解读**。只做"朗读友好的轻清洗"：修明显错字/OCR 错误、补必要断句标点、去掉页眉页脚/图注噪声 —— **绝不删改正文内容**。

## 单元切分

- **朗读语速标定（实测，重要）**：CosyVoice v2 中文朗读约 **540 字/分钟**（不是直觉的 ~285）。所以：
  - **~15 分钟/单元 ≈ 8500 字**（默认，`chunk_book.py --chars 8500`）
  - **~30 分钟/单元 ≈ 16000 字**（`chunk_book.py --chars 16000`）
  - 估算音频时长：`分钟 ≈ 字数 / 540`。先和用户确认想要多长的单元，再定 `--chars`。
- **只在自然段落边界切**，绝不切断句子。
- 每单元独立产出：① 逐字稿飞书文档 ② 完整朗读 MP3。

## 朗读

- 默认**单人朗读**，可选男/女声。脚本：`narrate.py --voice <voice> --model cosyvoice-v2`。
- 推荐音色：女 `longxiaochun_v2` / 男 `longshu_v2`。整本书全程**固定同一音色与语速**，保证连贯。

## 断点续传标记（RESUME ANCHOR）—— 格式必须严格一致

每个单元的逐字稿**正文末尾**追加下面这个标记块（人类可读），**同时**写一份机器可读的 `resume_state.json`。两者都更新，缺一不可。任何 agent 接手，只看标记/JSON 就能无歧义续读。

### 人类可读标记（贴在逐字稿结尾）

```
═══════════════════════════════════════
【断点续传标记 · RESUME ANCHOR · v1】
源标识(source_id)：<飞书token / 文件名 / ISBN，能唯一定位本书>
单元(unit)：第 K 单元 / 共 N 单元（N 未知写 "?"）
本单元覆盖(range)：第 START–END 字（占全书 ~PCT%）
结尾锚句(end_anchor)：「<本单元最后一句完整原文，20–40字，逐字>」
下一起点(next_anchor)：「<下一单元第一句完整原文开头，20–40字，逐字>」
朗读参数(voice_params)：model=cosyvoice-v2  voice=longxiaochun_v2  rate=1.0
续读指令(resume_cmd)：从「下一起点」那句开始，按相同 voice_params 朗读约 UNIT_MIN 分钟（≈UNIT_CHARS 字，按 540字/分钟），在自然段落边界收尾，然后写一个新的本标记并更新 resume_state.json。
状态(status)：✅ 本单元完成 ｜ 进度 END/TOTAL（PCT%）｜ 下一单元：第 K+1 单元
═══════════════════════════════════════
```

### 机器可读状态（resume_state.json，每单元覆盖写入）

```json
{
  "schema": "study-podcast.resume/v1",
  "source_id": "<唯一定位本书的串>",
  "source_text_path": "/abs/path/full_clean_text.txt",
  "total_chars": 210000,
  "unit": 3,
  "total_units": 25,
  "covered_range": [16001, 24500],
  "next_start_char": 24501,
  "end_anchor": "<本单元结尾逐字锚句>",
  "next_anchor": "<下一单元起点逐字锚句>",
  "voice_params": { "model": "cosyvoice-v2", "voice": "longxiaochun_v2", "rate": 1.0 },
  "status": "completed",
  "progress_pct": 11.7,
  "deliverables": { "doc_url": "<飞书逐字稿URL>", "mp3_path": "<本单元mp3>" }
}
```

### 字段约定（让续读无歧义）

- **source_id**：必须能唯一定位这本书（飞书 token / 文件名+大小 / ISBN）。换 agent 也认得同一本。
- **next_start_char**：权威的续读起点（基于清洗后全文 `full_clean_text.txt` 的字符下标）。`next_anchor` 是给人核对的逐字锚句，两者必须指向同一处；冲突时以 `next_start_char` + `next_anchor` 双重校验，不一致就停下报错、不硬续。
- **voice_params**：整本书固定不变，确保跨单元音色连贯。续读必须沿用，不得擅自更换。
- **total_units / total_chars**：首单元生成时估算并写入；之后单元沿用。

## 续读流程（任何 agent 接手）

1. 读 `resume_state.json`（或逐字稿结尾的标记块）。
2. 校验 `source_id` 指向的清洗全文存在；定位 `next_start_char`，并用 `next_anchor` 核对该处文本一致。
3. 从该处取约 8500 字（段落边界收尾）→ 生成逐字稿 doc + 朗读 MP3，用**相同 voice_params**。
4. 末尾写新的 RESUME ANCHOR + 覆盖更新 `resume_state.json`。
5. 发回用户（MP3 + doc + 一句进度："第 K 单元，进度 PCT%"）。
6. 若 `next_start_char >= total_chars`：标 `status="finished"`，告知"全书朗读完成"。

## 与输入适配层的关系

无损版尤其依赖"整本书"的输入适配器（PDF/ePub）。当前飞书文档已可；PDF/ePub 见 `source-adapters.md`（预留）。长书务必先转成一份清洗后的 `full_clean_text.txt`，单元切分与 `next_start_char` 都基于它。
