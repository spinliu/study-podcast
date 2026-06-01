#!/usr/bin/env python3
"""
PDF -> cleaned plain text source adapter (无损版/lossless input). See references/source-adapters.md.
Contract:  python3 from_pdf.py <pdf_path> [out=/tmp/sp_source.txt]
Light cleaning only (lossless): join hard-wrapped lines, drop page numbers / repeated
running headers-footers, collapse blank runs. Does NOT summarize or delete body content.
Requires PyMuPDF (fitz).
"""
import sys, re
from collections import Counter

def extract(path, out="/tmp/sp_source.txt"):
    import fitz
    doc = fitz.open(path)
    pages = [p.get_text("text") for p in doc]

    # detect repeated running header/footer lines (appear on many pages) and drop them
    line_counter = Counter()
    for pg in pages:
        for l in set(x.strip() for x in pg.splitlines() if x.strip()):
            line_counter[l] += 1
    n = max(1, len(pages))
    boiler = {l for l, c in line_counter.items() if c >= max(3, n * 0.4) and len(l) <= 40}

    out_paras = []
    for pg in pages:
        kept = []
        for l in pg.splitlines():
            s = l.strip()
            if not s:
                kept.append("")
                continue
            if s in boiler:
                continue
            if re.fullmatch(r'[-—·\s]*\d{1,4}[-—·\s]*', s):  # bare page number
                continue
            kept.append(s)
        out_paras.append("\n".join(kept))

    text = "\n".join(out_paras)
    # join lines hard-wrapped mid-sentence (line not ending in sentence/closing punctuation)
    text = re.sub(r'([^\n。！？!?：:；;、，,”")』】\)])\n(?=[^\n])', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    open(out, "w", encoding="utf-8").write(text)
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 from_pdf.py <pdf> [out]", file=sys.stderr); sys.exit(64)
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/sp_source.txt"
    t = extract(sys.argv[1], out)
    print(f"OK chars={len(t)} -> {out}")
