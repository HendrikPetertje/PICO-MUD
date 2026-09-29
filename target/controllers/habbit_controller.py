from models.storage import GameError
from models.properties import display_name
from views import game_view


class HabbitController:
    def __init__(self, world, sessions, notifications):
        self.world, self.sessions, self.notifications = world, sessions, notifications
        self.elapsed = {}

    def tick(self, elapsed_ms):
        occupied = {session.room_id for session in self.sessions.live()}
        active = set()
        for room in self.world.rooms.data:
            room_id = room["room_id"]
            for item in room["items"]:
                for job in item.get("cron_jobs", []):
                    key = (room_id, item["id"], job["id"])
                    if room_id not in occupied:
                        continue
                    active.add(key)
                    elapsed = self.elapsed.get(key, 0) + elapsed_ms
                    if elapsed < job["interval_seconds"] * 1000:
                        self.elapsed[key] = elapsed
                        continue
                    self.elapsed[key] = 0
                    if "emote" in job:
                        self.notifications.room(room_id, game_view.speech(item["name"], job["emote"], True))
                    if "chat_out" in job:
                        self.notifications.room(room_id, game_view.speech(item["name"], job["chat_out"]))
                    if "set_variable" in job:
                        for session in self.sessions.live():
                            if session.room_id == room_id:
                                try:
                                    key, value = session.properties.apply(session, room["owner_id"], job["set_variable"])
                                    self.notifications.send(session, "{}: {}".format(display_name(key), value))
                                except GameError as error:
                                    self.notifications.send(session, str(error))
        self.elapsed = {key: value for key, value in self.elapsed.items() if key in active}
