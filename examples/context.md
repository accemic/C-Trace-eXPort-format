# context: scheduler-owned task/context switches

Demonstrates `CONTEXT` events.

`CONTEXT::<value>` indicates the core entered a new context/task. The interpretation of
`value` is exporter- and target-dependent (often a task id).

This minimal example models three code regions:

- `task1`
- `scheduler`
- `task2`

Only the **scheduler** updates a “current task id” marker address. An exporter can derive
CTXP `CONTEXT` events from those marker writes.

The important point: after the scheduler updates the marker (context), execution continues
into the task code region *without the task itself touching the marker*.

Source provenance: [_sources/context.S](_sources/context.S).
