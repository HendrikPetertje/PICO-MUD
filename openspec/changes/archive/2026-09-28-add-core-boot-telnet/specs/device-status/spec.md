# Spec Delta

## Purpose

Shows the state of the Pico on the onboard LED and reports fatal errors over
the serial console so an admin can diagnose a device without a screen.

## ADDED Requirements

### Requirement: LED status patterns
The onboard LED SHALL show the device state: 1 blink when the hotspot is up;
2 blinks and then steady on when the telnet server is running; 3 blinks,
repeating until reset, after a fatal error.

#### Scenario: Normal boot
- **WHEN** the device boots with a valid configuration
- **THEN** the LED blinks once, then twice, then stays on

#### Scenario: Fatal error
- **WHEN** a fatal error occurs
- **THEN** the LED blinks 3 times, pauses, and repeats until the Pico is reset

### Requirement: Fatal error reporting
A fatal error (invalid configuration, hotspot failure, or an unhandled error
in the event loop itself) SHALL print the error and its traceback to the
serial console, stop the server, and then show the fatal error LED pattern.
The device SHALL NOT reboot itself, and no watchdog SHALL be used.

#### Scenario: Event loop crashes
- **WHEN** an unhandled exception escapes the event loop
- **THEN** the traceback is printed over serial and the LED shows the fatal
  error pattern, and the device stays in that state until reset

### Requirement: Boot log
The system SHALL print progress to the serial console during boot: the
hotspot SSID and IP address once the hotspot is up, and the telnet port once
the server is listening.

#### Scenario: Watch boot over serial
- **WHEN** the admin opens a serial REPL and resets the Pico
- **THEN** the SSID, `192.168.4.1` and the telnet port are printed
