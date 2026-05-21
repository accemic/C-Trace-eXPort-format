    .section .text
    .globl _start

# daq.S — provenance source for examples/daq.ctxp.txt
#
# This program is the code basis for the "instrumentation / DAQ" example. The DAQ events
# in the trace are *exporter-synthesized* from native ACT-CAP messages (they are triggered
# by user-configured watchpoints, not by the control flow itself), but the program
# counters and the data-access instruction they reference are real addresses from this
# code, so the example stays consistent with its disassembly.
#
# Notes:
# - The data address (0x70000040) is an arbitrary example bus/MMIO address.
# - The ecall models a trap so that "previous PC before exception" (DAQ_LAST_PC) has a
#   concrete meaning at the handler entry.

_start:
    # Point traps/ecall at the trap handler
    la      t3, trap_handler
    csrw    mtvec, t3

    # --- a measured function call (PC_CURR watchpoint fires inside) ---
    call    measured

    # --- trigger a trap so the handler sees a "last PC before exception" ---
    li      a7, 93              # SYS_exit
    ecall                       # -> trap_handler (mtvec)

hang:
    j       hang

measured:
    # A 32-bit store followed by a load at a watched data address.
    # DATA_DADDR / DADDR watchpoints fire on these accesses.
    li      t0, 0x70000040
    li      t1, 0x2a
    sw      t1, 0(t0)           # watched write
    lw      a0, 0(t0)           # watched read
    ret

trap_handler:
    # Handler entry: a PC_CURR_LAST watchpoint here captures both this PC and the
    # last instruction address before the trap (the ecall above).
    j       hang
