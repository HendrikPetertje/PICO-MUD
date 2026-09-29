# Design

## Context

See `proposal.md` for motivation and the two spec deltas for user-visible
behavior. `RoomController.view()` currently emits each section heading before it
knows whether a matching exit, ordinary item, or creature will be rendered.
`item_view()` similarly writes `Actions:` unconditionally before iterating
interactions. The existing room-view test only covers populated item and creature
sections; there is no item-inspection coverage for an item with no actions.

## Goals / Non-Goals

**Goals:**

- Render a heading only when at least one entry in that section will be emitted.
- Preserve lazy, line-oriented rendering, per-entry room visibility checks, item
  versus creature separation, entry order, and final player/prompt output.
- Cover empty and populated output paths with focused local tests.

**Non-Goals:**

- Do not change room data, permissions, command syntax, item interactions, or
  the standalone `/exits` and `/interactions` commands.
- Do not replace an empty section with placeholder text.
- Do not add buffering, storage, or transport abstractions.

## Decisions

### 1. Collect only each room section's renderable lines before its heading

For exits, the renderer can test the existing exit mapping before yielding the
heading. For items and creatures, it will first build a small list of matching
rendered lines from the existing room-local item snapshot, retaining the current
per-item re-resolution and visibility checks. It will yield the heading only if
that list is non-empty.

This keeps output ordering and mutation-safety checks intact. The configured
room item limit is small, so storing a section's rendered lines is bounded. A
second scan merely to determine emptiness would duplicate model lookups and
visibility checks.

### 2. Gate item action headings on the interaction collection

`item_view()` will yield `Actions:` only if the inspected item's interaction
list is non-empty. Detailed owner/admin metadata remains independent of that
heading, so `/examine` still shows technical item information for an item without
actions.

### 3. Extend the existing test module

Add tests alongside the established room-controller coverage in
`tests/test_habits.py`. Use the current in-memory room/item fixtures to assert
that empty headers are absent and populated headers retain their entries. This
avoids adding a test framework or introducing device-dependent checks.

## Risks / Trade-offs

- Rendering a section from a transient item snapshot could display stale entries
  after a later mutation -> retain the current re-resolution and access checks,
  skipping disappeared items as today.
- Header omission can accidentally suppress populated data -> test rooms with
  exits, ordinary items, creatures, and actions independently.
- Buffered section lines add minor temporary allocation -> the configured room
  item limit bounds the list size; no whole response is assembled.

## Migration Plan

No data migration is required. Deploy only the changed application source using
the established package upload procedure, preserving device `config.py` and
`data/`. Rollback restores the prior controller source; saved room and item data
is unchanged.
