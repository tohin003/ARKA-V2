import os

# Unified memory database path
DEFAULT_MEMORY_DB_PATH = os.path.expanduser("~/.arka/memory/arka_memory.db")

# Feature flags
AUTO_UPDATE_ENV = "ARKA_MEMORY_AUTO_UPDATE"  # "1" to enable distiller
AUTO_UPDATE_DEFAULT = "1"
RECALL_ENV = "ARKA_MEMORY_RECALL"  # "1" to enable memory recall injection
RECALL_DEFAULT = "1"
INCLUDE_SENSITIVE_ENV = "ARKA_MEMORY_INCLUDE_SENSITIVE"  # "1" to include sensitive facts
INCLUDE_SENSITIVE_DEFAULT = "0"

# Retention defaults (days). None means keep indefinitely.
DEFAULT_FACT_TTL_DAYS = None
DEFAULT_EVENT_TTL_DAYS = 90
DEFAULT_EPISODE_TTL_DAYS = 180

# Recall defaults
RECALL_MAX_TOKENS = 1200
RECALL_MAX_FACTS = 16
RECALL_MAX_EPISODES = 3

# Housekeeping
HOUSEKEEPING_INTERVAL_HOURS = 24

# Safe predicates for auto-extracted facts
SAFE_PREDICATES = {
    "preference",
    "preferred_name",
    "name",
    "title",
    "pronouns",
    "timezone",
    "language",
    "theme",
}

# Sensitive keywords to avoid auto-storage
SENSITIVE_KEYWORDS = {
    "password",
    "passcode",
    "otp",
    "api key",
    "secret",
    "token",
    "private key",
    "seed phrase",
    "mnemonic",
    "credit card",
    "ssn",
}
