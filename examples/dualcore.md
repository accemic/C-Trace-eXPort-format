# dualcore: multi-source interleaving + WALLCLOCK

This example demonstrates:

- Two sources (`#0` and `#1`) interleaved in one file.
- Per-source ordering is by `cycle_count` (the `@ ...` value).
- Inter-source ordering is *undefined* unless you add synchronization points.
- `WALLCLOCK` markers provide cross-source anchors for global ordering.

Related disassembly: [dualcore.dis](dualcore.dis).

Source provenance: [_sources/dualcore.S](_sources/dualcore.S).

WALLCLOCK events are global timestamp markers coming from the traced system’s timing/trace
infrastructure (used as cross-source synchronization anchors).
