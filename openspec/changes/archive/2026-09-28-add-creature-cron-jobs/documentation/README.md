# Implementation References

## Local sources

- `target/controllers/persistence_controller.py`: maintains elapsed time from `time.ticks_ms()` and owns the application tick.
- `target/controllers/telnet_controller.py`: invokes the world's tick and owns live session and notification collaborators.
- `target/controllers/notification_controller.py`: broadcasts to live sessions in a room.
- `target/models/items.py`: owns nested item validation and mutation in room storage.
- `target/controllers/room_controller.py`: formats room `/look` output and item inspection.

## Design constraint

The Pico has no wall clock. Cron jobs must therefore use elapsed monotonic intervals derived from the existing tick loop, not calendar expressions or persisted absolute timestamps.
