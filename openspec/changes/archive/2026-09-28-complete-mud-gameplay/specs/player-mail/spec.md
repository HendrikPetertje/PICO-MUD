# Spec Delta

## Purpose

Provide a small persistent private inbox for each registered player, including
offline delivery and strict capacity and recipient-only access rules.

## ADDED Requirements

### Requirement: Send bounded mail
`/mail send <user> <title> = <message>` SHALL append a mail containing numeric
from_user_id, title and message to an existing registered recipient's inbox.
Title SHALL fit MAX_NAME_LENGTH and message MAX_TEXT_LENGTH; both SHALL be
nonempty. At MAX_MAILS entries (default 10), further sends SHALL fail without
dropping or replacing existing mail. Sending to oneself or an offline user
SHALL work. Guests SHALL neither send nor receive mail.

#### Scenario: Full inbox
- **WHEN** a recipient already has 10 mails and another send is attempted
- **THEN** the sender sees inbox-full and neither mailbox nor dirty state changes

### Requirement: Own inbox only
`/mail` SHALL list the acting user's mail by 1-based number, sender and title.
`/mail read <number>` SHALL show that message; `/mail delete <number>` SHALL
delete it and renumber remaining entries. Invalid numbers SHALL fail safely.
Even admins SHALL NOT read or delete another user's mail through these commands.

#### Scenario: Admin privacy boundary
- **WHEN** an admin uses `/mail read 1`
- **THEN** only the admin's own first mail can be returned, never another inbox

### Requirement: Mail persistence and notification
Successful send/delete SHALL dirty only mail storage. Reads SHALL not dirty it.
Online recipients SHALL receive a new-mail notification after successful send;
offline recipients SHALL retain the message without a transient notification
backlog. Pending inbox response rendering SHALL not reveal deleted mail to
another session or treat a changed list number as a stable identity.

#### Scenario: Offline delivery survives restart
- **WHEN** mail is sent to an offline user and saved before reboot
- **THEN** the user can read it after logging in, with sender and text intact
