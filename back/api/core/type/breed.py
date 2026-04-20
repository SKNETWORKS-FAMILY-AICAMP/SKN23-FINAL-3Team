import enum


class BreedSizeEnum(str, enum.Enum):
    """견종 크기 분류."""
    small = "small"
    medium = "medium"
    large = "large"


class ActivityLevelEnum(str, enum.Enum):
    """활동량 수준."""
    low = "low"
    medium = "medium"
    high = "high"
