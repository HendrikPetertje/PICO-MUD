# Spec Delta

## MODIFIED Requirements

### Requirement: Direct notification routing
Notification controllers SHALL select recipients from the session controller's
live collection by session, user id, room id or all sessions. Views SHALL format
text; transport SHALL queue it. There SHALL be no separate channels registry,
durable notification queue or model-originated socket calls. A failed recipient
SHALL not stop delivery to others. Unsolicited gameplay notifications SHALL be
held in bounded per-session transient memory until the recipient has submitted
their current input and the session reaches a safe output boundary. The system
SHALL present held notifications before the next command prompt without ANSI or
cursor-control sequences. If the bounded transient queue cannot retain every
notification, the system SHALL report that some notifications were missed at the
next safe output boundary.

#### Scenario: Notification arrives during command entry
- **WHEN** a player is composing a gameplay command and receives a room message,
  emote, presence notice, page, shout, or new-mail notification
- **THEN** the system does not write the notification or another prompt before
  that player submits their current line
- **AND THEN** it presents the notification before the prompt after processing
  that line

#### Scenario: Several notifications arrive during command entry
- **WHEN** a player is composing a command while several eligible notifications
  arrive
- **THEN** the system presents the retained notifications in arrival order at the
  next safe output boundary
- **AND THEN** it presents one usable command prompt after them

#### Scenario: Held notification capacity is exceeded
- **WHEN** notifications exceed the bounded transient capacity for a player who
  has not submitted their current line
- **THEN** the system retains only the notifications that fit its bounded memory
- **AND THEN** it reports that some notifications were missed at the next safe
  output boundary

#### Scenario: Stale connection during broadcast
- **WHEN** one room occupant has disconnected during a notification
- **THEN** remaining eligible occupants receive or retain it according to their
  current input state and persistent state stays clean
