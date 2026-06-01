#!/usr/bin/env python3
"""
[PLACEHOLDER · NOT IMPLEMENTED]  epub -> plain text source adapter.

Contract (see references/source-adapters.md):
    from_epub(<path>)  ->  writes UTF-8 body text to /tmp/sp_source.txt

The skill's core pipeline (script -> TTS -> transcript -> deliver) is unchanged;
this adapter only extracts text. Implement when the epub modality is needed.

Planned approach:

    - ebooklib to parse chapter HTML -> text.

"""
import sys

def extract(path: str, out: str = "/tmp/sp_source.txt") -> str:
    raise NotImplementedError("epub adapter is a reserved stub — not implemented in this version")

if __name__ == "__main__":
    print("epub adapter: reserved stub, not implemented", file=sys.stderr)
    sys.exit(64)
