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
    this.typeName,
    this.selectedTags,
    required this.createdAt,
    required this.updatedAt,
    this.age,
    this.imageId,
    this.imageUrl,
    this.breedName,
    this.englishPrompt,
    this.mustIncludeKeywords,
  });

  final int id;
  final int userId;
  final int breedId;
  final String name;
  final DateTime? birthDate;
  final PetGender? gender;
  final bool? isNeutered;
  final int? typeId;
  final String? typeName;
  final List<dynamic>? selectedTags;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int? age;
  final int? imageId;
  final String? imageUrl;

  /// 견종 한국어 이름 (백엔드 computed_field).
  final String? breedName;

  /// AI 프로필 분석 — 이미지 생성용 영문 외형 프롬프트.
  final String? englishPrompt;

  /// AI 프로필 분석 — 매 그림에 반드시 포함할 핵심 키워드.
  final List<String>? mustIncludeKeywords;

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
      typeName: json['type_name'] as String?,
      selectedTags: json['selected_tags'] as List<dynamic>?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      age: json['age'] as int?,
      imageId: json['image_id'] as int?,
      imageUrl: json['image_url'] as String?,
      breedName: json['breed_name'] as String?,
      englishPrompt: json['english_prompt'] as String?,
      mustIncludeKeywords: (json['must_include_keywords'] as List<dynamic>?)
          ?.map((e) => e as String)
          .toList(),
    );
  }
}

/// `POST /api/pets` 요청 페이로드 (`PetCreate`).
/// type_id 는 백엔드가 selected_tags 로부터 자동 계산하므로 송신 필드에서 제외.
class PetCreate {
  const PetCreate({
    required this.breedId,
    required this.name,
    this.birthDate,
    this.gender,
    this.isNeutered,
    this.selectedTags,
    this.imageId,
  });

  final int breedId;
  final String name;
  final DateTime? birthDate;
  final PetGender? gender;
  final bool? isNeutered;
  final List<dynamic>? selectedTags;
  final int? imageId;

  Map<String, dynamic> toJson() => {
        'breed_id': breedId,
        'name': name,
        if (birthDate != null) 'birth_date': _formatDate(birthDate!),
        if (gender != null) 'gender': gender!.wire,
        if (isNeutered != null) 'is_neutered': isNeutered,
        if (selectedTags != null) 'selected_tags': selectedTags,
        if (imageId != null) 'image_id': imageId,
      };
}

/// `PATCH /api/pets/{id}` 요청 페이로드 (`PetUpdate`).
/// type_id 는 백엔드가 selected_tags 로부터 자동 재계산하므로 송신 필드에서 제외.
class PetUpdate {
  const PetUpdate({
    this.breedId,
    this.name,
    this.birthDate,
    this.gender,
    this.isNeutered,
    this.selectedTags,
    this.imageId,
  });

  final int? breedId;
  final String? name;
  final DateTime? birthDate;
  final PetGender? gender;
  final bool? isNeutered;
  final List<dynamic>? selectedTags;
  final int? imageId;

  Map<String, dynamic> toJson() => {
        if (breedId != null) 'breed_id': breedId,
        if (name != null) 'name': name,
        if (birthDate != null) 'birth_date': _formatDate(birthDate!),
        if (gender != null) 'gender': gender!.wire,
        if (isNeutered != null) 'is_neutered': isNeutered,
        if (selectedTags != null) 'selected_tags': selectedTags,
        if (imageId != null) 'image_id': imageId,
      };
}

DateTime? _parseDate(Object? value) {
  if (value == null) return null;
  return DateTime.parse(value as String);
}

String _formatDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
