    .section .text
    .globl _start

# memory.S — RV32I loads/stores to demonstrate MEMREAD/MEMWRITE events
#
# Notes:
# - The addresses used here are arbitrary example bus/MMIO addresses.
# - On real hardware, these would need to be backed by a memory region or MMIO device.
# - This file is meant as a *provenance* source for the example trace format, not as a
#   fully portable program for all targets.

_start:
    # Point traps/ecall to a local hang handler
    la      t3, hang
    csrw    mtvec, t3

    # Base addresses used in examples/memory.ctxp.txt
    li      t0, 0x70000010
    li      t1, 0x70000020
    li      t2, 0x70000024

    # --- 32-bit read/write at 0x70000010 ---
    lw      a0, 0(t0)
    li      a1, 0x2b
    sw      a1, 0(t0)

    # --- 16-bit read/write at 0x70000020 ---
    lhu     a2, 0(t1)
    li      a3, 0xaa
    sh      a3, 0(t1)

    # --- 8-bit read/write at 0x70000024 ---
    lbu     a4, 0(t2)
    li      a5, 0x01
    sb      a5, 0(t2)

    # Exit via ecall -> hang
    li      a0, 0
    li      a7, 93
    ecall

hang:
    j       hang
