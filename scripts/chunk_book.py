#!/usr/bin/env python3
"""
Cut ONE ~30-minute unit out of a cleaned full-book text, at a paragraph boundary,
starting from a given char offset. Used by 无损版 (lossless) mode. See references/lossless-mode.md.

Usage:
  python3 chunk_book.py --text full_clean_text.txt --start 0 --chars 8500 --out /tmp/unit.txt

Prints a JSON object to stdout with: start, end, next_start, end_anchor, next_anchor,
total_chars, unit_chars, progress_pct, done. Writes the unit text to --out.
The orchestrator (see SKILL.md) uses these to build the RESUME ANCHOR + resume_state.json.
"""
import argparse, json, re, sys

SENT_END = "。！？!?…\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--chars", type=int, default=8500, help="target chars per ~30min unit")
    ap.add_argument("--out", default="/tmp/sp_unit.txt")
    ap.add_argument("--anchor-len", type=int, default=34)
    a = ap.parse_args()

    full = open(a.text, encoding="utf-8").read()
    total = len(full)
    start = max(0, min(a.start, total))
    if start >= total:
        print(json.dumps({"done": True, "start": start, "end": start, "next_start": start,
                          "total_chars": total, "unit_chars": 0, "progress_pct": 100.0})); return

    target_end = min(start + a.chars, total)
    # snap forward to the next paragraph boundary (\n) so we end on a clean paragraph;
    # if that overshoots a lot, snap back to the last sentence end before target.
    nl = full.find("\n", target_end)
    if nl != -1 and nl - target_end <= a.chars * 0.4:
        end = nl + 1
    else:
        # find last sentence terminator at/just before target_end
        cut = -1
        for i in range(target_end - 1, start, -1):
            if full[i] in SENT_END:
                cut = i + 1; break
        end = cut if cut > start else target_end
    end = min(end, total)

    unit = full[start:end]
    open(a.out, "w", encoding="utf-8").write(unit)

    def anchor(s):
        s = s.strip().replace("\n", "")
        return s[:a.anchor_len]
    # end anchor = tail of this unit; next anchor = head of remaining
    end_anchor = anchor(unit[-(a.anchor_len + 10):])
    rest = full[end:].lstrip()
    next_anchor = anchor(rest[:a.anchor_len + 10]) if rest else ""

    print(json.dumps({
        "done": end >= total,
        "start": start, "end": end, "next_start": end,
        "total_chars": total, "unit_chars": len(unit),
        "progress_pct": round(end / total * 100, 1),
        "end_anchor": end_anchor, "next_anchor": next_anchor,
        "out": a.out,
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
