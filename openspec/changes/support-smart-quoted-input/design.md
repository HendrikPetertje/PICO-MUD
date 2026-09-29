# Design

## Context

See `proposal.md` for motivation and the `command-interface` delta for required
behavior. The shared `Arguments` parser currently has four ASCII-quote checks:
opening-token recognition, closing-token recognition, ASCII escape validation,
and detection of a quoted final free-text argument. `CommandController.dispatch`
also independently recognizes a leading ASCII quote as a room-speech shortcut.
`MailController` reparses the title segment with `Arguments`, so a parser-level
change also covers mail titles.

## Goals / Non-Goals

**Goals:**

- Accept the paired left/right typographic double quotes emitted by clients as
  delimiters in every shared parser path.
- Keep existing ASCII quoting, escaping, whitespace validation, and error
  behavior stable.
- Keep the leading speech shortcut consistent with parser-recognized openers.

**Non-Goals:**

- Supporting single quotation marks, locale-specific guillemets, or arbitrary
  Unicode punctuation as delimiters.
- Normalizing or rewriting typographic quote characters inside accepted text.
- Changing the telnet decoder, stored data format, command grammar, or help text
  beyond behavior covered by the specification.

## Decisions

### Recognize explicit quote pairs

The parser will classify a token's first character as either an ASCII quote or a
left typographic double quote, then require its matching closer: ASCII quote for
ASCII input and right typographic double quote for typographic input. The
resulting delimiter is not included in the parsed value. This accepts the client
behavior reported by users without making a lone or mismatched typographic quote
silently valid.

Alternative considered: treat all three quote characters as interchangeable
openers and closers. Rejected because it would accept malformed or accidentally
mixed input and make diagnostics less predictable.

### Preserve ASCII-only escaping

The existing escape grammar remains scoped to ASCII-quoted input: backslash may
escape ASCII quote and backslash only. Smart-quoted input does not introduce
backslash escapes, so backslashes and embedded typographic quotes stay literal
unless the matching right quote terminates the argument. This avoids adding an
ambiguous Unicode escape language and preserves existing ASCII behavior.

Alternative considered: allow `\”` inside smart-quoted input. Rejected because
the product need is delimiter compatibility, not an expanded quoting language.

### Share opener recognition with speech dispatch

Extract or otherwise reuse the quote-opener classification so `Arguments.rest()`
and `CommandController.dispatch()` agree on which characters initiate quoted
content or shorthand speech. Keep the helper small and allocation-free for the
Pico's constrained MicroPython runtime.

Alternative considered: add a second hard-coded smart-quote check in dispatch.
Rejected because parser and dispatch behavior could drift as delimiters evolve.

### Test parser semantics through command paths

Add focused unit coverage for both `Arguments` parsing and at least one real
multiword action/builder path, plus leading smart-quote speech dispatch. Retain
existing ASCII-quoted tests as compatibility coverage. This verifies the shared
parser's direct behavior and its externally visible integration points.

Alternative considered: only add a parser unit test. Rejected because dispatch
has its own shortcut branch and mail creates a separate parser instance.

## Risks / Trade-offs

- [A smart quote arrives without its matching closing quote] -> Preserve the
  existing unterminated-input failure instead of consuming arbitrary text.
- [Duplicated delimiter checks diverge between parser and dispatch] -> Centralize
  opener recognition in the parser module and test shortcut speech explicitly.
- [Additional Unicode comparisons affect Pico memory or speed] -> Use fixed
  character constants and a short linear scan; command lines are already
  decoded Unicode and bounded in length.

## Migration Plan

1. Deploy the parser and dispatch update with regression tests.
2. Existing ASCII-quoted commands remain valid; no persistent records need
   conversion because delimiters are removed before values are stored.
3. Roll back by restoring the prior code; previously stored values are unchanged,
   while clients using typographic delimiters must return to ASCII quotes.
