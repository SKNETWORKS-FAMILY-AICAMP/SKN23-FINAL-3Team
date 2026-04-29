import enum


class GenderEnum(str, enum.Enum):
    """사용자 성별 Enum."""
    MALE = "MALE"
    FEMALE = "FEMALE"


class PetGenderEnum(str, enum.Enum):
    """반려동물 성별 Enum."""
    MALE = "MALE"
    FEMALE = "FEMALE"
