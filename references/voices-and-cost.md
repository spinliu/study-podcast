# 音色与成本

## 引擎层级（2026-06-02 定稿，依据见 voice-eval.md）

- **主引擎：MiniMax speech-02-HD**（脚本 `scripts/synthesize_minimax.py`）。锁定参数：女声 `female-shaonv` pitch+1 / happy 为主·问句切 surprised；男声 `male-qn-badao`（磁性）pitch 0 neutral；speed 1.3；逐句情绪。
  - API：`POST https://api.minimaxi.com/v1/t2a_v2`，`Authorization: Bearer <MINIMAX_API_KEY>`（sk-cp- 自带 group，不传 GroupId）。body：`model:"speech-02-hd"` + `voice_setting{voice_id,speed(0.5-2),vol,pitch(-12~12,负=低沉),emotion}` + `audio_setting{sample_rate,format}`。返回 `data.audio` 为 **hex**（`bytes.fromhex`）。emotion 可选 happy/sad/angry/surprised/fearful/neutral 等，可逐句配。
  - 成本：~¥3.5/万字符，**中文 1 汉字=2 字符 → 实际 ~¥7/万汉字**。
- **备份引擎：阿里云百炼 CosyVoice v2**（脚本 `scripts/synthesize.py` / `narrate.py`）。主引擎不可用时兜底，也是"纯省钱"档（¥2/万汉字）。
- 火山豆包：评测过的候选，未设默认（见 voice-eval.md）。

---

## 备份引擎细节：阿里云百炼 DashScope CosyVoice

- SDK：`pip install dashscope --break-system-packages`，`from dashscope.audio.tts_v2 import SpeechSynthesizer`
- 凭据：`DASHSCOPE_API_KEY`（在 ~/zylos/.env）
- 调用：`SpeechSynthesizer(model=MODEL, voice=VOICE).call(text)` 返回 mp3 bytes。
- 超时：单段几秒；整篇按段循环。

### 模型与音色

- **cosyvoice-v2（推荐，更自然/有情绪）** 可用音色（已实测可用）：
  - 女声：`longxiaochun_v2`、`longwan_v2`
  - 男声：`longcheng_v2`、`longshu_v2`、`longhua_v2`
- cosyvoice-v1（较机械，备用）：`longxiaochun`（女）、`longcheng`（男）等。
- 默认配音：女主持 `longxiaochun_v2` × 男嘉宾 `longcheng_v2`。

### 成本（按字符计费）

- CosyVoice 约 **¥2 / 万字符** 量级（信心度：中；精确单价以阿里云控制台账单为准）。
- 实测：精炼版 2757 字 ≈ ¥0.55 / 8.7 分钟；详细版 4948 字 ≈ ¥0.99 / 15.7 分钟。
- 外推：60 分钟 ≈ 1.8 万字 ≈ ¥3.6。**成本不是瓶颈。**

## 朗读语速（实测标定）

- CosyVoice v2 中文朗读约 **540 字/分钟**（实测：8478 字 → 15.6 分钟）。
- 估时长：`分钟 ≈ 字数 / 540`。无损版按此定单元字数（~15min=8500字 / ~30min=16000字）。

## 拼接

- ffmpeg concat demuxer，段间插 0.35s 静音（`anullsrc`）让节奏自然。

## 进阶音色（可选，需额外 key）

- 想要"更像真人随口聊"的质感，可接 MiniMax（需 API Key + GroupID）或火山引擎语音合成（需 App ID + Access Token + cluster）。属可选增强，不影响内核。
