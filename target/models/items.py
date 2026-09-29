from models.storage import require, text, positive, memory_guard, GameError
from models.properties import conditions, effect


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
        item = {"id": identity, "name": name, "description": "An unremarkable item.", "visible_if": [], "interactions": []}
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

    def rules(self, room_id, identity, field, operation, rule=None, action_name=None):
        item = self.get(room_id, identity)
        target = item if action_name is None else self.action(item, action_name)
        current = target[field]
        if operation == "clear":
            updated = []
        else:
            conditions([rule])
            if operation == "add":
                require(rule not in current, "That rule already exists.")
                updated = current + [rule]
            else:
                require(operation == "remove" and rule in current, "No such rule.")
                updated = [entry for entry in current if entry != rule]
        if updated == current:
            return False
        changed_item = item.copy()
        if action_name is None:
            changed_item[field] = updated
        else:
            changed_action = target.copy(); changed_action[field] = updated
            changed_item["interactions"] = [changed_action if entry["action"] == target["action"] else entry
                                            for entry in item["interactions"]]
        self._replace(room_id, [changed_item if entry["id"] == item["id"] else entry
                                for entry in self.rooms.get(room_id)["items"]])
        return True

    def property_effect(self, room_id, identity, field, value=None, action_name=None, cron_id=None):
        item = self.get(room_id, identity)
        if action_name is not None:
            target = self.action(item, action_name)
            entries, key = item["interactions"], "action"
        else:
            entries, key = item.get("cron_jobs", []), "id"
            target = next((job for job in entries if job["id"] == cron_id), None)
            require(target is not None, "No such cron job.")
        changed = target.copy()
        if value is None:
            if field not in changed:
                return False
            changed.pop(field, None)
        else:
            effect(value)
            if changed.get(field) == value:
                return False
            changed[field] = value
        changed_item = item.copy()
        changed_item["interactions" if action_name is not None else "cron_jobs"] = [
            changed if entry[key] == target[key] else entry for entry in entries]
        self._replace(room_id, [changed_item if entry["id"] == item["id"] else entry
                                for entry in self.rooms.get(room_id)["items"]])
        return True

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
            changed = existing.copy() if existing else {"action": name, "available_if": []}
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

    def creature(self, room_id, identity, value):
        item = self.get(room_id, identity)
        if bool(item.get("creature")) == value:
            return
        changed = item.copy()
        if value:
            memory_guard(self.config)
            changed["creature"] = True
        else:
            changed.pop("creature", None)
        self._replace(room_id, [changed if i["id"] == item["id"] else i
                                for i in self.rooms.get(room_id)["items"]])

    def cron(self, room_id, identity, operation, cron_id=None, field=None, value=None):
        item = self.get(room_id, identity)
        jobs = item.get("cron_jobs", [])
        if operation == "add":
            interval = value
            require(len(jobs) < self.config.MAX_CRON_JOBS_PER_ITEM, "Cron job limit reached.")
            text(field, self.config.MAX_NAME_LENGTH, "Cron job name")
            require(positive(interval), "Interval must be positive.")
            memory_guard(self.config)
            changed = {"id": max([job["id"] for job in jobs] + [0]) + 1,
                       "name": field, "interval_seconds": interval}
            updated = jobs + [changed]
        else:
            job = next((job for job in jobs if job["id"] == cron_id), None)
            require(job is not None, "No such cron job.")
            if operation == "remove":
                updated = [current for current in jobs if current["id"] != cron_id]
            else:
                changed = job.copy()
                if field == "interval_seconds":
                    require(positive(value), "Interval must be positive.")
                elif field == "name":
                    text(value, self.config.MAX_NAME_LENGTH, "Cron job name")
                else:
                    require(field in ("chat_out", "emote"), "Invalid cron job field.")
                    if value is not None:
                        text(value, self.config.MAX_TEXT_LENGTH, "Cron job " + field)
                if changed.get(field) == value:
                    return
                if value is None:
                    changed.pop(field, None)
                else:
                    memory_guard(self.config)
                    changed[field] = value
                updated = [changed if current["id"] == cron_id else current for current in jobs]
        replacement = item.copy()
        if updated:
            replacement["cron_jobs"] = updated
        else:
            replacement.pop("cron_jobs", None)
        self._replace(room_id, [replacement if i["id"] == item["id"] else i
                                for i in self.rooms.get(room_id)["items"]])

    def crons(self, item):
        return item.get("cron_jobs", [])

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
                require("creature" not in item or item["creature"] is True, "Invalid creature flag.")
                conditions(item.get("visible_if"))
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
                    conditions(action.get("available_if"))
                    if "set_variable" in action:
                        effect(action["set_variable"])
                    if "teleport_to_room_id" in action:
                        self.rooms.get(action["teleport_to_room_id"])
                jobs = item.get("cron_jobs", [])
                require(type(jobs) is list and len(jobs) <= self.config.MAX_CRON_JOBS_PER_ITEM,
                        "Invalid cron jobs.")
                job_ids = set()
                for job in jobs:
                    require(type(job) is dict and positive(job.get("id")) and job["id"] not in job_ids,
                            "Invalid or duplicate cron job.")
                    job_ids.add(job["id"])
                    text(job.get("name"), self.config.MAX_NAME_LENGTH, "Cron job name")
                    require(positive(job.get("interval_seconds")), "Invalid cron job interval.")
                    for field in ("chat_out", "emote"):
                        if field in job:
                            text(job[field], self.config.MAX_TEXT_LENGTH, "Cron job " + field)
                    if "set_variable" in job:
                        effect(job["set_variable"])
