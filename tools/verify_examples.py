#!/usr/bin/env python3

"""Verify that example CTXP traces look plausible with their corresponding disassembly.

This is a *sanity check* for this repository's examples, not a full semantic trace verifier.

Checks:
  - For each examples/<name>.ctxp.txt, a matching examples/<name>.dis exists.
  - All hex addresses referenced by the trace (value1/value2 fields) appear in the .dis text.

Limitations:
  - Many events are exporter-synthesized (WALLCLOCK, CONTEXT, INFO_*) and/or may reference
    non-code addresses (MEMREAD/MEMWRITE). This script only checks addresses that look like
    code addresses (0x8........) by default.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


HEX_RE = re.compile(r"0x[0-9a-f]+")


def extract_trace_hex_addrs(ctxp_text: str) -> set[str]:
    addrs = set(HEX_RE.findall(ctxp_text))
    # Filter to typical code region used in our examples (0x8000....).
    return {a for a in addrs if a.startswith("0x8")}


def main() -> int:
    examples_dir = Path("examples")
    ok = True

    for ctxp_path in sorted(examples_dir.glob("*.ctxp.txt")):
        name = ctxp_path.name.replace(".ctxp.txt", "")
        dis_path = examples_dir / f"{name}.dis"
        if not dis_path.exists():
            print(f"ERROR: missing disassembly for {ctxp_path}: expected {dis_path}")
            ok = False
            continue

        trace = ctxp_path.read_text(encoding="utf-8")
        dis = dis_path.read_text(encoding="utf-8", errors="replace")

        addrs = extract_trace_hex_addrs(trace)
        missing = [a for a in sorted(addrs) if a[2:] not in dis and a not in dis]
        if missing:
            # This indicates either:
            #  - the example trace is not derived from this .S/.elf,
            #  - or the address map differs.
            print(f"WARN: {name}: {len(missing)} trace code addresses not found in {dis_path}")
            for a in missing[:25]:
                print(f"  - {a}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
