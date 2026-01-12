# basic: single-core control-flow

This example demonstrates a minimal, **single-core** control-flow trace:

- `SYNC` establishes the initial program counter.
- `BRANCH_TAKEN` / `BRANCH_NOTTAKEN` encode conditional branches.
- `CALL` / `RETURN` encode function calls and returns.

Related disassembly: [basic.dis](basic.dis).

Source provenance: [_sources/basic.S](_sources/basic.S).

Notes:

- All addresses are instruction addresses (first byte of the instruction).
- `@ <cycle_count>` is optional, but present here.
