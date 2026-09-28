import errno
import gc
import json
import os


class GameError(Exception):
    """An expected, safe-to-display command error."""


def require(condition, message):
    if not condition:
        raise GameError(message)


def positive(value):
    return type(value) is int and value > 0


def text(value, limit, label="Text", empty=False):
    require(isinstance(value, str), label + " must be text.")
    require((empty or bool(value.strip())) and len(value) <= limit,
            label + " must be " + ("0" if empty else "1") + "-" + str(limit) + " characters.")
    require(not any(ord(c) < 32 or 127 <= ord(c) < 160 for c in value),
            label + " contains control characters.")
    return value


def memory_guard(config):
    gc.collect()
    require(gc.mem_free() >= config.MIN_FREE_MEMORY, "Memory is low; cannot grow the world.")


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError as error:
        if error.args[0] == errno.ENOENT:
            return False
        raise


class Storage:
    def __init__(self, path):
        self.path = path
        self.dirty = False
        self.data = None

    def load(self):
        with open(self.path, "r") as stream:
            self.data = json.load(stream)
        self.dirty = False

    def write(self, stream):
        json.dump(self.data, stream, separators=(",", ":"))

    def save_if_dirty(self):
        if not self.dirty:
            return False
        with open(self.path + ".tmp", "w") as stream:
            self.write(stream)
        os.rename(self.path + ".tmp", self.path)
        self.dirty = False
        return True

    def publish(self, data):
        """Publish an already prepared replacement without further allocation."""
        self.data = data
        self.dirty = True


class Records(Storage):
    id_field = "id"

    def __init__(self, path, config):
        super().__init__(path)
        self.config = config
        self.data = []
        self.next_id = 1

    def validate_ids(self):
        require(type(self.data) is list, "Expected a record array: " + self.path)
        seen = set()
        for record in self.data:
            require(type(record) is dict, "Invalid record in " + self.path)
            identity = record.get(self.id_field)
            require(positive(identity) and identity not in seen, "Invalid or duplicate record id.")
            seen.add(identity)
        self.next_id = max(list(seen) + [0]) + 1

    def get(self, identity):
        require(positive(identity), "Invalid id.")
        for record in self.data:
            if record[self.id_field] == identity:
                return record
        raise GameError("No such record: " + str(identity))

    def has(self, identity):
        return positive(identity) and any(r[self.id_field] == identity for r in self.data)

    def prepare_replace(self, identity, replacement):
        return [replacement if r[self.id_field] == identity else r for r in self.data]

    def update(self, identity, field, value):
        record = self.get(identity)
        if record[field] == value:
            return False
        if isinstance(value, str) and len(value.encode()) > len(str(record[field]).encode()):
            memory_guard(self.config)
        changed = record.copy()
        changed[field] = value
        self.publish(self.prepare_replace(identity, changed))
        return True
