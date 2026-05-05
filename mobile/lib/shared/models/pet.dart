import 'enums.dart';

/// 백엔드 `schemas/pet.py PetResponse` 와 1:1.
class Pet {
  const Pet({
    required this.id,
    required this.userId,
    required this.breedId,
    required this.name,
    this.birthDate,
    this.gender,
    this.isNeutered,
    this.typeId,
    this.selectedTags,
    required this.createdAt,
    required this.updatedAt,
    this.age,
  });

  final int id;
  final int userId;
  final int breedId;
  final String name;
  final DateTime? birthDate;
  final PetGender? gender;
  final bool? isNeutered;
  final int? typeId;
  final List<dynamic>? selectedTags;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int? age;

  factory Pet.fromJson(Map<String, dynamic> json) {
    return Pet(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      breedId: json['breed_id'] as int,
      name: json['name'] as String,
      birthDate: _parseDate(json['birth_date']),
      gender: PetGender.fromWire(json['gender'] as String?),
      isNeutered: json['is_neutered'] as bool?,
      typeId: json['type_id'] as int?,
      selectedTags: json['selected_tags'] as List<dynamic>?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      age: json['age'] as int?,
    );
  }
}

/// `POST /api/pets` 요청 페이로드 (`PetCreate`).
class PetCreate {
  const PetCreate({
    required this.breedId,
    required this.name,
    this.birthDate,
    this.gender,
    this.isNeutered,
    this.typeId,
    this.selectedTags,
  });

  final int breedId;
  final String name;
  final DateTime? birthDate;
  final PetGender? gender;
  final bool? isNeutered;
  final int? typeId;
  final List<dynamic>? selectedTags;

  Map<String, dynamic> toJson() => {
        'breed_id': breedId,
        'name': name,
        if (birthDate != null) 'birth_date': _formatDate(birthDate!),
        if (gender != null) 'gender': gender!.wire,
        if (isNeutered != null) 'is_neutered': isNeutered,
        if (typeId != null) 'type_id': typeId,
        if (selectedTags != null) 'selected_tags': selectedTags,
      };
}

/// `PATCH /api/pets/{id}` 요청 페이로드 (`PetUpdate`).
class PetUpdate {
  const PetUpdate({
    this.breedId,
    this.name,
    this.birthDate,
    this.gender,
    this.isNeutered,
    this.typeId,
    this.selectedTags,
  });

  final int? breedId;
  final String? name;
  final DateTime? birthDate;
  final PetGender? gender;
  final bool? isNeutered;
  final int? typeId;
  final List<dynamic>? selectedTags;

  Map<String, dynamic> toJson() => {
        if (breedId != null) 'breed_id': breedId,
        if (name != null) 'name': name,
        if (birthDate != null) 'birth_date': _formatDate(birthDate!),
        if (gender != null) 'gender': gender!.wire,
        if (isNeutered != null) 'is_neutered': isNeutered,
        if (typeId != null) 'type_id': typeId,
        if (selectedTags != null) 'selected_tags': selectedTags,
      };
}

DateTime? _parseDate(Object? value) {
  if (value == null) return null;
  return DateTime.parse(value as String);
}

String _formatDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
