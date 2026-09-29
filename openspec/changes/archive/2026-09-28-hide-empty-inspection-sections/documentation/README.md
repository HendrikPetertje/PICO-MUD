# Implementation references

- `../../../target/controllers/room_controller.py`: emits room and item
  inspection sections and headings.
- `../../../target/views/game_view.py`: formats room and item entries.
- `../../../tests/test_habits.py`: current room-view coverage, including
  separate ordinary-item and creature output.
- `../../../openspec/specs/command-interface/spec.md`: room inspection and
  bounded presentation contract.
- `../../../openspec/specs/item-interactions/spec.md`: item inspection and
  interaction visibility contract.

No external documentation is needed. Keep rendering lazy and line-oriented so
the existing response chunking and 4096-byte transport constraints remain in
effect.
