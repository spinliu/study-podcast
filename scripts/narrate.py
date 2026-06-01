#!/usr/bin/env python3
"""
单人朗读：把一段纯文本（无损版的一个单元）合成为一条 MP3。用于 无损版 mode。
与 synthesize.py（双人对话）区分：这里是单一音色、忠实朗读、无说话人标签。

Usage:
  python3 narrate.py --text unit.txt --out unit.mp3 \
      [--voice longxiaochun_v2] [--model cosyvoice-v2] [--segdir /tmp/narr] \
      [--gap 0.25] [--max-chars 400]

Splits text into TTS-friendly chunks at sentence boundaries (<= --max-chars each),
synthesizes each with the SAME voice, concatenates. Prints final:
  DONE dur_sec=.. dur_min=.. size_kb=.. total_chars=.. cost_cny=..
"""
import os, re, sys, time, argparse, subprocess

def load_key():
    if os.environ.get("DASHSCOPE_API_KEY"): return
    p = os.path.expanduser("~/zylos/.env")
    if os.path.exists(p):
        for line in open(p):
            m = re.match(r'^DASHSCOPE_API_KEY=(.*)$', line.strip())
            if m: os.environ["DASHSCOPE_API_KEY"] = m.group(1).strip()

SENT = re.compile(r'[^。！？!?…\n]*[。！？!?…\n]|[^。！？!?…\n]+$')

def split_chunks(text, maxc):
    chunks, cur = [], ""
    for piece in SENT.findall(text):
        piece = piece.strip("\n")
        if not piece.strip():
            continue
        if len(cur) + len(piece) <= maxc:
            cur += piece
        else:
            if cur: chunks.append(cur)
            if len(piece) <= maxc:
                cur = piece
            else:  # a single overlong sentence: hard-split
                for i in range(0, len(piece), maxc):
                    chunks.append(piece[i:i+maxc])
                cur = ""
    if cur: chunks.append(cur)
    return chunks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="longxiaochun_v2")
    ap.add_argument("--model", default="cosyvoice-v2")
    ap.add_argument("--segdir", default="/tmp/sp_narr")
    ap.add_argument("--gap", type=float, default=0.25)
    ap.add_argument("--max-chars", type=int, default=400)
    ap.add_argument("--rate-per-10k", type=float, default=2.0)
    a = ap.parse_args()

    load_key()
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("ERROR: DASHSCOPE_API_KEY not set"); sys.exit(1)
    import dashscope
    from dashscope.audio.tts_v2 import SpeechSynthesizer
    dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]

    text = open(a.text, encoding="utf-8").read()
    chunks = split_chunks(text, a.max_chars)
    total_chars = sum(len(c) for c in chunks)
    print(f"chunks={len(chunks)} total_chars={total_chars}", flush=True)

    os.makedirs(a.segdir, exist_ok=True)
    sil = os.path.join(a.segdir, "sil.mp3")
    subprocess.run(f"ffmpeg -y -f lavfi -i anullsrc=r=22050:cl=mono -t {a.gap} -q:a 9 {sil}",
                   shell=True, capture_output=True)
    listpath = os.path.join(a.segdir, "list.txt")
    with open(listpath, "w") as lf:
        for i, c in enumerate(chunks):
            for attempt in range(3):
                try:
                    audio = SpeechSynthesizer(model=a.model, voice=a.voice).call(c)
                    if audio and len(audio) > 400:
                        fn = os.path.join(a.segdir, f"n_{i:04d}.mp3")
                        open(fn, "wb").write(audio)
                        lf.write(f"file '{fn}'\nfile '{sil}'\n")
                        if i % 10 == 0: print(f"chunk {i}/{len(chunks)}", flush=True)
                        break
                except Exception as e:
                    print(f"chunk {i} attempt{attempt} ERROR: {e}", flush=True); time.sleep(2)
            else:
                print(f"chunk {i} FAILED"); sys.exit(3)

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
