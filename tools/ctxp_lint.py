#!/usr/bin/env python3

"""CTXP (.ctxp.txt) linter

Purpose:
  - Keep repository examples consistent with the PR8.18 CTXP text specification.
  - Provide a lightweight validator for tool authors.

Design:
  - Strict about structure (HDR/META/event line parsing).
  - Intended to match the authoritative PDF spec (PR8.18) closely.

Exit codes:
  0: ok (no errors)
  1: errors found
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


HDR_RE = re.compile(r"^HDR:(?P<kv>.*)$")
META_RE = re.compile(r"^META:(?P<body>.*)$")

# Event line:
#   #<id>:<type>:(<v1>)?:(<v2>)? [@ <cycle>]?
EVENT_RE = re.compile(
    r"^\s*#(?P<sid>\d{1,3})\s*:\s*(?P<typ>[A-Z0-9_]+)\s*:\s*"
    r"(?P<v1>0x[0-9a-f]+)?\s*:\s*(?P<v2>0x[0-9a-f]+)?\s*"
    r"(?:@\s*(?P<cyc>\d+))?\s*$"
)

META_ENTRY_RE = re.compile(r"#(?P<sid>\d{1,3})=\"(?P<name>(?:\\.|[^\\\"])*)\"")


# (has_v1, has_v2): True = required, False = forbidden, None = optional
EVENT_PAYLOAD_KIND: Dict[str, Tuple[Optional[bool], bool]] = {
    "SYNC": (False, True),
    "BRANCH_TAKEN": (True, True),
    "BRANCH_NOTTAKEN": (True, True),
    "CALL": (True, True),
    "RETURN": (True, True),
    "INTERRUPT": (True, True),
    "RFI": (True, True),
    "MEMWRITE_0": (True, False),
    "MEMWRITE_1": (True, True),
    "MEMWRITE_2": (True, True),
    "MEMWRITE_4": (True, True),
    "MEMWRITE_8": (True, True),
    "MEMREAD_0": (True, False),
    "MEMREAD_1": (True, True),
    "MEMREAD_2": (True, True),
    "MEMREAD_4": (True, True),
    "MEMREAD_8": (True, True),
    "OVERFLOW": (False, False),
    "CONTEXT": (False, True),
    "WALLCLOCK": (False, True),
    "INFO_1": (False, True),
    "INFO_2": (False, True),
    "INFO_3": (False, True),
    # Instrumentation / DAQ events (exporter-synthesized from native ACT-CAP messages).
    # value2 carries packed metadata (context + DirectData tag / counter kind+region).
    "DAQ_DATA": (None, True),     # value1 = data value (optional); value2 = {ctx, tag}
    "DAQ_COUNTER": (True, True),  # value1 = counter value; value2 = {kind, region, tag_hi}
    "DAQ_LAST_PC": (False, True), # value2 = previous PC before exception/interrupt
}

@dataclass
class Issue:
    level: str  # "error" | "warn"
    path: Path
    line_no: int
    message: str


def parse_hdr(line: str, issues: List[Issue], path: Path) -> Dict[str, str]:
    m = HDR_RE.match(line.strip())
    if not m:
        issues.append(Issue("error", path, 1, "Missing or invalid HDR line"))
        return {}

    kv = {}
    body = m.group("kv")
    # very simple k=v parsing (comma separated)
    for part in [p.strip() for p in body.split(",") if p.strip()]:
        if "=" not in part:
            issues.append(Issue("warn", path, 1, f"HDR part not key=value: {part!r}"))
            continue
        k, v = part.split("=", 1)
        kv[k.strip()] = v.strip()

    if kv.get("ver") != "1":
        issues.append(Issue("error", path, 1, f"Unsupported ver={kv.get('ver')!r} (expected '1')"))

    fmt = kv.get("format")
    if fmt != "accemic//ctxp-txt":
        issues.append(Issue("error", path, 1, f"Invalid or missing format={fmt!r} (expected 'accemic//ctxp-txt')"))

    return kv


def unescape_meta_string(s: str) -> Optional[str]:
    # Supports \" and \\ as per spec
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        if i + 1 >= len(s):
            return None
        nxt = s[i + 1]
        if nxt in ['\\', '"']:
            out.append(nxt)
            i += 2
        else:
            # unknown escape
            return None
    return "".join(out)


def parse_meta(line: str, issues: List[Issue], path: Path) -> Dict[int, str]:
    m = META_RE.match(line.strip())
    if not m:
        issues.append(Issue("error", path, 2, "Missing or invalid META line"))
        return {}

    body = m.group("body").strip()
    if not body:
        return {}

    entries = [p.strip() for p in body.split(",") if p.strip()]
    mapping: Dict[int, str] = {}
    for ent in entries:
        mm = META_ENTRY_RE.fullmatch(ent)
        if not mm:
            issues.append(Issue("error", path, 2, f"Invalid META entry: {ent!r}"))
            continue
        sid = int(mm.group("sid"))
        if sid in mapping:
            issues.append(Issue("error", path, 2, f"Duplicate META source id: {sid}"))
            continue
        raw = mm.group("name")
        val = unescape_meta_string(raw)
        if val is None:
            issues.append(Issue("error", path, 2, f"Invalid escape sequence in META name for #{sid}"))
            continue
        if len(val.encode("utf-8")) > 1024:
            issues.append(Issue("warn", path, 2, f"META name for #{sid} exceeds 1024 bytes UTF-8"))
        mapping[sid] = val
    return mapping


def lint_file(path: Path) -> List[Issue]:
    issues: List[Issue] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        issues.append(Issue("error", path, 1, "File must have at least HDR and META lines"))
        return issues

    parse_hdr(lines[0], issues, path)
    meta = parse_meta(lines[1], issues, path)

    last_cycle: Dict[int, Optional[int]] = {}
    after_overflow: Dict[int, bool] = {}

    for idx, raw in enumerate(lines[2:], start=3):
        if not raw.strip():
            issues.append(Issue("warn", path, idx, "Blank line (prefer none in examples)"))
            continue

        m = EVENT_RE.match(raw)
        if not m:
            issues.append(Issue("error", path, idx, f"Invalid event line syntax: {raw!r}"))
            continue

        sid = int(m.group("sid"))
        typ = m.group("typ")
        v1 = m.group("v1")
        v2 = m.group("v2")
        cyc_s = m.group("cyc")
        cyc = int(cyc_s) if cyc_s is not None else None

        if sid > 255:
            issues.append(Issue("error", path, idx, f"source_id out of range (0..255): {sid}"))

        if typ not in EVENT_PAYLOAD_KIND:
            issues.append(Issue("error", path, idx, f"Unknown event type: {typ}"))
            continue

        exp_v1, exp_v2 = EVENT_PAYLOAD_KIND[typ]

        # payload presence checks (True = required, False = forbidden, None = optional)
        if exp_v1 is True and v1 is None:
            issues.append(Issue("error", path, idx, f"{typ} requires value1"))
        if exp_v1 is False and v1 is not None:
            issues.append(Issue("error", path, idx, f"{typ} must not have value1 (use '::{v1}' with empty value1 slot)"))
        if exp_v2 is True and v2 is None:
            issues.append(Issue("error", path, idx, f"{typ} requires value2"))
        if exp_v2 is False and v2 is not None:
            issues.append(Issue("warn", path, idx, f"{typ} should not have value2"))

        # source id appears without name is fine, but warn for examples
        if sid not in meta:
            issues.append(Issue("warn", path, idx, f"source_id #{sid} not present in META mapping"))

        # cycle monotonicity per source (when present)
        if cyc is not None:
            if sid not in last_cycle:
                last_cycle[sid] = cyc
                after_overflow[sid] = False
            else:
                if after_overflow.get(sid, False):
                    # after overflow, allow anything and reset tracking
                    last_cycle[sid] = cyc
                    after_overflow[sid] = False
                else:
                    prev = last_cycle[sid]
                    if prev is not None and cyc < prev:
                        issues.append(Issue("error", path, idx, f"cycle_count decreased for source #{sid}: {prev} -> {cyc}"))
                    last_cycle[sid] = cyc

        if typ == "OVERFLOW":
            after_overflow[sid] = True

    return issues


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help=".ctxp.txt files or directories")
    args = ap.parse_args(argv)

    files: List[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.ctxp.txt")))
        else:
            files.append(path)

    all_issues: List[Issue] = []
    for f in files:
        all_issues.extend(lint_file(f))

    # stable output ordering
    all_issues.sort(key=lambda i: (str(i.path), i.line_no, i.level))
    has_err = False
    for iss in all_issues:
        if iss.level == "error":
            has_err = True
        print(f"{iss.path}:{iss.line_no}: {iss.level}: {iss.message}")

    return 1 if has_err else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
