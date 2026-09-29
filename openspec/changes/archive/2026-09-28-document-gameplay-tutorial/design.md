# Design

## Context

See `proposal.md` for motivation and the command-interface delta for behavior.
Regular help is generated from the canonical `COMMANDS` registry in
`target/modules/commands.py`: `CommandController.help()` resolves a topic as a
registered command and sends entries through `game_view.help_entry()`. A
non-command `tutorial` topic therefore needs an explicit branch before registry
lookup. The existing response pipeline accepts iterators and chunks long lines,
so it can deliver a short tutorial without new buffering behavior.

`README.md` currently has a two-column command table. Command syntaxes containing
literal `|` are parsed as extra Markdown columns, then the document ends without
any guided examples.

## Goals / Non-Goals

**Goals:**

- Keep regular command help registry-driven.
- Add one stable tutorial topic that uses the same command names, syntax, and
  permission constraints as the existing implementation and specs.
- Keep tutorial rendering in the view layer as yielded plain-text lines, so the
  existing bounded response and prompt behavior is retained.
- Make the README's command syntax render correctly and make its walkthroughs
  match the in-game tutorial.

**Non-Goals:**

- Do not add a command named `tutorial`, alter command permissions, or change
  room, item, creature, or habit mechanics.
- Do not duplicate all command-reference text in the tutorial or add external
  documentation dependencies.
- Do not change transport buffering, persistence, or the public game data model.

## Decisions

### 1. Reserve `tutorial` as a help-only topic

`CommandController.help()` will recognize `tutorial` after parsing the optional
topic and before looking up a registry command. This avoids adding it to the
command registry, where it would become an executable slash command and a
reserved item-action name. Other topics retain their existing registry lookup
and unknown-topic behavior.

The alternative, representing the tutorial as a synthetic registry entry, would
incorrectly expose `/tutorial` as a built-in command and make the help renderer
fit paragraph content into a per-command shape.

### 2. Render tutorial text with a dedicated view generator

`target/views/game_view.py` will provide a small generator for tutorial lines.
It will group the existing workflows into movement, rooms, items, and creatures,
with prose and literal command examples. The controller will return this
generator directly so the telnet response pipeline continues to chunk it and add
one final prompt.

The tutorial will say that builders must own the current room for editing and
that guests can move through public rooms and run item actions. It will show
message-only and portal interactions separately, and state that cross-owner
portal targets must be public. It will only document implemented commands:
`/go`, direction aliases, `/join`, `/teleport`, `/dig`, `/rename here`,
`/describe here`, `/create`, `/interaction`, `/creature`, `/habit`, and
`/habits`.

Embedding the tutorial as a multi-line controller string would work but would
mix presentation with command routing and make matching README text harder to
review.

### 3. Apply spacing only to regular command-list help

The existing syntax reminder will gain one trailing newline in the normal
`help_lines()` output, yielding the required blank line before the terminal
prompt. The tutorial owns its own paragraph spacing and does not need to reuse
the regular command-list header or reminder.

### 4. Keep README walkthroughs adjacent to the command table

Escape every pipe in command syntax cells as `\|`, including existing optional
alternatives. Follow the table with four short subsections aligned with the
in-game topic, using the same valid commands and caveats. This repairs the
rendering at the source rather than replacing the table with a less scannable
format.

## Risks / Trade-offs

- Tutorial examples can drift from gameplay behavior as commands evolve -> use
  the command registry and existing capability specs as the implementation
  source, and manually exercise each example after editing.
- Added help text can grow beyond a single transport queue -> yield bounded
  lines through the existing response iterator rather than concatenate one
  response string.
- Markdown tables remain fragile around special characters -> review the rendered
  table and verify that every syntax alternative uses an escaped pipe.

## Migration Plan

No data or protocol migration is required. Deploy the updated application files
with the normal package upload procedure while preserving device `config.py` and
`data/`. Rollback is restoring the previous `README.md` and changed application
files; saved worlds are unaffected.
