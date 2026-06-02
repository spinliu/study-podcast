#!/usr/bin/env python3
"""
PRIMARY narrator for 无损版 (lossless full-book reading): single-voice MiniMax T2A
(speech-02-hd). Reads a plain-text unit, splits into sentence chunks, synthesizes each,
concatenates. Resumable + RPM rate-limit backoff. CosyVoice narrate.py is the backup.

Usage:
  python3 narrate_minimax.py --text unit.txt --out unit.mp3 \
      [--voice male-qn-badao] [--pitch 0] [--speed 1.3] [--emotion neutral] \
      [--model speech-02-hd] [--segdir /tmp/mmn] [--gap 0.25] [--max-chars 300] [--delay 1.2]
Requires MINIMAX_API_KEY in env or ~/zylos/.env ; ffmpeg.
"""
import os, re, sys, json, time, argparse, subprocess, urllib.request
API="https://api.minimaxi.com/v1/t2a_v2"
SENT=re.compile(r'[^。！？!?…\n]*[。！？!?…\n]|[^。！？!?…\n]+$')

def load_key():
    if os.environ.get("MINIMAX_API_KEY"): return os.environ["MINIMAX_API_KEY"]
    p=os.path.expanduser("~/zylos/.env")
    if os.path.exists(p):
        for line in open(p):
            m=re.match(r'^MINIMAX_API_KEY=(.*)$',line.strip())
            if m: return m.group(1).strip()

def split_chunks(text,maxc):
    out,cur=[],""
    for piece in SENT.findall(text):
        piece=piece.strip("\n")
        if not piece.strip(): continue
        if len(cur)+len(piece)<=maxc: cur+=piece
        else:
            if cur: out.append(cur)
            if len(piece)<=maxc: cur=piece
            else:
                for i in range(0,len(piece),maxc): out.append(piece[i:i+maxc])
                cur=""
    if cur: out.append(cur)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--text",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--voice",default="male-qn-badao"); ap.add_argument("--pitch",type=int,default=0)
    ap.add_argument("--speed",type=float,default=1.3); ap.add_argument("--emotion",default="neutral")
    ap.add_argument("--model",default="speech-02-hd"); ap.add_argument("--segdir",default="/tmp/mmn")
    ap.add_argument("--gap",type=float,default=0.25); ap.add_argument("--max-chars",type=int,default=300)
    ap.add_argument("--delay",type=float,default=1.2)
    ap.add_argument("--rate-per-10k",type=float,default=7.0)
    a=ap.parse_args()
    KEY=load_key()
    if not KEY: print("ERROR: MINIMAX_API_KEY not set"); sys.exit(1)
    chunks=split_chunks(open(a.text,encoding="utf-8").read(),a.max_chars)
    total=sum(len(c) for c in chunks)
    print(f"chunks={len(chunks)} total_chars={total}",flush=True)
    os.makedirs(a.segdir,exist_ok=True)
    sil=os.path.join(a.segdir,"sil.mp3")
    subprocess.run(f"ffmpeg -y -f lavfi -i anullsrc=r=24000:cl=mono -t {a.gap} -q:a 9 {sil}",shell=True,capture_output=True)
    def synth(text):
        body={"model":a.model,"text":text,"voice_setting":{"voice_id":a.voice,"speed":a.speed,"vol":1.0,"pitch":a.pitch,"emotion":a.emotion},"audio_setting":{"sample_rate":24000,"format":"mp3"}}
        req=urllib.request.Request(API,data=json.dumps(body).encode(),headers={"Authorization":"Bearer "+KEY,"Content-Type":"application/json"})
        r=json.load(urllib.request.urlopen(req,timeout=90))
        if r.get("base_resp",{}).get("status_code")!=0: raise RuntimeError(json.dumps(r.get("base_resp"),ensure_ascii=False))
        return bytes.fromhex(r["data"]["audio"])
    lf=open(os.path.join(a.segdir,"list.txt"),"w")
    for i,c in enumerate(chunks):
        fn=os.path.join(a.segdir,f"n_{i:04d}.mp3")
        if os.path.exists(fn) and os.path.getsize(fn)>400:
            lf.write(f"file '{fn}'\nfile '{sil}'\n"); continue
        ok=False
        for attempt in range(6):
            try:
                open(fn,"wb").write(synth(c)); ok=True; break
            except Exception as ex:
                s=str(ex)
                time.sleep((6+attempt*3) if ("1002" in s or "rate limit" in s.lower()) else 2)
        if not ok: print(f"chunk {i} FAILED"); sys.exit(3)
        lf.write(f"file '{fn}'\nfile '{sil}'\n")
        if i%10==0: print(f"chunk {i}/{len(chunks)}",flush=True)
        time.sleep(a.delay)
    lf.close()
    r=subprocess.run(f"ffmpeg -y -f concat -safe 0 -i {a.segdir}/list.txt -c:a libmp3lame -q:a 4 {a.out}",shell=True,capture_output=True,text=True)
    if r.returncode!=0: print("CONCAT_FAIL",r.stderr[-300:]); sys.exit(4)
    dur=float(subprocess.run(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {a.out}",shell=True,capture_output=True,text=True).stdout.strip() or 0)
    print(f"DONE dur_sec={dur:.0f} dur_min={dur/60:.1f} size_kb={os.path.getsize(a.out)//1024} total_chars={total} cost_cny={total/10000*a.rate_per_10k:.2f}",flush=True)

if __name__=="__main__": main()
