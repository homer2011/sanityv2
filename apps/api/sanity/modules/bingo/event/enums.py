from enum import Enum


class EventType(str, Enum):
    TRADITIONAL = "TRADITIONAL"
    LEVELS = "LEVELS"


class EventStatus(str, Enum):
    SCHEDULED = "SCHEDULED"  # Editable
    ACTIVE = "ACTIVE"  # Moderation only
    COMPLETED = "COMPLETED"  # Read only
