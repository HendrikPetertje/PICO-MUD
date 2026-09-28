# Tasks

## 1. In-game tutorial help

- [x] 1.1 Add a dedicated plain-text tutorial renderer covering movement and teleportation, room building, message and portal item actions, and creatures with habbits; verify every shown command matches the implemented parser and the relevant capability specs.
- [x] 1.2 Route `/help tutorial` to the tutorial renderer before normal command-topic lookup without registering `/tutorial` as a command; verify guests and logged-in users receive the tutorial while unknown help topics still fail normally.
- [x] 1.3 Add the `/help tutorial` hint to successful post-login guidance and add the required blank line after the standard `/help` syntax reminder; verify the exact welcome and help output through the existing response pipeline, including one final prompt.

## 2. README gameplay guide

- [x] 2.1 Escape literal Markdown table pipes in every Commands table syntax that uses alternatives; verify the rendered table remains two columns and all command descriptions are aligned.
- [x] 2.2 Add concise Commands subsections for movement, room creation and exploration, item message/portal actions, and creatures/habbits; verify the examples match `/help tutorial`, existing permissions, and public-room portal restrictions.

## 3. Verification

- [x] 3.1 Run the available local syntax or focused command-help checks and manually inspect `/help`, `/help tutorial`, and login welcome output; verify the tutorial output is complete, has no raw Markdown, and retains bounded-response behavior.
- [x] 3.2 Validate the OpenSpec change with `openspec validate document-gameplay-tutorial --strict`; resolve every reported issue before requesting implementation review.
