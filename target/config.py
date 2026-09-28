AP_SSID = "PICO MUD"

# These defaults are public on GitHub. Change AP_PASSWORD, ADMIN_NAME,
# ADMIN_PASSWORD and PASSWORD_SALT before the first boot of a private MUD.
# Changing PASSWORD_SALT later invalidates existing password hashes.
AP_PASSWORD = "MultiUserDungeon"
ADMIN_NAME = "admin"
ADMIN_PASSWORD = "changeme"
PASSWORD_SALT = "..."

TELNET_PORT = 8888
MAX_CLIENTS = 6
IDLE_TIMEOUT = 900  # seconds
WELCOME_TEXT = "Welcome to PICO MUD!\nExplore, build and meet other players. Type /help for commands."

SAVE_INTERVAL = 60  # seconds between dirty-model saves
MAX_USERS = 15
MAX_ROOMS_PER_USER = 10
MAX_ITEMS_PER_ROOM = 5
MAX_INTERACTIONS_PER_ITEM = 2
MAX_CRON_JOBS_PER_ITEM = 3
MAX_NAME_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 600  # room, item and exit descriptions
MAX_TEXT_LENGTH = 250
MAX_MAILS = 10
MIN_FREE_MEMORY = 32768  # bytes

# Fixed device memory budget, not an operator tuning setting. Measured in bytes,
# allowing a full UTF-8 command (including future mail title and message fields).
MAX_LINE_LENGTH = 2048
