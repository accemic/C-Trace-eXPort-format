    .section .text
    .globl _start

# context.S — RV32I program with task regions and scheduler-owned context updates
#
# CTXP `CONTEXT` events are typically exporter-synthesized (OS/task awareness) or derived
# from traced writes to a known task-id marker address.
#
# This program models three code regions:
#   - task1
#   - scheduler
#   - task2
#
# Only the scheduler writes the task-id marker (0x70001000). An exporter can map those
# writes to CTXP `CONTEXT` events.

_start:
    la      t3, hang
    csrw    mtvec, t3

    # Marker address (arbitrary example address)
    li      t0, 0x70001000

    # enter scheduler (tasks do NOT update the marker themselves)
    j       scheduler

scheduler:
    # “switch to task 1”
    li      t1, 1
    sw      t1, 0(t0)
    call    task1

    # “switch to task 2”
    li      t1, 2
    sw      t1, 0(t0)
    call    task2

    # exit
    li      a0, 0
    li      a7, 93
    ecall

task1:
    nop
    ret

task2:
    nop
    ret

hang:
    j       hang
