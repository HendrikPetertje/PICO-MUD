from models.storage import require, text


MAX_PROPERTIES_PER_OWNER = 6
MAX_PROPERTY_LENGTH = 15
OPERATORS = ("equals", "more_than", "less_than")


def property_value(value, effect=False):
    if type(value) is int:
        require((-100 if effect else 0) <= value <= 100, "Invalid property number.")
    else:
        text(value, MAX_PROPERTY_LENGTH, "Property value")
    return value


def property_name(value):
    text(value, MAX_PROPERTY_LENGTH, "Property name")
    require("a" <= value[0] <= "z" and
            all("a" <= char <= "z" or "0" <= char <= "9" or char == "_" for char in value) and
            "__" not in value and not value.endswith("_"), "Invalid property name.")
    return value


def display_name(value):
    return value.replace("_", " ").capitalize()


def condition(value):
    require(type(value) is list and len(value) == 3, "Invalid property condition.")
    property_name(value[0])
    require(value[1] in OPERATORS, "Invalid property condition operator.")
    value[2] = property_value(value[2])
    return value


def conditions(values):
    require(type(values) is list, "Invalid property conditions.")
    for entry in values:
        condition(entry)
    return values


def effect(value):
    require(type(value) is list and len(value) == 2, "Invalid property effect.")
    property_name(value[0])
    value[1] = property_value(value[1], True)
    return value


class Properties:
    def __init__(self):
        self.data = {}

    def clear(self, session):
        self.data.pop(session, None)

    def values(self, session):
        result = self.data.get(session, {})
        return [(owner, key, value) for owner, entries in result.items() for key, value in entries.items()]

    def allowed(self, session, owner, rules):
        if session.user_id == owner or session.admin():
            return True
        entries = self.data.get(session, {}).get(owner, {})
        for key, operator, target in rules:
            current = entries.get(key)
            if operator == "equals":
                if current != target:
                    return False
            elif type(current) is not int or type(target) is not int:
                return False
            elif operator == "more_than":
                if current <= target:
                    return False
            elif current >= target:
                return False
        return True

    def apply(self, session, owner, update):
        effect(update)
        owners = self.data.setdefault(session, {})
        entries = owners.setdefault(owner, {})
        key, update = update
        current = entries.get(key)
        if type(update) is int:
            require(current is None or type(current) is int, "Property has a different value type.")
            result = min(100, max(0, (current or 0) + update))
        else:
            result = update
        require(key in entries or len(entries) < MAX_PROPERTIES_PER_OWNER,
                "Property limit reached for this owner.")
        entries[key] = result
        return key, result
