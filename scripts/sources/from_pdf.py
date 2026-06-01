#!/usr/bin/env python3
"""
[PLACEHOLDER · NOT IMPLEMENTED]  pdf -> plain text source adapter.

Contract (see references/source-adapters.md):
    from_pdf(<path>)  ->  writes UTF-8 body text to /tmp/sp_source.txt

The skill's core pipeline (script -> TTS -> transcript -> deliver) is unchanged;
this adapter only extracts text. Implement when the pdf modality is needed.

Planned approach:
    - pymupdf / pdfplumber to extract body text; for books, split by chapter first.


"""
import sys

def extract(path: str, out: str = "/tmp/sp_source.txt") -> str:
    raise NotImplementedError("pdf adapter is a reserved stub — not implemented in this version")

if __name__ == "__main__":
    print("pdf adapter: reserved stub, not implemented", file=sys.stderr)
    sys.exit(64)
