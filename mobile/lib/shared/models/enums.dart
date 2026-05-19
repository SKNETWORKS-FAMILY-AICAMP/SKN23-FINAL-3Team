/// 백엔드 `core/type/gender.py` 와 1:1.
enum Gender {
  male('MALE'),
  female('FEMALE');

  const Gender(this.wire);

  final String wire;

  static Gender? fromWire(String? value) {
    if (value == null) return null;
    for (final g in Gender.values) {
      if (g.wire == value) return g;
    }
    return null;
  }
}

/// 백엔드 `PetGenderEnum` (현재 MALE/FEMALE 만, UI 라벨은 남아/여아).
enum PetGender {
  male('MALE', '남아'),
  female('FEMALE', '여아');

  const PetGender(this.wire, this.label);

  final String wire;
  final String label;

  static PetGender? fromWire(String? value) {
    if (value == null) return null;
    for (final g in PetGender.values) {
      if (g.wire == value) return g;
    }
    return null;
  }
}

/// 백엔드 `core/type/breed.py` 의 BreedSizeEnum.
enum BreedSize {
  small('small'),
  medium('medium'),
  large('large');

  const BreedSize(this.wire);

  final String wire;

  static BreedSize? fromWire(String? value) {
    if (value == null) return null;
    for (final s in BreedSize.values) {
      if (s.wire == value) return s;
    }
    return null;
  }
}
