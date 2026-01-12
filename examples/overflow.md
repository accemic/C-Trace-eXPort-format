# overflow: discontinuity + recovery

This example demonstrates an `OVERFLOW` event.

- `OVERFLOW` means the source-local trace buffer wrapped / events were lost.
- After `OVERFLOW`, the decoder must reset per-source state.
- After `OVERFLOW`, the subsequent `cycle_count` restarts from zero (or at least is no longer
  comparable to the previous values).

Related disassembly: [overflow.dis](overflow.dis).

Source provenance: [_sources/overflow.S](_sources/overflow.S).
