from models.storage import require, GameError
from models.rooms import DIRECTIONS, ALIASES, OPPOSITE, direction
from models.properties import display_name
from modules.command_parser import identity, toggle
from views import game_view


class RoomController:
    def __init__(self, world, sessions, notifications):
        self.world, self.sessions, self.notifications = world, sessions, notifications
        self.rooms = world.rooms

    def editable(self, session, room_id=None):
        room = self.rooms.get(session.room_id if room_id is None else room_id)
        require(session.can_edit(room), "You do not own this room.")
        return room

    def view(self, session):
        room_id = session.room_id
        room = self.rooms.get(room_id)
        yield from game_view.room_header(room)
        exits = []
        for way in DIRECTIONS:
            room = self.rooms.get(room_id)
            require(session.can_enter(room) and session.room_id == room_id, "Room view changed; look again.")
            if way in room["exits"]:
                exits.append(game_view.exit_line(way, room["exits"][way]))
        if exits:
            yield "Exits:\n"
            yield from exits
        for label, creature in (("Items", False), ("Creatures", True)):
            entries = []
            for item_id in [i["id"] for i in self.rooms.get(room_id)["items"]]:
                room = self.rooms.get(room_id)
                require(session.can_enter(room) and session.room_id == room_id, "Room view changed; look again.")
                try:
                    item = self.world.items.get(room_id, item_id)
                except GameError:
                    continue
                if (bool(item.get("creature")) == creature and
                        session.properties.allowed(session, room["owner_id"], item["visible_if"])):
                    entries.append(game_view.room_item_line(item))
            if entries:
                yield label + ":\n"
                yield from entries
        yield "Here: " + ", ".join(s.name() for s in self.sessions.live() if s.room_id == room_id) + "\n\n"

    def move(self, session, destination_id, way=None):
        destination = self.rooms.get(destination_id)
        require(session.can_enter(destination), "That room is private.")
        old = session.room_id
        if old == destination_id:
            return
        self.notifications.room(old, game_view.presence(session.name(), "leaves" + (" " + way if way else "")), session)
        session.room_id = destination_id
        reverse = OPPOSITE.get(way)
        entry = destination["exits"].get(reverse)
        arrival = "arrives from the " + reverse if entry and entry["to_room_id"] == old else "arrives"
        self.notifications.room(destination_id, game_view.presence(session.name(), arrival), session)

    def travel(self, session, verb, args):
        if verb in DIRECTIONS or verb == "go":
            way = direction(args.pop()) if verb == "go" else verb
            args.end()
            exit = self.rooms.get(session.room_id)["exits"].get(way)
            require(exit is not None, "There is no exit that way.")
            require(not exit["locked"], "That exit is locked.")
            self.move(session, exit["to_room_id"], way)
            return self.with_text(exit["activation_text"], self.view(session))
        if verb == "join":
            player = self.sessions.named(args.pop()); args.end()
            destination = player.room_id
        else:
            had_to = args.remaining().lower().startswith("to ")
            values = []
            while args.remaining():
                values.append(args.pop().lower())
            if verb == "home":
                require(not values, "Home takes no arguments.")
                values = ["home"]
            if values and values[0] == "to":
                values = values[1:]
            if values == ["global", "home"]:
                destination = 1
            elif values == ["home"]:
                require(session.user_id is not None, "Guests have no personal home.")
                destination = session.user()["home_room_id"]
            else:
                require(verb == "teleport" and had_to and len(values) == 1, "Use /teleport to <id>, home or global home.")
                destination = identity(values[0])
        self.move(session, destination)
        return self.view(session)

    def with_text(self, message, lines):
        if message:
            yield message + "\n"
        yield from lines

    def evacuate(self, room_ids):
        for visitor in self.sessions.live():
            if visitor.room_id in room_ids:
                self.move(visitor, 1)
                visitor.reply(self.view(visitor))

    def build(self, session, verb, args):
        if verb == "room-unlock-rules":
            room = self.editable(session)
            operation = args.pop().lower()
            if operation == "clear":
                args.end(); self.rooms.unlock_rules(room["room_id"], operation, homes=self.home_ids())
            else:
                rule = [args.pop(), args.pop().lower(), self.property_value(args)]
                args.end(); self.rooms.unlock_rules(room["room_id"], operation, rule, self.home_ids())
            return "Updated.\n"
        if verb == "destroy":
            require(args.pop().lower() == "room", "Expected room <id>.")
            room_id = identity(args.pop()); args.end()
            self.editable(session, room_id)
            require(room_id != 1 and not any(u["home_room_id"] == room_id for u in self.world.users.data),
                    "Global home and personal homes cannot be deleted.")
            prepared = self.rooms.prepare_delete([room_id])
            self.evacuate([room_id])
            self.rooms.publish(prepared)
            return "Room deleted.\n"
        room = self.editable(session)
        if verb == "dig":
            way = args.pop()
            if args.remaining().lower().startswith("to "):
                args.pop()
                target = identity(args.pop()); args.end()
                result = self.rooms.dig(room["room_id"], way, target_id=target)
            else:
                result = self.rooms.dig(room["room_id"], way, name=args.rest())
            return "Linked room " + str(result) + ".\n"
        if verb == "undig":
            way = args.pop(); args.end()
            self.rooms.edit_exit(room["room_id"], way)
        elif verb == "private":
            value = toggle(args.pop(True), room["private"]); args.end()
            require(not value or room["room_id"] not in self.home_ids(), "Home rooms are permanently public.")
            self.rooms.edit(room["room_id"], "private", value)
            if value:
                for visitor in self.sessions.live():
                    if visitor.room_id == room["room_id"] and not visitor.can_enter(self.rooms.get(room["room_id"])):
                        self.move(visitor, 1)
                        visitor.reply(self.view(visitor))
        elif verb == "sethome":
            args.end()
            require(session.user_id is not None, "Guests have no personal home.")
            require(not room["private"] and not room["unlocked_if"], "Homes must be public and have no unlock rules.")
            self.world.users.set_home(session.user_id, room)
        elif verb in ("lock", "unlock"):
            way = args.pop(); args.end()
            self.rooms.edit_exit(room["room_id"], way, "locked", verb == "lock")
        elif verb == "message":
            way = args.pop()
            self.rooms.edit_exit(room["room_id"], way, "activation_text", args.rest())
        else:
            target = args.pop()
            field = "name" if verb == "rename" else "description"
            if target.lower() == "here":
                self.rooms.edit(room["room_id"], field, args.rest())
            elif target.lower() in DIRECTIONS or target.lower() in ALIASES:
                self.rooms.edit_exit(room["room_id"], target, field, args.rest())
            else:
                self.world.items.edit(room["room_id"], target, field, args.rest())
        return "Updated.\n"

    def inspect(self, session, verb, args):
        if verb == "whoami":
            args.end()
            return game_view.user_entry(session.user()) if session.user_id else session.name() + " (guest)\n"
        if verb == "who":
            args.end()
            return self.who(session)
        if verb in ("rooms", "items"):
            require(session.user_id is not None, "Log in as a user first.")
            name = args.pop(True); args.end()
            owner = self.world.users.named(name)["user_id"] if name else session.user_id
            return self.list_owned(session, owner, verb == "items")
        room = self.rooms.get(session.room_id)
        if verb == "look" and not args.remaining():
            return self.view(session)
        if verb == "exits":
            args.end()
            return (game_view.exit_line(k, v) for k, v in room["exits"].items())
        if verb == "look":
            require(args.pop().lower() == "at", "Use /look at <target>.")
        target = args.pop(); args.end()
        if target.lower() == "self":
            return self.properties_view(session, session)
        if target.lower() in DIRECTIONS or target.lower() in ALIASES:
            way = direction(target)
            exit = room["exits"].get(way)
            require(exit is not None, "No such exit.")
            result = exit["name"] + "\n" + exit["description"] + "\n"
            if verb == "examine":
                result += "Owner: {} Locked: {}\n".format(room["owner_id"], exit["locked"])
                destination = self.rooms.get(exit["to_room_id"])
                if session.can_enter(destination):
                    result += "Destination: " + str(destination["room_id"]) + "\n"
            return result
        try:
            item = self.world.items.get(session.room_id, target)
        except GameError as error:
            if str(error) != "No such item." or verb != "look":
                raise
            player = self.sessions.named(target)
            require(player.room_id == session.room_id, "Player is not here.")
            return self.properties_view(session, player)
        require(session.properties.allowed(session, room["owner_id"], item["visible_if"]), "No such item.")
        return self.item_view(session, item, verb == "examine")

    def item_view(self, session, item, detailed=False):
        yield item["name"] + "\n"
        yield item["description"] + "\n"
        if detailed:
            yield "Item {} in room {}, owner {}\n".format(item["id"], session.room_id, self.rooms.get(session.room_id)["owner_id"])
        actions = [action for action in item["interactions"] if
                   session.properties.allowed(session, self.rooms.get(session.room_id)["owner_id"], action["available_if"])]
        if actions:
            yield "Actions:\n"
            for action in actions:
                yield game_view.action_entry(action, detailed and session.can_edit(self.rooms.get(session.room_id)))

    def properties_view(self, viewer, target):
        label = "Your" if viewer is target else target.name() + "'s"
        lines = [label + " properties:\n"]
        values = target.properties.values(target)
        if values:
            lines.extend("  {} (owner {}): {}\n".format(display_name(key), owner, value)
                         for owner, key, value in values)
        else:
            lines.append("  None.\n")
        return lines

    def property_value(self, args):
        value = args.pop()
        return value if args.quoted or not value.lstrip("-").isdigit() else int(value)

    def home_ids(self):
        return [user["home_room_id"] for user in self.world.users.data]

    def who(self, viewer):
        for player in self.sessions.live():
            room = self.rooms.get(player.room_id)
            location = room["name"] + " [" + str(room["room_id"]) + "]" if viewer.can_enter(room) else "[private]"
            yield (player.name() + " — " + location + "\n", room["room_id"]) if viewer.can_enter(room) else player.name() + " — [private]\n"

    def list_owned(self, viewer, owner, items=False):
        for room_id in [r["room_id"] for r in self.rooms.owned(owner)]:
            if not self.rooms.has(room_id):
                continue
            room = self.rooms.get(room_id)
            if not viewer.can_enter(room):
                continue
            if not items:
                yield (game_view.room_entry(room), room_id)
            else:
                for item_id in [i["id"] for i in room["items"]]:
                    if not self.rooms.has(room_id) or not viewer.can_enter(self.rooms.get(room_id)):
                        break
                    try:
                        item = self.world.items.get(room_id, item_id)
                    except GameError:
                        continue
                    if viewer.properties.allowed(viewer, room["owner_id"], item["visible_if"]):
                        yield (game_view.item_entry(room_id, item), room_id)
