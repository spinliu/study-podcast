#!/usr/bin/env python3
"""
Synthesize a two-host dialogue script into a single MP3 using Alibaba DashScope CosyVoice TTS.

Input script format: each spoken line is `**【<speaker>】** <text>` (Markdown). Non-matching
lines (headings, quotes, rules) are ignored. Two speakers map to a female and a male voice.

Usage:
  python3 synthesize.py --script script.md --out podcast.mp3 \
      [--model cosyvoice-v2] [--female longxiaochun_v2] [--male longcheng_v2] \
      [--female-name 小鹿] [--male-name 老唐] [--segdir /tmp/segs] [--gap 0.35]

Requires: dashscope SDK (pip install dashscope --break-system-packages), ffmpeg on PATH,
DASHSCOPE_API_KEY in env or in ~/zylos/.env.
Prints a final line: DONE dur_sec=<n> dur_min=<n> size_kb=<n> total_chars=<n> cost_cny=<n>
"""
import os, re, sys, time, argparse, subprocess

def load_key():
    if os.environ.get("DASHSCOPE_API_KEY"): return
    envp = os.path.expanduser("~/zylos/.env")
    if os.path.exists(envp):
        for line in open(envp):
            m = re.match(r'^DASHSCOPE_API_KEY=(.*)$', line.strip())
            if m: os.environ["DASHSCOPE_API_KEY"] = m.group(1).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="cosyvoice-v2")
    ap.add_argument("--female", default="longxiaochun_v2")
    ap.add_argument("--male", default="longcheng_v2")
    ap.add_argument("--female-name", default="小鹿")
    ap.add_argument("--male-name", default="老唐")
    ap.add_argument("--segdir", default="/tmp/sp_segs")
    ap.add_argument("--gap", type=float, default=0.35)
    ap.add_argument("--rate-per-10k", type=float, default=2.0, help="CNY per 10k chars (estimate)")
    a = ap.parse_args()

    load_key()
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("ERROR: DASHSCOPE_API_KEY not set"); sys.exit(1)
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer
    dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]

    voice_of = {a.female_name: a.female, a.male_name: a.male}
    pat = re.compile(r'^\*\*【(' + re.escape(a.female_name) + '|' + re.escape(a.male_name) + r')】\*\*\s*(.+)$')
    segs = []
    for line in open(a.script, encoding="utf-8"):
        m = pat.match(line.strip())
        if not m: continue
        text = m.group(2).replace("**", "").replace("*", "").strip()
        if text: segs.append((m.group(1), text))
    if not segs:
        print("ERROR: no dialogue segments found (expect '**【name】** text' lines)"); sys.exit(2)

    total_chars = sum(len(t) for _, t in segs)
    print(f"segments={len(segs)} total_chars={total_chars}", flush=True)

    os.makedirs(a.segdir, exist_ok=True)
    sil = os.path.join(a.segdir, "sil.mp3")
    subprocess.run(f"ffmpeg -y -f lavfi -i anullsrc=r=22050:cl=mono -t {a.gap} -q:a 9 {sil}",
                   shell=True, capture_output=True)
    listpath = os.path.join(a.segdir, "list.txt")
    with open(listpath, "w") as lf:
        for i, (spk, text) in enumerate(segs):
            voice = voice_of[spk]
            for attempt in range(3):
                try:
                    audio = SpeechSynthesizer(model=a.model, voice=voice).call(text)
                    if audio and len(audio) > 500:
                        fn = os.path.join(a.segdir, f"seg_{i:03d}.mp3")
                        open(fn, "wb").write(audio)
                        lf.write(f"file '{fn}'\nfile '{sil}'\n")
                        print(f"seg {i:03d} {spk}/{voice} chars={len(text)}", flush=True)
                        break
                except Exception as e:
                    print(f"seg {i:03d} attempt{attempt} ERROR: {e}", flush=True); time.sleep(2)
            else:
                print(f"seg {i:03d} FAILED"); sys.exit(3)

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
