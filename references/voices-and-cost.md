# 音色与成本

## TTS 引擎：阿里云百炼 DashScope CosyVoice

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

## 拼接

- ffmpeg concat demuxer，段间插 0.35s 静音（`anullsrc`）让节奏自然。

## 进阶音色（可选，需额外 key）

- 想要"更像真人随口聊"的质感，可接 MiniMax（需 API Key + GroupID）或火山引擎语音合成（需 App ID + Access Token + cluster）。属可选增强，不影响内核。
