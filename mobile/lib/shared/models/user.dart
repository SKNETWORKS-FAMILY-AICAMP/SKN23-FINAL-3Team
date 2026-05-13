import 'enums.dart';
import 'pet.dart';

/// 백엔드 `schemas/user.py UserResponse` 와 1:1.
/// 5/2 신규: `primaryPetId` + `primaryPet` (nested PetResponse).
class User {
  const User({
    required this.id,
    required this.email,
    required this.nickname,
    this.gender,
    this.birthDate,
    this.profileId,
    required this.provider,
    this.typeId,
    this.typeName,
    this.primaryPetId,
    this.primaryPet,
    this.selectedTags,
    required this.createdAt,
    required this.updatedAt,
    this.age,
    this.profileImageUrl,
  });

  final int id;
  final String email;
  final String nickname;
  final Gender? gender;
  final DateTime? birthDate;
  final int? profileId;
  final String provider;
  final int? typeId;
  final String? typeName;
  final int? primaryPetId;
  final Pet? primaryPet;
  final List<dynamic>? selectedTags;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int? age;
  final String? profileImageUrl;

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      email: json['email'] as String,
      nickname: json['nickname'] as String,
      gender: Gender.fromWire(json['gender'] as String?),
      birthDate: _parseDate(json['birth_date']),
      profileId: json['profile_id'] as int?,
      provider: json['provider'] as String,
      typeId: json['type_id'] as int?,
      typeName: json['type_name'] as String?,
      primaryPetId: json['primary_pet_id'] as int?,
      primaryPet: json['primary_pet'] == null
          ? null
          : Pet.fromJson(json['primary_pet'] as Map<String, dynamic>),
      selectedTags: json['selected_tags'] as List<dynamic>?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
      age: json['age'] as int?,
      profileImageUrl: json['profile_image_url'] as String?,
    );
  }
}

/// `PATCH /api/users/{id}` 요청 (`UserUpdate`).
/// type_id 는 백엔드가 selected_tags 로부터 자동 재계산하므로 송신 필드에서 제외.
class UserUpdate {
  const UserUpdate({
    this.nickname,
    this.gender,
    this.birthDate,
    this.profileId,
    this.clearProfileId = false,
    this.primaryPetId,
    this.selectedTags,
  });

  final String? nickname;
  final Gender? gender;
  final DateTime? birthDate;
  final int? profileId;
  /// true 이면 profile_id: null 을 명시적으로 전송하여 프로필 사진 삭제.
  final bool clearProfileId;
  final int? primaryPetId;
  final List<dynamic>? selectedTags;

  Map<String, dynamic> toJson() => {
        if (nickname != null) 'nickname': nickname,
        if (gender != null) 'gender': gender!.wire,
        if (birthDate != null) 'birth_date': _formatDate(birthDate!),
        if (profileId != null) 'profile_id': profileId,
        if (clearProfileId) 'profile_id': null,
        if (primaryPetId != null) 'primary_pet_id': primaryPetId,
        if (selectedTags != null) 'selected_tags': selectedTags,
      };
}

DateTime? _parseDate(Object? value) {
  if (value == null) return null;
  return DateTime.parse(value as String);
}

String _formatDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
