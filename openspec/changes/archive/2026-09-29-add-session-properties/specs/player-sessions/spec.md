# Spec Delta

## MODIFIED Requirements

### Requirement: Single login and cleanup
Only one live session SHALL represent a registered user. Successful duplicate
login SHALL remove the old session from gameplay immediately, notify and close
its connection, and enter the new session in room 1. A delayed disconnect
callback for the old connection SHALL NOT remove the replacement. Disconnect,
boot, ban and timeout SHALL release presence and queued responses exactly once,
and SHALL discard that session's transient properties.

#### Scenario: Reconnect clears properties
- **WHEN** a user disconnects after receiving a property and then logs in again
- **THEN** their new session has no properties from the previous session

#### Scenario: Duplicate login
- **WHEN** Adam successfully logs in from a second connection
- **THEN** the old connection stops acting as Adam and is disconnected
- **AND** its later cleanup leaves the new session active
