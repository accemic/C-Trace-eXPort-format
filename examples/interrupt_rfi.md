# interrupt_rfi: interrupt entry + return-from-interrupt

Demonstrates exceptional control-flow:

- `INTERRUPT:origin:target` means the core reached `target` because of an interrupt.
- `RFI:origin:target` marks returning from interrupt.

The exact interrupt handler contents are typically not traced; CTXP captures the control-flow
transition points.

Source provenance: [_sources/interrupt_rfi.S](_sources/interrupt_rfi.S).
