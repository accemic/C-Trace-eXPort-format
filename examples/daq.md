# daq: instrumentation / DAQ user-generated events

Unlike control-flow or memory tracing, **DAQ events have no fixed meaning of their own** —
what gets emitted depends entirely on how the user configured the instrumentation
(watchpoints / probes) in C-Trace's ACT-CAP / ACT-ST facility. A probe fires on some
trigger and emits a *DAQ message* carrying whatever that probe was told to capture.

So this example doesn't show "the" DAQ output; it **mimics a small ACT-CAP setup** with
three probes, to show the handful of building blocks you will actually see:

| Probe | Trigger (in [_sources/daq.S](_sources/daq.S)) | What it captures | CTXP events |
|-------|-----------------------------------------------|------------------|-------------|
| **A** | reaches the store at `0x80000024`             | the current **PC** | `DAQ_DATA`(tag 1) → `SYNC::0x80000024` |
| **B** | the next **data access** (that same store)    | address + value  | `DAQ_DATA`(tag 2) → `MEMWRITE_4:0x70000040:0x2a` |
| **C** | enters the trap handler (`0x8000002e`)        | the **last PC before the trap** + current PC | `DAQ_DATA`(tag 3) → `DAQ_LAST_PC::0x80000012` → `SYNC::0x8000002e` |

Everything else in the trace (the opening `SYNC`, the `CALL`, the `RETURN`) is ordinary
control flow, shown so the probe firings have context.

## The four building blocks

1. **PC sample → `SYNC`.** A probe that reports "where is the core now" maps to a `SYNC`
   with the PC in `target`. Probe A samples the PC at the store (`SYNC::0x80000024`).
2. **Next data access → `MEMREAD`/`MEMWRITE`.** A probe that captures a data access *is* a
   memory access — Probe B's capture of the store becomes `MEMWRITE_4` (address
   `0x70000040`, value `0x2a`). Read/write and size come from the access itself.
3. **Last PC before interrupt/exception → `DAQ_LAST_PC`.** Probe C, at the trap handler,
   reports the instruction that was executing before the trap (`0x80000012`, the `ecall`)
   in a `DAQ_LAST_PC`, followed by a `SYNC` to the current PC (`0x8000002e`, the handler).
4. **Tag (`DirectData`) → `DAQ_DATA`.** Every probe attaches a small user value. Here it is
   used as a **probe id** (`0x000001`, `0x000002`, `0x000003`) so an analyzer knows which
   probe fired. It rides in a `DAQ_DATA` event, emitted **immediately before** the event it
   tags, on the same source and `cycle_count`.

## Reading the trace

```
#0:SYNC::0x80000000           trace start: core at 0x80000000
#0:CALL:0x8000000c:0x80000018 call into measured()
#0:DAQ_DATA::0x000001         probe A's tag (id 1) ...
#0:SYNC::0x80000024           ... reports the current PC
#0:DAQ_DATA::0x000002         probe B's tag (id 2) ...
#0:MEMWRITE_4:0x70000040:0x0000002a  ... captures the store (4 bytes, value 0x2a)
#0:RETURN:0x8000002c:0x8000000e      return from measured()
#0:DAQ_DATA::0x000003         probe C's tag (id 3) ...
#0:DAQ_LAST_PC::0x80000012    ... the PC before the trap (the ecall)
#0:SYNC::0x8000002e           ... and the current PC (trap handler)
```

A probe could equally have been configured with `DirectData = 0`; then no `DAQ_DATA` is
emitted and you just see the bare `SYNC` / `MEMWRITE` / `DAQ_LAST_PC`.

## Other ACT-CAP commands

The remaining commands map the same way (full table in the spec, "Export from Native
Traces"):

- **value-only capture** (a value whose address isn't recorded) → a memory access with the
  address omitted, e.g. `#0:MEMREAD_1::0x000000ff`.
- **address-only capture** → `MEMREAD_0`/`MEMWRITE_0` (address, no value).
- **performance/threshold counters** → `DAQ_COUNTER`, e.g.
  `#0:DAQ_COUNTER:0x00000010:0x001a00ab` (count 16; `value2` packs `kind`, `region`, tag).

## Timestamps

Data accesses carry the timestamp of the actual access (the probe triggers on it). A PC
sample, a counter readout, and probe C's `SYNC` carry the trigger time; the `DAQ_LAST_PC`
value is retrospective (the `ecall` retired before probe C fired).

Related disassembly: [daq.dis](daq.dis).
