import binascii
import hashlib
from models.storage import Records, require, text, positive, memory_guard, GameError


class Users(Records):
    id_field = "user_id"

    def username(self, name):
        text(name, self.config.MAX_NAME_LENGTH, "Username")
        require(not name.isdigit() and not any(c.isspace() or c in '/"\\=' for c in name),
                "Username must be a nonnumeric single word without /, quotes, backslash or =.")
        require(name.lower() != "guest" and not name.lower().startswith("guest-"),
                "Guest names are reserved.")
        return name

    def named(self, name):
        for user in self.data:
            if user["name"].lower() == name.lower():
                return user
        raise GameError("Unknown user.")

    def password_hash(self, password):
        require(isinstance(password, str) and 0 < len(password) <= self.config.MAX_TEXT_LENGTH,
                "Invalid password length.")
        require(not any(ord(c) < 32 or 127 <= ord(c) < 160 for c in password),
                "Password contains control characters.")
        return binascii.hexlify(hashlib.sha256((self.config.PASSWORD_SALT + password).encode()).digest()).decode()

    def authenticate(self, name, password):
        try:
            user = self.named(name)
        except GameError:
            return None
        if user["banned"] or user["password"] != self.password_hash(password):
            return None
        return user

    def prepare_user(self, name, password, home_id, admin=False):
        self.username(name)
        require(len(self.data) < self.config.MAX_USERS, "User limit reached.")
        require(not any(u["name"].lower() == name.lower() for u in self.data), "Username already exists.")
        require(positive(home_id), "Invalid home id.")
        memory_guard(self.config)
        return {"user_id": self.next_id, "name": name, "password": self.password_hash(password),
                "admin": admin, "home_room_id": home_id, "banned": False}

    def set_password(self, identity, password):
        return self.update(identity, "password", self.password_hash(password))

    def set_flag(self, identity, field, value):
        require(field in ("admin", "banned") and type(value) is bool, "Invalid user flag.")
        require(identity != 1 or (field == "admin" and value) or (field == "banned" and not value),
                "User 1 must remain an unbanned admin.")
        return self.update(identity, field, value)

    def set_home(self, identity, room):
        require(room["owner_id"] == identity, "You must actually own your home room.")
        return self.update(identity, "home_room_id", room["room_id"])

    def validate(self):
        self.validate_ids()
        require(0 < len(self.data) <= self.config.MAX_USERS, "Invalid user count.")
        names = set()
        for user in self.data:
            name = self.username(user.get("name")).lower()
            require(name not in names, "Duplicate username.")
            names.add(name)
            digest = user.get("password")
            require(isinstance(digest, str) and len(digest) == 64 and
                    all(c in "0123456789abcdef" for c in digest), "Invalid password hash.")
            require(type(user.get("admin")) is bool and type(user.get("banned")) is bool,
                    "Invalid user flags.")
            require(positive(user.get("home_room_id")), "Invalid home id.")
        first = self.get(1)
        require(first["admin"] and not first["banned"], "User 1 must be an unbanned admin.")
