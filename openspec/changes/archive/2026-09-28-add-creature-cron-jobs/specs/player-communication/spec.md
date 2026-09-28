# Spec Delta

## ADDED Requirements

### Requirement: Automated room messages
Due item and creature cron jobs SHALL use the existing room notification behavior to deliver emotes and speech only to live gameplay sessions currently in the item's room. Pre-login, disconnected, closing, and sessions in other rooms SHALL not receive the automated output. Automated messages SHALL be transient and SHALL not change persistent state merely by running.

#### Scenario: Automated room isolation
- **WHEN** a due creature cron job emits output in a room with two occupants and another player is elsewhere
- **THEN** both occupants receive the output and the player elsewhere does not
