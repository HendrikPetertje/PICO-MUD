# Proposal

## Why

Mobile and desktop MUD clients can send typographic double quotes instead of
ASCII double quotes. The current command parser recognizes only ASCII quotes,
so valid multiword targets and quoted string values such as `“coffee machine”`
are rejected or misparsed.

## What Changes

- Accept opening and closing typographic double quotes as argument delimiters
  wherever the command parser accepts an ASCII double-quoted argument.
- Treat typographic opening double quotes as the speech shortcut, matching the
  existing leading ASCII `"` behavior.
- Preserve current ASCII quote delimiters, ASCII quote/backslash escape rules,
  free-text behavior, and malformed-input errors.
- Add focused parser and command-dispatch regression coverage for smart-quoted
  multiword targets and string values, including numeric-looking strings.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `command-interface`: Accept typographic double quotes for quoted command
  arguments and the leading speech shortcut without changing existing ASCII
  quoting semantics.

## Impact

- Affected code: `target/modules/command_parser.py` and
  `target/controllers/command_controller.py`.
- Affected tests: parser- and command-path coverage in `tests/`.
- No data migration, network-protocol change, or external dependency is needed.
