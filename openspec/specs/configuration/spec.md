# configuration Specification

## Purpose

Defines the settings file on the Pico, its default values, and how the
configuration is validated when the device boots.

## Requirements

### Requirement: Configuration file
The system SHALL read all settings from `config.py` in the root of the device.
This SHALL remain a settings-only file, separate from utility modules and MVC
state; validation SHALL occur during boot without storing database or dirty
state in configuration.
The file SHALL define at least the following settings with these defaults:
`AP_SSID` ("PICO MUD"), `AP_PASSWORD` ("MultiUserDungeon"), `TELNET_PORT`
(8888), `MAX_CLIENTS` (6), `IDLE_TIMEOUT` (900 seconds), `ADMIN_NAME`,
`ADMIN_PASSWORD`, `PASSWORD_SALT`, `WELCOME_TEXT`, `SAVE_INTERVAL` (30),
`MAX_USERS` (15), `MAX_ROOMS_PER_USER` (10), `MAX_ITEMS_PER_ROOM` (5),
`MAX_INTERACTIONS_PER_ITEM` (2), `MAX_NAME_LENGTH` (60), `MAX_TEXT_LENGTH`
(250), `MAX_MAILS` (10) and `MIN_FREE_MEMORY` (32768 bytes).

#### Scenario: Defaults present
- **WHEN** the device boots with the shipped `config.py`
- **THEN** every listed setting is defined with its default value

#### Scenario: Changed value is used
- **WHEN** the admin changes `TELNET_PORT` to 2323 in `config.py` and reboots
- **THEN** the telnet server listens on port 2323

#### Scenario: MVC configuration location
- **WHEN** the application is deployed with utility and MVC packages
- **THEN** the admin still edits the single root-level `config.py`
- **AND** no package-specific duplicate configuration is required

### Requirement: Fixed line length constant
`config.py` SHALL define `MAX_LINE_LENGTH` as a global constant, in bytes, for
the maximum length of one input line. It SHALL be marked in the file as a
device limit that is not meant to be tuned.

#### Scenario: Constant defined
- **WHEN** `config.py` is inspected
- **THEN** `MAX_LINE_LENGTH` is defined and a comment says it reflects the
  device's memory limits

### Requirement: Public defaults warning
`config.py` SHALL include a comment warning that the default `AP_PASSWORD`,
`ADMIN_NAME`, `ADMIN_PASSWORD` and `PASSWORD_SALT` are public, that they should
be changed before the first boot of a private MUD, and that changing
`PASSWORD_SALT` later makes existing passwords invalid.

#### Scenario: Warning present
- **WHEN** an admin opens `config.py`
- **THEN** the warning is shown above the credential settings

### Requirement: Boot-time validation
At boot, before the hotspot starts, the system SHALL check that `AP_PASSWORD`
is 8 to 63 characters long and that `TELNET_PORT`, `MAX_CLIENTS`,
`IDLE_TIMEOUT` and `MAX_LINE_LENGTH` are positive integers. A failed check
SHALL be treated as a fatal error that names the invalid setting.

#### Scenario: Password too short
- **WHEN** `AP_PASSWORD` is "short" and the device boots
- **THEN** no hotspot is started, a message naming `AP_PASSWORD` is printed to
  the serial console, and the fatal error LED pattern is shown

#### Scenario: Valid configuration
- **WHEN** all checked settings are valid
- **THEN** boot continues to the hotspot
