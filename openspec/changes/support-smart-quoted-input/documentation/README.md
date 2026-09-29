# Implementation Notes

## Observed Scope

- `target/modules/command_parser.py` owns token parsing for command arguments,
  including quoted tokens and final free-text values.
- `target/controllers/command_controller.py` independently detects a leading
  ASCII double quote as the shorthand for room speech before it creates an
  `Arguments` instance.
- `target/controllers/mail_controller.py` creates a second `Arguments` instance
  while separating a mail title from its `=` delimiter, so parser-level support
  must work for nested parser use as well.

## Compatibility Constraint

The targeted client behavior uses paired typographic quotes: left double quote
(`U+201C`) opens a quoted value and right double quote (`U+201D`) closes it.
ASCII double quotes continue to open and close values and remain the only
escapable quote character with the existing backslash syntax. Typographic quote
characters within ASCII-quoted values stay ordinary text unless they are the
matching closing delimiter.

## Verification Focus

- Smart-quoted multiword item names resolve through regular item/action command
  paths.
- Smart-quoted values remain strings when their content resembles an integer.
- Leading left double quotes route non-slash input through room speech.
- Mismatched or unterminated quote pairs continue to produce an input error.
