#!/usr/bin/env python3
"""
[PLACEHOLDER · NOT IMPLEMENTED]  pptx -> plain text source adapter.

Contract (see references/source-adapters.md):
    from_pptx(<path>)  ->  writes UTF-8 body text to /tmp/sp_source.txt

The skill's core pipeline (script -> TTS -> transcript -> deliver) is unchanged;
this adapter only extracts text. Implement when the pptx modality is needed.

Planned approach:


    - python-pptx to pull per-slide text + speaker notes.
"""
import sys

def extract(path: str, out: str = "/tmp/sp_source.txt") -> str:
    raise NotImplementedError("pptx adapter is a reserved stub — not implemented in this version")

if __name__ == "__main__":
    print("pptx adapter: reserved stub, not implemented", file=sys.stderr)
    sys.exit(64)
