# daq: instrumentation / DAQ user-generated events

This example demonstrates **user-generated events**: messages emitted by C-Trace's
ACT-CAP / ACT-ST facility when a user-configured watchpoint/trigger fires. They are
*exporter-synthesized* from native DAQ messages — their occurrence and content come from
user configuration, not from the program's control flow.

The guiding rule is **reuse existing CTXP events wherever the semantics match**; only
three new event types exist for what CTXP cannot otherwise express:

- `DAQ_DATA` — a captured data value and/or packed `{context, DirectData}` metadata.
- `DAQ_COUNTER` — a performance/threshold counter readout.
- `DAQ_LAST_PC` — the previous PC before an exception/interrupt.

Related disassembly: [daq.dis](daq.dis). Source provenance: [_sources/daq.S](_sources/daq.S).

## What the trace shows

| Line(s)                                  | Native DAQ command | Notes |
|------------------------------------------|--------------------|-------|
| `SYNC ::0x80000000`                       | (trace start)      | initial PC |
| `CALL 0x8000000c:0x80000018`              | (control flow)     | call into `measured` |
| `DAQ_DATA` + `MEMWRITE_4`                 | `DATA_DADDR` (store) | a watched 4-byte write at `0x70000040`; the `DAQ_DATA` carries context + tag |
| `DAQ_DATA` + `MEMREAD_0`                  | `DADDR` (load)     | a watched read where only the address was captured |
| `RETURN 0x8000002c:0x8000000e`            | (control flow)     | return from `measured` |
| `DAQ_DATA ::0x0000abcd`                    | `DIRECT_DATA`      | an opaque user tag, no value/context |
| `DAQ_DATA :0x000000ff:…`                  | `DATA`             | a captured data value with context + tag, no address |
| `DAQ_COUNTER :0x00000010:…`               | `DATA_RD`          | 16 read accesses counted for a region, then reset |
| `DAQ_DATA` + `DAQ_LAST_PC` + `SYNC`       | `PC_CURR_LAST`     | at trap handler entry: current PC + the PC before the trap (the `ecall`) |

## Ordering rule

Supplementary DAQ events (`DAQ_DATA`, `DAQ_LAST_PC`) are emitted **immediately before** the
event they qualify ("the triggered event"), on the same source with the same
`cycle_count`. A decoder reads them as qualifiers of the event that follows.

## value2 packing

- `DAQ_DATA` context+tag: `[33:30]=Dtype`, `[29:24]=DSize` (bytes = 2^DSize), `[23:0]=DirectData`.
  Example `0x42123456` = Dtype `STORE` (1), DSize 2 (4 bytes), DirectData `0x123456`.
- `DAQ_COUNTER`: `[20:19]=kind` (0=IFETCH_TH, 1=DATA_RD_TH, 2=DATA_WR, 3=DATA_RD),
  `[18:16]=region`, `[15:0]=DirectData[23:8]`. Example `0x001a00ab` = kind `DATA_RD` (3),
  region 2, tag `0x00ab`.

## Timestamps

- Data accesses (`MEMREAD`/`MEMWRITE` from `DATA_DADDR`/`DADDR`) carry the timestamp of the
  actual access — the DAQ message triggers on it.
- `PC_CURR`, counters, and `PC_CURR_LAST`'s `SYNC` carry the trigger/emission time. The
  `DAQ_LAST_PC` value is retrospective (the instruction before the earlier trap).

The full native-command-to-CTXP mapping is documented in the CTXP specification
(section "Export from Native Traces").
