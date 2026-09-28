# Tasks

## 1. Conditional inspection sections

- [x] 1.1 Update room rendering to omit `Exits:`, `Items:`, and `Creatures:` when no corresponding renderable entry exists, while preserving populated-section order, visibility checks, and item/creature separation; verify focused room-view tests cover empty and populated sections.
- [x] 1.2 Update item inspection to omit `Actions:` when an item has no interactions while preserving the heading and entries for populated actions and owner/admin examine details; verify focused item-view tests cover both states.

## 2. Verification

- [x] 2.1 Run `python -m unittest discover -s tests -v` and inspect representative empty and populated output; verify no empty section headings remain and existing room/item content is unchanged when present.
- [x] 2.2 Validate the change with `openspec validate hide-empty-inspection-sections --strict`; resolve every reported issue before implementation review.
