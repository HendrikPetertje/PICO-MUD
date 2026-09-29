# Spec Delta

## Purpose

Provide bounded, owner-scoped session variables so builders can create temporary
per-player progression without retaining obsolete story state after a disconnect
or reboot.

## ADDED Requirements

### Requirement: Owner-scoped transient properties
The system SHALL maintain properties only for a live gameplay session, keyed by
the player identity, the owner of the content that reads or writes the property,
and a variable name. Registered users and guests SHALL each receive independent
property state. Properties SHALL be removed when a session ends and SHALL not
persist across a server restart, create a data file, or dirty persistent models.
Each player SHALL hold at most six properties for one content owner.

#### Scenario: Independent player and owner scopes
- **WHEN** two players receive a property from content owned by user 3 and one
  player also receives a property from content owned by user 4
- **THEN** each player sees only their own values and user 3's properties do not
  consume the six-property limit for user 4's content

### Requirement: Bounded property values and conditions
Property names SHALL be lowercase ASCII identifiers of at most 15 characters:
they begin with a letter and use only letters, digits, and non-consecutive,
non-trailing underscores. Player presentation SHALL render underscores as spaces
and capitalize the first letter. A stored property value SHALL be either a number
from 0 through 100 or a non-empty string of at most 15 characters. Builder
commands SHALL interpret quoted values as strings, including numeric-looking
text, and unquoted integer tokens as numbers. A condition SHALL contain a name,
one of `equals`, `more_than`, or `less_than`, and a valid stored-value type; all
conditions in one condition list SHALL pass. Numeric comparisons SHALL require
numeric stored and condition values. A missing property SHALL not satisfy a
condition.

#### Scenario: All conditions are required
- **WHEN** content requires `has_blue_key equals 1` and `health more_than 20`
- **THEN** a player missing either value cannot access that content

### Requirement: Property effects and presentation
A property effect SHALL contain a valid name and value. A string effect SHALL
replace the property value. A numeric effect SHALL use a signed numeric delta,
add it to an existing numeric value or zero when absent, and clamp the result to
0 through 100.
Adding a new property beyond the per-owner limit SHALL fail without changing
state. A successful effect SHALL notify its recipient of the resulting property
value. `/look at self` and `/look at <player>` SHALL show the target's currently
held properties, or indicate that the target has none.

#### Scenario: Numeric effect is clamped
- **WHEN** a player with `health` 99 receives the effect `[health, 5]`
- **THEN** their displayed `health` property becomes 100 and the player receives
  a notification of that result
