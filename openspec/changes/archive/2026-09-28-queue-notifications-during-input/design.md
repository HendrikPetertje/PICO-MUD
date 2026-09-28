# Design

## Context

See `proposal.md` for motivation and the `player-communication` delta for the
behavior contract. Notifications currently call `Client.try_send` directly,
while `Session.pump` independently streams command responses and terminal
prompts. `Client.line` retains bytes received so far, but a direct write cannot
be made safe for an arbitrary telnet client without terminal cursor control.

The Pico has fixed memory limits, per-client output is already capped at 4096
bytes, and the project requires plain UTF-8 output without ANSI sequences.

## Goals / Non-Goals

**Goals:**

- Prevent notifications from corrupting or obscuring a command being typed.
- Retain normal notification routing and their arrival order for retained items.
- Keep deferred state bounded, session-local, and non-persistent.
- Present deferred notices before a single subsequent command prompt.

**Non-Goals:**

- Redraw active lines with ANSI terminal controls.
- Guarantee delivery after a recipient disconnects or remains idle forever.
- Change command parsing, telnet negotiation, message visibility, or saved data.
- Build a global notification channel or durable notification inbox.

## Decisions

### Use a bounded queue owned by `Session`

Each active session will own a small fixed-capacity collection of formatted
notification messages plus an overflow flag. `NotificationController` will
enqueue through the session instead of writing directly to its client.

This keeps presentation timing beside existing response state, has no model
impact, and bounds allocation per connected client. A global queue would add
routing lifecycle complexity and a persistent queue would change game behavior.

### Flush only at a prompt-safe response boundary

After a complete incoming line has been processed, `Session.pump` will stream
the command result, then append queued notifications, an omission notice if the
queue overflowed, and exactly one prompt. Notifications generated while the
line is being handled are included in that same safe presentation cycle.

The terminal prompt is the natural boundary: the user has already committed
their input, and the next prompt makes the queued output readable. Immediate
writes with ANSI redraw were rejected because the command-interface contract
prohibits cursor control and basic telnet clients need not support it.

### Do not flush solely because the transport has output capacity

Notifications remain held until a line is submitted rather than being sent from
the periodic pump while the player may be typing. This favors input integrity
over real-time delivery and avoids having to infer client-side editing state.

### Reuse existing missed-notification reporting semantics

Queue overflow and a client output buffer that cannot accept safe presentation
will set a concise missed-notifications indicator. The indicator is emitted at
the next successful safe boundary rather than creating an unbounded backlog.

## Risks / Trade-offs

- [A player who never presses Enter will not see notifications immediately] ->
  This is intentional to preserve their input; bounded retention and an
  omission notice prevent unbounded memory growth.
- [More session state adds allocation pressure on the Pico] -> Use a small
  fixed capacity, clear it on disconnect/logout, and avoid copying messages
  after they have been rendered.
- [Command responses can temporarily delay notifications after Enter] -> Flush
  only after the response is complete so output order and the final prompt stay
  coherent.
- [Queue overflow drops transient notices] -> Surface one concise omission
  notice; message persistence and routing behavior remain unchanged.

## Migration Plan

1. Upload the changed application files without replacing the Pico's `/data`
   directory.
2. Restart the Pico so all sessions use the new per-session transient state.
3. Roll back by restoring the prior application files and restarting; no data
   migration or cleanup is needed because queued notifications are ephemeral.
