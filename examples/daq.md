# daq: instrumentation / DAQ user-generated events

This example demonstrates **user-generated events**: messages emitted by C-Trace's
ACT-CAP / ACT-ST facility when a user-configured watchpoint/trigger fires. They are
*exporter-synthesized* from native DAQ messages — their occurrence and content come from
user configuration, not from the program's control flow.

The guiding rule is **reuse existing CTXP events wherever the semantics match**; only
three new event types exist for what CTXP cannot otherwise express:

- `DAQ_DATA` — a bare 24-bit `DirectData` user tag (no other payload).
- `DAQ_COUNTER` — a performance/threshold counter readout.
- `DAQ_LAST_PC` — the previous PC before an exception/interrupt.

Captured data **values** are not carried by `DAQ_DATA`; they are ordinary
`MEMREAD`/`MEMWRITE` events — and those may now **omit the address** to express a
value-only capture (empty `value1` slot).

Related disassembly: [daq.dis](daq.dis). Source provenance: [_sources/daq.S](_sources/daq.S).

## What the trace shows

| Line(s)                                  | Native DAQ command | Notes |
|------------------------------------------|--------------------|-------|
| `SYNC ::0x80000000`                       | (trace start)      | initial PC |
| `CALL 0x8000000c:0x80000018`              | (control flow)     | call into `measured` |
| `DAQ_DATA ::0x00123456` + `MEMWRITE_4`    | `DATA_DADDR` (store) | a watched 4-byte write at `0x70000040`; `DAQ_DATA` adds only the `DirectData` tag (size/direction are already in `MEMWRITE_4`) |
| `MEMREAD_0 :0x70000040:`                  | `DADDR` (load)     | a watched read where only the address was captured (tag is 0, so no `DAQ_DATA`) |
| `RETURN 0x8000002c:0x8000000e`            | (control flow)     | return from `measured` |
| `DAQ_DATA ::0x0000abcd`                    | `DIRECT_DATA`      | a standalone opaque user tag |
| `MEMREAD_1 ::0x000000ff`                  | `DATA`             | a captured 1-byte value with **no address** (empty `value1`) |
| `DAQ_COUNTER :0x00000010:…`               | `DATA_RD`          | 16 read accesses counted for a region, then reset |
| `DAQ_DATA` + `DAQ_LAST_PC` + `SYNC`       | `PC_CURR_LAST`     | at trap handler entry: tag, the PC before the trap (the `ecall`), and the current PC |

## Optional address on memory events

`MEMREAD_1/2/4/8` and `MEMWRITE_1/2/4/8` may omit the address:

- `#0:MEMWRITE_4:0x70000040:0x0000002a` — address + value (normal access).
- `#0:MEMREAD_1::0x000000ff` — value only, **address omitted** (a captured datum whose
  address is not recorded). In the binary encoding the absent address is the reserved
  sentinel `0xFFFFFFFFFFFFFFFF`.
- `#0:MEMREAD_0:0x70000040:` — address only, no value (size unknown).

## Ordering rule

Supplementary DAQ events (`DAQ_DATA`, `DAQ_LAST_PC`) are emitted **immediately before** the
event they qualify ("the triggered event"), on the same source with the same
`cycle_count`. A decoder reads them as qualifiers of the event that follows.

## value2 packing

- `DAQ_DATA`: `value2` = the 24-bit `DirectData` tag, e.g. `0x00123456`. Nothing else.
- `DAQ_COUNTER`: `[20:19]=kind` (0=IFETCH_TH, 1=DATA_RD_TH, 2=DATA_WR, 3=DATA_RD),
  `[18:16]=region`, `[15:0]=DirectData[23:8]`. Example `0x001a00ab` = kind `DATA_RD` (3),
  region 2, tag `0x00ab`.

## Timestamps

- Data accesses (`MEMREAD`/`MEMWRITE`) carry the timestamp of the actual access — the DAQ
  message triggers on it.
- `DAQ_COUNTER` and `PC_CURR_LAST`'s `SYNC` carry the trigger/emission time. The
  `DAQ_LAST_PC` value is retrospective (the `ecall` retired before the trigger).

The full native-command-to-CTXP mapping is documented in the CTXP specification
(section "Export from Native Traces"). Note the two intentionally-dropped details: the
exact atomic/CSR operation flavor (mapped to read/write) and the width of an address-only
`DADDR` capture (`MEMREAD_0`/`MEMWRITE_0`, "unknown size").
