    .section .text
    .globl _start

# dualcore.S — Minimal dual-hart (core0/core1) RV32I example
# Each hart selects its own code path by reading mhartid and calls a
# hart-specific function in a separate code range. Traps end in a local loop.

_start:
    # Point mtvec to a local hang handler so ecall/traps terminate cleanly
    la      t3, hang
    csrw    mtvec, t3

    # Select per-hart entry based on mhartid (with QEMU: use -smp 2)
    csrr    t0, mhartid          # t0 = 0 for core0, 1 for core1
    beqz    t0, core0_entry      # if hart 0 -> core0
    li      t1, 1
    beq     t0, t1, core1_entry  # if hart 1 -> core1
    j       unknown_hart         # any other hart id -> park

# ------------------------- Core 0 range -------------------------
    .p2align 2
core0_entry:
    # Call a core0-specific function (separate code range)
    call    core0_func

    # Exit via ecall (will jump to hang via mtvec)
    li      a0, 0                # exit code
    li      a7, 93               # SYS_exit on Linux; harmless bare-metal
    ecall

# Simple, leaf function for core0
core0_func:
    li      a0, 0xC0             # observable register change for traces
    ret

# ------------------------- Core 1 range -------------------------
    .p2align 2
core1_entry:
    # Call a core1-specific function (separate code range)
    call    core1_func

    # Exit via ecall (will jump to hang via mtvec)
    li      a0, 0                # exit code
    li      a7, 93
    ecall

# Simple, leaf function for core1
core1_func:
    li      a0, 0xC1             # observable register change for traces
    ret

# ---------------------- Common sinks ---------------------------
unknown_hart:
    wfi
    j       unknown_hart

hang:
    j       hang
