    .section .text
    .globl _start

# basic.S — minimal RV32I control-flow
#
# Bare-metal example.
# mtvec points to `hang` so that ECALL/traps terminate in a stable way.

_start:
    # Point mtvec at `hang` (e.g. QEMU virt machine, no BIOS)
    la      t3, hang
    csrw    mtvec, t3

    # --- 1) conditional branch (TAKEN) ---
    li      t0, 1
    li      t1, 1
    beq     t0, t1, 1f
    nop

1:  # --- 2) call + return ---
    call    foo

    # --- 3) indirect branch (JALR) ---
    la      t2, target_indirect
    jalr    x0, t2, 0

target_indirect:
    # --- 4) conditional branch (NOT TAKEN) ---
    li      t0, 0
    li      t1, 1
    beq     t0, t1, skipped     # NOT TAKEN -> fall-through

exit:
    # --- 5) exit ---
    li      a0, 0
    li      a7, 93              # SYS_exit (ecall)
    ecall                        # trap via mtvec to hang

hang:
    j       hang

skipped:
    j       exit

foo:
    li      a0, 42
    ret
