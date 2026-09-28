# Spec Delta

## MODIFIED Requirements

### Requirement: Help and inspection
`/help [command]` SHALL list available commands and explain syntax, aliases and
permissions. `/help tutorial` SHALL be available before and after login and
provide a readable, paragraph-based walkthrough of four existing gameplay
workflows: moving, joining players and teleporting; creating and exploring a
room; creating a message-only item action and a teleporting item action; and
classifying a creature and configuring its timed habbits. The walkthrough SHALL
use valid command examples, explain that item portals can target another
owner's public room but not a private room, and distinguish builder-only steps
from actions that guests may perform. Successful post-login welcome guidance
SHALL direct players to `/help tutorial`. Regular `/help` output SHALL preserve
its command syntax reminder and include a blank line after that reminder before
the final prompt. `/look` (`/l`), `/look at`, `/examine` (`/ex`), `/exits`,
`/rooms [user]`, `/items [user]`, `/who` and `/whoami` SHALL implement the
outline's inspection behavior. `/habbits <item>` SHALL list cron-job details for
an item or creature. Player inspection SHALL show identity and presence, not
invent an editable description field absent from the user schema. Item action
names and cron-job summaries SHALL be public to visitors; detailed flavor,
target, and cron-output editing data SHALL be restricted to the owner/admin.

#### Scenario: Room view
- **WHEN** a player uses `/look`
- **THEN** they see room name, description, exits, ordinary items, creatures and players, then a prompt
- **AND** ordinary items appear only below `Items:` and items marked `creature: true` appear only below `Creatures:`
- **AND** each item or creature is shown as an indented local name followed by its bracketed local id, without repeating the room id
- **AND** a blank line precedes the room name and follows the player list;
  login, movement and teleports use the same spacing

#### Scenario: Public tutorial topic
- **WHEN** a guest runs `/help tutorial`
- **THEN** the MUD shows the four gameplay walkthroughs without requiring a
  login or exposing private room or editing data

#### Scenario: Portal tutorial example
- **WHEN** a registered room owner reads the item-action section of
  `/help tutorial`
- **THEN** it shows one action that returns flavor text and another that assigns
  a teleport destination, and explains that another owner's destination must be
  public

#### Scenario: Welcome and regular help spacing
- **WHEN** a player successfully enters the MUD and later runs `/help`
- **THEN** the welcome guidance mentions `/help tutorial` and the regular help
  response has a blank line between its final syntax reminder and the prompt
