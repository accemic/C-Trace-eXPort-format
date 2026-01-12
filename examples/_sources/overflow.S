    .section .text
    .globl _start

# overflow.S — Single-core RV32I demo with indirect-loop-back
# Purpose:
#   Tight loop with an indirect jump back each iteration to stress trace bandwidth.
#
# Flow:
#   1) Set mtvec -> hang
#   2) Load loop target into t2
#   3) Loop 1000 times: decrement counter; if zero -> fall-through; otherwise
#      perform jalr x0,t2,0 (indirect jump back)
#   4) Call a function, return, and exit via ecall

_start:
    # point traps/ecall to local hang handler
    la      t3, hang
    csrw    mtvec, t3

    # prepare loop
    li      t0, 1000          # loop counter
    la      t2, loop_start    # indirect target in register

    # --- tight loop (indirect jump back) ---
loop_start:
    addi    t0, t0, -1        # decrement
    beqz    t0, loop_done     # if zero -> done (fall-through)
    jalr    x0, t2, 0         # indirect jump back to loop_start (no link)

loop_done:
    # function call after loop
    call    overflow_func

    # exit (ecall will go to hang via mtvec)
    li      a0, 0
    li      a7, 93
    ecall

# small function to mark the end of the burst
overflow_func:
    li      a0, 0x55
    ret

# trap / parking sinks
hang:
    j       hang
