#!/usr/bin/env python3
"""
PDF -> text source adapter. See references/source-adapters.md.
Primary: PyMuPDF4LLM (fast, CPU-only, zero model) -> structured Markdown (headings/tables).
Fallback: plain PyMuPDF (fitz) text if pymupdf4llm is unavailable.

Usage:
  python3 from_pdf.py <pdf_path> [out=/tmp/sp_source.txt] [--plain]
    (default = structured Markdown, good for 解读/精炼/详细 — preserves chapter structure)
    (--plain = narration-friendly text for 无损版: strips #/**/table pipes)

Install primary: pip install -U pymupdf4llm --break-system-packages
Lossless: only light cleaning (page numbers, blank runs); never deletes body content.
"""
import sys, re

def _strip_md(md):
    out = []
    for line in md.splitlines():
        s = line.rstrip()
        s = re.sub(r'^\s*#{1,6}\s*', '', s)      # heading markers -> keep title text
        s = s.replace('**', '').replace('__', '')
        s = re.sub(r'^\s*[-*]\s+', '', s)        # bullet markers
        if re.fullmatch(r'[\s\-=|]+', s):        # md rule / table separator rows
            continue
        out.append(s)
    return '\n'.join(out)

def extract(path, out="/tmp/sp_source.txt", plain=False):
    try:
        import pymupdf4llm
        text = pymupdf4llm.to_markdown(path)
        if plain:
            text = _strip_md(text)
        engine = "pymupdf4llm"
    except Exception:
        import fitz                              # fallback: plain text
        from collections import Counter
        pages = [p.get_text("text") for p in fitz.open(path)]
        lc = Counter()
        for pg in pages:
            for l in set(x.strip() for x in pg.splitlines() if x.strip()):
                lc[l] += 1
        n = max(1, len(pages))
        boiler = {l for l, c in lc.items() if c >= max(3, n * 0.4) and len(l) <= 40}
        keep = []
        for pg in pages:
            for l in pg.splitlines():
                s = l.strip()
                if s and s not in boiler and not re.fullmatch(r'[-—·\s]*\d{1,4}[-—·\s]*', s):
                    keep.append(s)
                elif not s:
                    keep.append("")
        text = "\n".join(keep)
        text = re.sub(r'([^\n。！？!?：:；;、，,”")』】\)])\n(?=[^\n])', r'\1', text)
        engine = "fitz-fallback"
    # light lossless cleanup
    text = re.sub(r'\b\d{1,3}\s*/\s*\d{1,3}\b', '', text)   # "4 / 42" page markers
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    open(out, "w", encoding="utf-8").write(text)
    return text, engine

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    plain = "--plain" in sys.argv
    if not args:
        print("usage: python3 from_pdf.py <pdf> [out] [--plain]", file=sys.stderr); sys.exit(64)
    out = args[1] if len(args) > 1 else "/tmp/sp_source.txt"
    t, eng = extract(args[0], out, plain=plain)
    print(f"OK engine={eng} chars={len(t)} -> {out}")
