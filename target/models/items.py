from models.storage import require, text, positive, memory_guard, GameError


class Items:
    def __init__(self, rooms, config, reserved):
        self.rooms, self.config, self.reserved = rooms, config, reserved

    def get(self, room_id, target):
        items = self.rooms.get(room_id)["items"]
        if str(target).isdigit():
            matches = [i for i in items if i["id"] == int(target)]
        else:
            matches = [i for i in items if i["name"].lower() == str(target).lower()]
        require(bool(matches), "No such item.")
        require(len(matches) == 1, "Ambiguous item; use id: " + ", ".join(str(i["id"]) for i in matches))
        return matches[0]

    def _replace(self, room_id, items):
        room = self.rooms.get(room_id).copy()
        room["items"] = items
        self.rooms.publish(self.rooms.prepare_replace(room_id, room))

    def create(self, room_id, name):
        text(name, self.config.MAX_NAME_LENGTH, "Item name")
        items = self.rooms.get(room_id)["items"]
        require(len(items) < self.config.MAX_ITEMS_PER_ROOM, "Item limit reached.")
        memory_guard(self.config)
        identity = max([i["id"] for i in items] + [0]) + 1
        item = {"id": identity, "name": name, "description": "An unremarkable item.", "interactions": []}
        self._replace(room_id, items + [item])
        return identity

    def edit(self, room_id, identity, field, value):
        require(field in ("name", "description"), "Invalid item field.")
        text(value, self.config.MAX_NAME_LENGTH if field == "name" else self.config.MAX_DESCRIPTION_LENGTH)
        item = self.get(room_id, identity)
        if item[field] == value:
            return
        memory_guard(self.config)
        changed = item.copy()
        changed[field] = value
        self._replace(room_id, [changed if i["id"] == item["id"] else i for i in self.rooms.get(room_id)["items"]])

    def destroy(self, room_id, identity):
        item = self.get(room_id, identity)
        self._replace(room_id, [i for i in self.rooms.get(room_id)["items"] if i["id"] != item["id"]])

    def move(self, source_id, identity, destination_id):
        source, destination = self.rooms.get(source_id), self.rooms.get(destination_id)
        item = self.get(source_id, identity)
        require(source_id != destination_id, "Item is already in that room.")
        require(source["owner_id"] == destination["owner_id"], "Items cannot move between owners.")
        require(len(destination["items"]) < self.config.MAX_ITEMS_PER_ROOM, "Destination item limit reached.")
        memory_guard(self.config)
        moved = item.copy()
        moved["id"] = max([i["id"] for i in destination["items"]] + [item["id"]]) + 1
        src, dst = source.copy(), destination.copy()
        src["items"] = [i for i in source["items"] if i["id"] != item["id"]]
        dst["items"] = destination["items"] + [moved]
        prepared = [src if r["room_id"] == source_id else dst if r["room_id"] == destination_id else r
                    for r in self.rooms.data]
        self.rooms.publish(prepared)
        return moved["id"]

    def action_name(self, name):
        text(name, self.config.MAX_NAME_LENGTH, "Action")
        require(not any(c.isspace() or c in '/"\\=' for c in name), "Action must be one word.")
        require(name.lower() not in self.reserved, "Action conflicts with a command.")
        return name.lower()

    def action(self, item, name):
        for action in item["interactions"]:
            if action["action"].lower() == name.lower():
                return action
        raise GameError("This item has no such action.")

    def interaction(self, room_id, identity, operation, name, value=None):
        item = self.get(room_id, identity)
        name = self.action_name(name)
        actions = item["interactions"]
        existing = next((a for a in actions if a["action"] == name), None)
        if operation == "add":
            text(value, self.config.MAX_TEXT_LENGTH, "Flavor text")
            require(existing is not None or len(actions) < self.config.MAX_INTERACTIONS_PER_ITEM,
                    "Interaction limit reached.")
            if existing and existing["flavor_text"] == value:
                return
            memory_guard(self.config)
            changed = existing.copy() if existing else {"action": name}
            changed["flavor_text"] = value
        else:
            require(existing is not None, "No such interaction.")
            changed = existing.copy()
            if operation == "teleport":
                if value is not None:
                    self.rooms.get(value)
                if existing.get("teleport_to_room_id") == value:
                    return
                if value is not None:
                    memory_guard(self.config)
                if value is None:
                    changed.pop("teleport_to_room_id", None)
                else:
                    changed["teleport_to_room_id"] = value
            else:
                require(operation == "remove", "Invalid interaction operation.")
        updated = [changed if a["action"] == name else a for a in actions]
        if existing is None:
            updated.append(changed)
        if operation == "remove":
            updated = [a for a in actions if a["action"] != name]
        replacement = item.copy()
        replacement["interactions"] = updated
        self._replace(room_id, [replacement if i["id"] == item["id"] else i
                                for i in self.rooms.get(room_id)["items"]])

    def validate(self):
        for room in self.rooms.data:
            require(len(room["items"]) <= self.config.MAX_ITEMS_PER_ROOM, "Item quota exceeded.")
            seen = set()
            for item in room["items"]:
                require(type(item) is dict and positive(item.get("id")), "Invalid item.")
                require(item["id"] not in seen, "Duplicate local item id.")
                seen.add(item["id"])
                text(item.get("name"), self.config.MAX_NAME_LENGTH, "Item name")
                text(item.get("description"), self.config.MAX_DESCRIPTION_LENGTH, "Item description", empty=True)
                actions = item.get("interactions")
                require(type(actions) is list and len(actions) <= self.config.MAX_INTERACTIONS_PER_ITEM,
                        "Invalid interactions.")
                names = set()
                for action in actions:
                    require(type(action) is dict, "Invalid action record.")
                    name = self.action_name(action.get("action"))
                    require(name not in names and name == action["action"], "Duplicate or noncanonical action.")
                    names.add(name)
                    text(action.get("flavor_text"), self.config.MAX_TEXT_LENGTH, "Flavor text")
                    if "teleport_to_room_id" in action:
                        self.rooms.get(action["teleport_to_room_id"])
