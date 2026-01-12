    .section .text
    .globl _start

# interrupt_rfi.S — RV32I trap-based approximation of INTERRUPT/RFI
#
# Real asynchronous interrupts require a timer/peripheral setup.
# For a deterministic, self-contained example we trigger an exception via `ecall`.
# A CTXP exporter may choose to represent trap entry/exit as `INTERRUPT`/`RFI` events.

_start:
    la      t0, trap_vector
    csrw    mtvec, t0

    # Some control-flow before the trap
    li      t1, 1
    beqz    t1, after_trap
    nop

    # Trigger exception -> enters trap handler
    ecall

after_trap:
    # Continue after returning from trap
    li      a0, 0
    li      a7, 93
    ecall

hang:
    j       hang

# --- Trap handler ---
trap_vector:
    # In a real system, mepc contains the faulting PC.
    # We advance it by 4 so we return to the instruction after `ecall`.
    csrr    t2, mepc
    addi    t2, t2, 4
    csrw    mepc, t2

    mret
