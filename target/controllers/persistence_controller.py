import os
import sys
import time
from models.storage import exists, require
from models.users import Users
from models.rooms import Rooms
from models.items import Items
from models.mail import Mail


class PersistenceController:
    def __init__(self, config, reserved, directory="/data"):
        self.config = config
        self.directory = directory
        self.users = Users(directory + "/users.json", config)
        self.rooms = Rooms(directory + "/rooms.json", config)
        self.items = Items(self.rooms, config, reserved)
        self.mail = Mail(directory + "/mail.json", config)
        self.last_tick = time.ticks_ms()
        self.elapsed_ms = 0
        self.save_elapsed = 0

    def load(self):
        if not exists(self.directory):
            os.mkdir(self.directory)
        present = [exists(m.path) for m in (self.users, self.rooms, self.mail)]
        if not any(present):
            room = self.rooms.prepare_room(1, "Global Home")
            user = self.users.prepare_user(self.config.ADMIN_NAME, self.config.ADMIN_PASSWORD, 1, True)
            self.rooms.publish([room])
            self.users.publish([user])
            self.mail.publish({})
        else:
            require(present[0] and present[1], "Incomplete users/rooms database; restore a backup.")
            self.users.load()
            self.rooms.load()
            if present[2]:
                self.mail.load()
            else:
                self.mail.publish({})
        self.validate()
        results = self.save()
        require(not any(m.dirty for m in (self.users, self.rooms, self.mail)),
                "Initial database save failed: " + "; ".join(results))

    def validate(self):
        self.users.validate()
        self.rooms.validate(self.users)
        self.items.validate()
        self.mail.validate(self.users)

    def save(self):
        results = []
        for name, model in (("users", self.users), ("rooms", self.rooms), ("mail", self.mail)):
            try:
                saved = model.save_if_dirty()
                results.append(name + (": saved" if saved else ": clean"))
            except Exception as error:
                sys.print_exception(error)
                results.append(name + ": save failed; will retry")
        return results

    def tick(self, now):
        elapsed = max(0, time.ticks_diff(now, self.last_tick))
        self.last_tick = now
        self.elapsed_ms += elapsed
        self.save_elapsed += elapsed
        if self.save_elapsed >= self.config.SAVE_INTERVAL * 1000:
            self.save_elapsed = 0
            self.save()
        return elapsed

    def create_user(self, name, password, admin=False):
        # Prepare both replacements before publishing either save unit.
        room = self.rooms.prepare_room(self.users.next_id, ("Home of " + name)[:self.config.MAX_NAME_LENGTH])
        user = self.users.prepare_user(name, password, room["room_id"], admin)
        users = self.users.data + [user]
        rooms = self.rooms.data + [room]
        self.users.publish(users)
        self.rooms.publish(rooms)
        self.users.next_id += 1
        self.rooms.next_id += 1
        return user

    def prepare_remove_user(self, identity):
        require(identity != 1, "User 1 cannot be removed.")
        self.users.get(identity)
        room_ids = [r["room_id"] for r in self.rooms.owned(identity)]
        users = [u for u in self.users.data if u["user_id"] != identity]
        rooms = self.rooms.prepare_delete(room_ids)
        mail = self.mail.prepare_remove_user(identity)
        return room_ids, users, rooms, mail

    def remove_user(self, identity, prepared=None):
        if prepared is None:
            prepared = self.prepare_remove_user(identity)
        room_ids, users, rooms, mail = prepared
        mail_changed = mail != self.mail.data
        self.users.publish(users)
        self.rooms.publish(rooms)
        if mail_changed:
            self.mail.publish(mail)
        return room_ids
