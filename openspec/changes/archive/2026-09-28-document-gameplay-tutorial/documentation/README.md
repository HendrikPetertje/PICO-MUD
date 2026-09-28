# Implementation references

- `../../../README.md`: user-facing installation and command documentation to
  repair and expand.
- `../../../target/modules/commands.py`: canonical command syntax and summary
  descriptions used by regular help.
- `../../../target/controllers/command_controller.py`: current `/help` lookup,
  output sequence, and post-login welcome guidance.
- `../../../target/views/game_view.py`: bounded, pure text renderers used for
  normal help entries.
- `../../../openspec/specs/command-interface/spec.md`: authoritative help and
  bounded-output requirements.
- `../../../openspec/specs/room-building/spec.md`,
  `../../../openspec/specs/item-interactions/spec.md`, and
  `../../../openspec/specs/creature-scheduling/spec.md`: existing rules and
  examples that the tutorial must accurately explain.

The implementation needs no external documentation or dependency. Keep tutorial
text bounded and yielded in the existing response pipeline so it retains the
4096-byte transport guarantees.
