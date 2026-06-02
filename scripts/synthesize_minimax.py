#!/usr/bin/env python3
"""
PRIMARY synthesizer: two-host dialogue script -> single MP3 via MiniMax T2A (speech-02-hd).
This is the chosen primary engine (see references/voice-eval.md). CosyVoice (synthesize.py)
is the backup engine.

Input script format: each spoken line is `**【<speaker>】** <text>` (Markdown). Two speakers
map to a female and a male MiniMax voice. Per-line emotion is assigned automatically
(female: surprised on question/surprise markers else happy; male: neutral) for richer dynamics.

Usage:
  python3 synthesize_minimax.py --script script.md --out podcast.mp3 \
      [--model speech-02-hd] [--female-voice female-shaonv] [--male-voice male-qn-badao] \
      [--female-name 小鹿] [--male-name 老唐] [--speed 1.3] \
      [--female-pitch 1] [--male-pitch 0] [--segdir /tmp/mm_segs] [--gap 0.26]

Requires: MINIMAX_API_KEY in env or ~/zylos/.env ; ffmpeg on PATH.
Prints final: DONE dur_sec=.. dur_min=.. size_kb=.. total_chars=.. cost_cny=..
"""
import os, re, sys, json, time, argparse, subprocess, urllib.request

API = "https://api.minimaxi.com/v1/t2a_v2"
# female emotion heuristic: surprise/question markers -> surprised, else happy
SURPRISE = re.compile(r'(等等|居然|竟然|真的吗|啊？|？！|卧槽|天呐|哇[，、]?|吓|没想到|什么？|不会吧)')

def load_key():
    if os.environ.get("MINIMAX_API_KEY"): return os.environ["MINIMAX_API_KEY"]
    p = os.path.expanduser("~/zylos/.env")
    if os.path.exists(p):
        for line in open(p):
            m = re.match(r'^MINIMAX_API_KEY=(.*)$', line.strip())
            if m: return m.group(1).strip()
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="speech-02-hd")
    ap.add_argument("--female-voice", default="female-shaonv")
    ap.add_argument("--male-voice", default="male-qn-badao")
    ap.add_argument("--female-name", default="小鹿")
    ap.add_argument("--male-name", default="老唐")
    ap.add_argument("--speed", type=float, default=1.3)
    ap.add_argument("--female-pitch", type=int, default=1)
    ap.add_argument("--male-pitch", type=int, default=0)
    ap.add_argument("--segdir", default="/tmp/mm_segs")
    ap.add_argument("--gap", type=float, default=0.26)
    ap.add_argument("--delay", type=float, default=1.2, help="seconds between API calls (avoid RPM rate limit)")
    ap.add_argument("--rate-per-10k", type=float, default=7.0, help="CNY per 10k Chinese chars est (HD, 1汉字=2字符)")
    a = ap.parse_args()

    KEY = load_key()
    if not KEY:
        print("ERROR: MINIMAX_API_KEY not set"); sys.exit(1)

    cfg = {a.female_name: dict(voice=a.female_voice, pitch=a.female_pitch, kind="f"),
           a.male_name:   dict(voice=a.male_voice,   pitch=a.male_pitch,   kind="m")}
    pat = re.compile(r'^\*\*【(' + re.escape(a.female_name) + '|' + re.escape(a.male_name) + r')】\*\*\s*(.+)$')
    segs = []
    for line in open(a.script, encoding="utf-8"):
        m = pat.match(line.strip())
        if not m: continue
        text = m.group(2).replace("**", "").replace("*", "").strip()
        if text: segs.append((m.group(1), text))
    if not segs:
        print("ERROR: no dialogue segments (expect '**【name】** text')"); sys.exit(2)

    total_chars = sum(len(t) for _, t in segs)
    print(f"segments={len(segs)} total_chars={total_chars}", flush=True)

    os.makedirs(a.segdir, exist_ok=True)
    sil = os.path.join(a.segdir, "sil.mp3")
    subprocess.run(f"ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t {a.gap} -q:a 9 {sil}",
                   shell=True, capture_output=True)

    def synth(text, voice, pitch, emotion):
        body = {"model": a.model, "text": text,
                "voice_setting": {"voice_id": voice, "speed": a.speed, "vol": 1.0, "pitch": pitch, "emotion": emotion},
                "audio_setting": {"sample_rate": 24000, "format": "mp3"}}
        req = urllib.request.Request(API, data=json.dumps(body).encode(),
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
        r = json.load(urllib.request.urlopen(req, timeout=90))
        if r.get("base_resp", {}).get("status_code") != 0:
            raise RuntimeError(json.dumps(r.get("base_resp"), ensure_ascii=False))
        return bytes.fromhex(r["data"]["audio"])

    def synth_seg(text, voice, pitch, emo):
        # try assigned emotion then neutral; on rate-limit (1002) back off and retry harder
        for e in [emo, "neutral"]:
            for attempt in range(5):
                try:
                    return synth(text, voice, pitch, e)
                except Exception as ex:
                    s = str(ex)
                    if "1002" in s or "rate limit" in s.lower():
                        time.sleep(6 + attempt * 3)          # RPM backoff
                    elif attempt < 4:
                        time.sleep(2)
                    else:
                        break  # try next emotion
        return None

    listpath = os.path.join(a.segdir, "list.txt")
    with open(listpath, "w") as lf:
        for i, (spk, text) in enumerate(segs):
            c = cfg[spk]
            fn = os.path.join(a.segdir, f"seg_{i:03d}.mp3")
            if os.path.exists(fn) and os.path.getsize(fn) > 400:   # resume: reuse existing
                lf.write(f"file '{fn}'\nfile '{sil}'\n"); continue
            emo = ("surprised" if (c["kind"] == "f" and SURPRISE.search(text)) else
                   "happy" if c["kind"] == "f" else "neutral")
            audio = synth_seg(text, c["voice"], c["pitch"], emo)
            if audio is None:
                print(f"seg {i:03d} FAILED"); sys.exit(3)
            open(fn, "wb").write(audio)
            lf.write(f"file '{fn}'\nfile '{sil}'\n")
            if i % 10 == 0: print(f"seg {i:03d} {spk}/{c['voice']} emo={emo}", flush=True)
            time.sleep(a.delay)   # pace to avoid RPM limit

    r = subprocess.run(f"ffmpeg -y -f concat -safe 0 -i {listpath} -c:a libmp3lame -q:a 4 {a.out}",
                       shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print("CONCAT_FAIL", r.stderr[-400:]); sys.exit(4)
    dur = float(subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {a.out}",
                               shell=True, capture_output=True, text=True).stdout.strip() or 0)
    sz = os.path.getsize(a.out)
    cost = total_chars / 10000 * a.rate_per_10k
    print(f"DONE dur_sec={dur:.0f} dur_min={dur/60:.1f} size_kb={sz//1024} total_chars={total_chars} cost_cny={cost:.2f}", flush=True)

if __name__ == "__main__":
    main()
