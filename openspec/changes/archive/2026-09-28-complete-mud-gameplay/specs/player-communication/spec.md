# Spec Delta

## Purpose

Deliver room chat, direct messages and presence notices to live players using
their current session locations and the existing non-blocking telnet transport.

## ADDED Requirements

### Requirement: Room speech and emotes
`/say`, plain text and the quote shortcut SHALL send speech to all active
sessions in the sender's room, including the sender. `/emote` and the colon
shortcut SHALL do the same with action text. Guests SHALL participate. Chat
SHALL be bounded by MAX_TEXT_LENGTH and SHALL not be persisted.

#### Scenario: Room isolation
- **WHEN** Adam speaks with Bob in his room and Carol elsewhere
- **THEN** Adam and Bob receive the message and Carol does not

### Requirement: Direct messages and announcements
`/whisper <player> <text>` SHALL require a live recipient in the same room;
`/page <player> <text>` SHALL reach a live player anywhere. Both SHALL support
guest identities, report invalid/offline recipients and confirm to the sender.
Only sender and recipient SHALL see message text. `/shout` SHALL require admin
rights and reach all active gameplay sessions. Pre-login connections SHALL
not receive gameplay messages.

#### Scenario: Whisper outside room
- **WHEN** Adam whispers to Bob while he is elsewhere
- **THEN** Adam receives an error and nobody receives the private text

### Requirement: Presence sequencing
Successful moves SHALL queue departure to the old room excluding the mover,
update the live location, queue arrival to the new room excluding the mover,
and show the new room to the mover in one controller turn. Failed or same-room
moves SHALL not announce movement. Login, logout, timeout, boot and replacement
SHALL update and announce presence exactly once per affected session.

#### Scenario: Moving between rooms
- **WHEN** Adam successfully moves north
- **THEN** old-room players see departure and new-room players see arrival
- **AND** subsequent chat uses Adam's new location immediately

### Requirement: Direct notification routing
Notification controllers SHALL select recipients from the session controller's
live collection by session, user id, room id or all sessions. Views SHALL format
text; transport SHALL queue it. There SHALL be no separate channels registry,
durable notification queue or model-originated socket calls. A failed recipient
SHALL not stop delivery to others. Unsolicited text SHALL start on a fresh line
and reissue the command prompt when appropriate, without ANSI restoration.

#### Scenario: Stale connection during broadcast
- **WHEN** one room occupant has disconnected during a notification
- **THEN** remaining eligible occupants receive it and persistent state stays clean
