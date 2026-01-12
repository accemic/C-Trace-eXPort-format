# memory: MEMREAD/MEMWRITE events

Demonstrates memory access events (RV32-friendly sizes):

- `MEMREAD_N:addr:value` / `MEMWRITE_N:addr:value`
- `N` is 1, 2, or 4 bytes in this example (RV32)
  
Note: `MEMREAD_0` / `MEMWRITE_0` exist in CTXP to represent accesses where the address is
known but the data is unknown/not recorded. This particular example focuses on sizes where
the data is present.

Note: the endianness of the value follows the traced target’s endianness.

Source provenance: [_sources/memory.S](_sources/memory.S).
