# Spec Delta

## MODIFIED Requirements

### Requirement: Help and inspection
`/help [command]` SHALL list available commands and explain syntax, aliases and permissions. `/look` (`/l`), `/look at`, `/examine` (`/ex`), `/exits`, `/rooms [user]`, `/items [user]`, `/who` and `/whoami` SHALL implement the outline's inspection behavior. `/habbits <item>` SHALL list cron-job details for an item or creature. Item action names and cron-job summaries SHALL be public to visitors; detailed flavor, target, and cron-output editing data SHALL be restricted to the owner/admin.

#### Scenario: Room view
- **WHEN** a player uses `/look`
- **THEN** they see room name, description, exits, ordinary items, creatures and players, then a prompt
- **AND** ordinary items appear only below `Items:` and items marked `creature: true` appear only below `Creatures:`
- **AND** each item or creature is shown as an indented local name followed by its bracketed local id, without repeating the room id
- **AND** a blank line precedes the room name and follows the player list; login, movement and teleports use the same spacing
