from models.storage import GameError, require


class Arguments:
    """Consume target tokens while retaining untouched final free text."""
    def __init__(self, source):
        self.source = source
        self.position = 0
        self.quoted = False

    def remaining(self):
        return self.source[self.position:].lstrip()

    def pop(self, optional=False):
        source = self.source
        while self.position < len(source) and source[self.position].isspace():
            self.position += 1
        if self.position == len(source):
            require(optional, "Missing argument.")
            return None
        self.quoted = source[self.position] == '"'
        if not self.quoted:
            start = self.position
            while self.position < len(source) and not source[self.position].isspace():
                require(source[self.position] != '"', "Quote a whole argument.")
                self.position += 1
            return source[start:self.position]
        self.position += 1
        result = []
        while self.position < len(source):
            char = source[self.position]
            self.position += 1
            if char == '"':
                require(self.position == len(source) or source[self.position].isspace(), "Space required after quote.")
                return "".join(result)
            if char == "\\":
                require(self.position < len(source) and source[self.position] in '\\"', "Invalid escape.")
                char = source[self.position]
                self.position += 1
            result.append(char)
        raise GameError("Unterminated quote.")

    def rest(self):
        rest = self.remaining()
        require(bool(rest), "Missing text.")
        if rest.startswith('"'):
            value = self.pop()
            self.end()
            return value
        self.position = len(self.source)
        return rest

    def end(self):
        require(not self.remaining(), "Too many arguments.")


def identity(value):
    require(isinstance(value, str) and bool(value) and all('0' <= c <= '9' for c in value), "Expected a numeric id.")
    result = int(value)
    require(result > 0, "Id must be positive.")
    return result


def toggle(value, current):
    require(value is None or value.lower() in ("on", "off"), "Use on or off.")
    return not current if value is None else value.lower() == "on"
