from models.storage import Records, require, text, positive, memory_guard


DIRECTIONS = ("north", "east", "south", "west", "up", "down")
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east",
            "up": "down", "down": "up"}
ALIASES = dict(zip(("n", "e", "s", "w", "u", "d"), DIRECTIONS))


def direction(value):
    value = value.lower()
    result = ALIASES.get(value, value)
    require(result in DIRECTIONS, "Expected north, east, south, west, up or down.")
    return result


class Rooms(Records):
    id_field = "room_id"

    def owned(self, owner):
        return [r for r in self.data if r["owner_id"] == owner]

    def prepare_room(self, owner, name):
        require(positive(owner), "Invalid room owner.")
        text(name, self.config.MAX_NAME_LENGTH, "Room name")
        require(len(self.owned(owner)) < self.config.MAX_ROOMS_PER_USER, "Room limit reached.")
        memory_guard(self.config)
        return {"room_id": self.next_id, "owner_id": owner, "name": name,
                "description": "An empty room.", "private": False, "exits": {}, "items": []}

    def edit(self, identity, field, value):
        require(field in ("name", "description", "private"), "Invalid room field.")
        if field == "private":
            require(type(value) is bool, "Invalid private flag.")
            require(identity != 1 or not value, "Room 1 is permanently public.")
        else:
            text(value, self.config.MAX_NAME_LENGTH if field == "name" else self.config.MAX_DESCRIPTION_LENGTH)
        return self.update(identity, field, value)

    def _exit(self, target, name):
        return {"to_room_id": target, "name": name, "description": "A passage.",
                "locked": False, "activation_text": "You go " + name + "."}

    def dig(self, source_id, way, name=None, target_id=None):
        way = direction(way)
        source = self.get(source_id)
        require(way not in source["exits"], "That exit is occupied.")
        memory_guard(self.config)
        target = self.get(target_id) if target_id is not None else self.prepare_room(source["owner_id"], name)
        require(target["room_id"] != source_id, "Cannot dig a room into itself.")
        require(source["owner_id"] == target["owner_id"], "Exits cannot link different owners' rooms.")
        reverse = OPPOSITE[way]
        require(reverse not in target["exits"], "The return exit is occupied.")
        src, dst = source.copy(), target.copy()
        src["exits"], dst["exits"] = source["exits"].copy(), target["exits"].copy()
        src["exits"][way] = self._exit(target["room_id"], way)
        dst["exits"][reverse] = self._exit(source_id, reverse)
        replacement = [src if r["room_id"] == source_id else
                       dst if r["room_id"] == target["room_id"] else r for r in self.data]
        if target_id is None:
            replacement.append(dst)
        self.publish(replacement)
        if target_id is None:
            self.next_id += 1
        return target["room_id"]

    def edit_exit(self, identity, way, field=None, value=None):
        way = direction(way)
        room = self.get(identity)
        require(way in room["exits"], "No exit in that direction.")
        if field is not None:
            require(field in ("name", "description", "activation_text", "locked"), "Invalid exit field.")
            if field == "locked":
                require(type(value) is bool, "Invalid lock flag.")
            else:
                text(value, self.config.MAX_NAME_LENGTH if field == "name" else
                     (self.config.MAX_DESCRIPTION_LENGTH if field == "description" else self.config.MAX_TEXT_LENGTH))
            if room["exits"][way][field] == value:
                return False
            memory_guard(self.config)
        changed = room.copy()
        changed["exits"] = room["exits"].copy()
        if field is None:
            del changed["exits"][way]
        else:
            changed["exits"][way] = room["exits"][way].copy()
            changed["exits"][way][field] = value
        self.publish(self.prepare_replace(identity, changed))
        return True

    def prepare_delete(self, identities):
        require(1 not in identities, "Room 1 cannot be deleted.")
        result = []
        for room in self.data:
            if room["room_id"] in identities:
                continue
            changed = room.copy()
            changed["exits"] = {k: v for k, v in room["exits"].items() if v["to_room_id"] not in identities}
            items = []
            for item in room["items"]:
                copy = item.copy()
                actions = []
                for action in item["interactions"]:
                    action = action.copy()
                    if action.get("teleport_to_room_id") in identities:
                        del action["teleport_to_room_id"]
                    actions.append(action)
                copy["interactions"] = actions
                items.append(copy)
            changed["items"] = items
            result.append(changed)
        return result

    def validate(self, users):
        self.validate_ids()
        require(self.has(1), "Global room 1 is missing.")
        counts = {}
        for room in self.data:
            owner = room.get("owner_id")
            require(users.has(owner), "Unknown room owner.")
            counts[owner] = counts.get(owner, 0) + 1
            require(counts[owner] <= self.config.MAX_ROOMS_PER_USER, "Owner room quota exceeded.")
            text(room.get("name"), self.config.MAX_NAME_LENGTH, "Room name")
            text(room.get("description"), self.config.MAX_DESCRIPTION_LENGTH, "Room description", empty=True)
            require(type(room.get("private")) is bool, "Invalid private flag.")
            require(type(room.get("exits")) is dict and type(room.get("items")) is list, "Invalid room collections.")
            for way, exit in room["exits"].items():
                require(way in DIRECTIONS and type(exit) is dict, "Invalid exit.")
                target = self.get(exit.get("to_room_id"))
                require(target["owner_id"] == owner, "Cross-owner exit.")
                require(type(exit.get("locked")) is bool, "Invalid exit lock.")
                text(exit.get("name"), self.config.MAX_NAME_LENGTH, "Exit name")
                text(exit.get("description"), self.config.MAX_DESCRIPTION_LENGTH, "Exit description", empty=True)
                text(exit.get("activation_text"), self.config.MAX_TEXT_LENGTH, "activation_text", empty=True)
        require(self.get(1)["owner_id"] == 1 and not self.get(1)["private"], "Invalid global home.")
        for user in users.data:
            require(self.get(user["home_room_id"])["owner_id"] == user["user_id"], "Invalid personal home.")
