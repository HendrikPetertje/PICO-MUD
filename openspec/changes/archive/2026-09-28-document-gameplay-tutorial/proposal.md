# Proposal

## Why

The README's Commands table renders several syntaxes incorrectly because literal
pipe characters are interpreted as Markdown table separators. It also lists
commands without showing a player how the core movement, building, interaction,
and creature systems fit together; the in-game help has the same gap.

## What Changes

- Repair the README command table by escaping pipe characters in command
  syntaxes.
- Add guided README subsections under Commands covering movement, joining and
  teleporting; digging and describing rooms; message and teleport item actions;
  and creatures with timed habbits.
- Add a public `/help tutorial` topic that presents the same four gameplay
  walkthroughs in concise paragraphs with executable command examples.
- Point logged-in players to `/help tutorial` in the welcome guidance.
- End `/help` responses with a blank line after the existing syntax reminder,
  before the normal prompt.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `command-interface`: add a public tutorial help topic, a post-login tutorial
  hint, and required help-output spacing.

## Impact

The implementation will update `README.md`, the command help routing and
rendering in `target/controllers/command_controller.py` and
`target/views/game_view.py`, and possibly the command registry if its help
description must advertise the tutorial topic. No gameplay command, persistence,
permission, or networking behavior changes. The tutorial describes existing
room-building, item-interaction, and creature-scheduling rules without changing
their specifications.
