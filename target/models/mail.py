import json
from models.storage import Storage, require, positive, text, memory_guard


class Mail(Storage):
    def __init__(self, path, config):
        super().__init__(path)
        self.config = config
        self.data = {}

    def load(self):
        super().load()
        require(type(self.data) is dict, "Invalid mailbox object.")
        converted = {}
        for key, inbox in self.data.items():
            require(type(key) is str and key.isdigit() and str(int(key)) == key and int(key) > 0,
                    "Invalid mailbox id.")
            converted[int(key)] = inbox
        self.data = converted

    def write(self, stream):
        stream.write("{")
        first = True
        for identity, inbox in self.data.items():
            if not first:
                stream.write(",")
            first = False
            json.dump(str(identity), stream)
            stream.write(":")
            json.dump(inbox, stream, separators=(",", ":"))
        stream.write("}")

    def inbox(self, user_id):
        return self.data.get(user_id, [])

    def send(self, sender, recipient, title, message):
        require(positive(sender) and positive(recipient), "Invalid mail identity.")
        text(title, self.config.MAX_NAME_LENGTH, "Title")
        text(message, self.config.MAX_TEXT_LENGTH, "Message")
        inbox = self.inbox(recipient)
        require(len(inbox) < self.config.MAX_MAILS, "Recipient inbox is full.")
        memory_guard(self.config)
        data = self.data.copy()
        data[recipient] = inbox + [{"from_user_id": sender, "title": title, "message": message}]
        self.publish(data)

    def read(self, identity, number):
        inbox = self.inbox(identity)
        require(positive(number) and number <= len(inbox), "No such mail number.")
        return inbox[number - 1].copy()

    def delete(self, identity, number):
        self.read(identity, number)
        inbox = self.inbox(identity)
        data = self.data.copy()
        data[identity] = inbox[:number - 1] + inbox[number:]
        self.publish(data)

    def prepare_remove_user(self, identity):
        return {key: [m for m in inbox if m["from_user_id"] != identity]
                for key, inbox in self.data.items() if key != identity}

    def validate(self, users):
        for identity, inbox in self.data.items():
            require(users.has(identity), "Unknown inbox owner.")
            require(type(inbox) is list and len(inbox) <= self.config.MAX_MAILS, "Invalid inbox.")
            for message in inbox:
                require(type(message) is dict and users.has(message.get("from_user_id")), "Unknown mail sender.")
                text(message.get("title"), self.config.MAX_NAME_LENGTH, "Mail title")
                text(message.get("message"), self.config.MAX_TEXT_LENGTH, "Mail message")
