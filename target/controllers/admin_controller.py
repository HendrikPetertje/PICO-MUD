import gc
from models.storage import require
from modules.command_parser import toggle
from views import game_view


class AdminController:
    def __init__(self, world, sessions, rooms):
        self.world, self.sessions, self.rooms = world, sessions, rooms

    def handle(self, session, verb, args):
        if verb == "uptime":
            args.end(); gc.collect()
            return ("Uptime: {}s\nFree heap: {} bytes\nConnections: {}/{}\nUsers: {}/{}\nRooms: {}/{} ({} per user)\n".format(
                self.world.elapsed_ms // 1000, gc.mem_free(), len(self.sessions.sessions), self.world.config.MAX_CLIENTS,
                len(self.world.users.data), self.world.config.MAX_USERS, len(self.world.rooms.data),
                self.world.config.MAX_USERS * self.world.config.MAX_ROOMS_PER_USER, self.world.config.MAX_ROOMS_PER_USER))
        require(session.admin(), "Admin permission required.")
        if verb == "save":
            args.end(); return "\n".join(self.world.save()) + "\n"
        if verb == "users":
            args.end(); return self.listing(session)
        if verb == "boot":
            target = self.sessions.named(args.pop()); args.end()
            self.sessions.kick(target, "Disconnected by an admin.\n")
            return "Player disconnected.\n"
        operation = args.pop().lower()
        name = args.pop()
        if operation == "create":
            password = args.pop()
            flag = args.pop(True); args.end()
            require(flag is None or flag.lower() == "admin", "Optional flag must be admin.")
            user = self.world.create_user(name, password, flag is not None)
            return "Created user {} with home {}.\n".format(user["user_id"], user["home_room_id"])
        user = self.world.users.named(name)
        identity = user["user_id"]
        if operation == "password":
            password = args.pop(); args.end()
            self.world.users.set_password(identity, password)
        elif operation == "admin":
            value = toggle(args.pop(True), user["admin"]); args.end()
            self.world.users.set_flag(identity, "admin", value)
            target = self.sessions.by_user.get(identity)
            if target and not target.can_enter(self.world.rooms.get(target.room_id)):
                self.rooms.move(target, 1)
                target.reply(self.rooms.view(target))
        elif operation in ("ban", "unban"):
            args.end()
            self.world.users.set_flag(identity, "banned", operation == "ban")
            if operation == "ban" and identity in self.sessions.by_user:
                self.sessions.kick(self.sessions.by_user[identity], "You have been banned.\n")
        else:
            require(operation == "remove", "Unknown user operation.")
            args.end(); require(identity != 1, "User 1 cannot be removed.")
            prepared = self.world.prepare_remove_user(identity)
            # Keep identity available for departure formatting until the user is removed.
            target = self.sessions.by_user.get(identity)
            if target:
                self.sessions.kick(target, "Your account was removed.\n")
            room_ids = prepared[0]
            self.rooms.evacuate(room_ids)
            self.world.remove_user(identity, prepared)
        return "User updated.\n"

    def listing(self, viewer):
        for identity in [u["user_id"] for u in self.world.users.data]:
            require(viewer.admin(), "Admin permission required.")
            if self.world.users.has(identity):
                yield game_view.user_entry(self.world.users.get(identity))
