# Spec Delta

## Purpose

Defines the password-protected wifi access point the Pico creates at boot so
invited players can reach the MUD at a fixed address.

## ADDED Requirements

### Requirement: WPA2 hotspot on boot
On boot the system SHALL start a wifi access point with SSID `AP_SSID`,
secured with WPA2 using `AP_PASSWORD`. The access point SHALL NOT be an open
network.

#### Scenario: Join with correct password
- **WHEN** a laptop joins "PICO MUD" with the configured password
- **THEN** it connects and gets an IP address from the Pico

#### Scenario: Wrong password refused
- **WHEN** a device tries to join with a wrong password
- **THEN** the connection is refused

### Requirement: Fixed address
The Pico SHALL be reachable at 192.168.4.1 on the hotspot network, and
connected devices SHALL get an address by DHCP from the Pico.

#### Scenario: Address after boot
- **WHEN** the hotspot is up
- **THEN** the serial console shows 192.168.4.1 as the Pico's address and a
  joined client can reach that address

### Requirement: Hotspot startup failure
If the access point does not become active within 10 seconds of being
started, the system SHALL treat this as a fatal error.

#### Scenario: Radio does not start
- **WHEN** the access point is still inactive after 10 seconds
- **THEN** a message is printed to the serial console and the fatal error LED
  pattern is shown

### Requirement: No other network services
The system SHALL NOT run a DNS server, captive portal or HTTP server. Only the
hotspot, its built-in DHCP, and the telnet server are started.

#### Scenario: Port 80 closed
- **WHEN** a joined client connects to 192.168.4.1 on port 80
- **THEN** the connection is refused
