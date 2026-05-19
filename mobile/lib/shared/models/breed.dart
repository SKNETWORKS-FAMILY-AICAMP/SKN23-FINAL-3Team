import 'enums.dart';

/// 백엔드 `schemas/breed.py BreedResponse` 와 1:1.
class Breed {
  const Breed({
    required this.id,
    required this.nameKo,
    required this.nameEn,
    required this.top10,
    this.size,
    this.activityLevel,
    this.temperament,
    this.breedGroup,
    this.imageUrl,
  });

  final int id;
  final String nameKo;
  final String nameEn;
  final bool top10;
  final BreedSize? size;
  final String? activityLevel;
  final String? temperament;
  final String? breedGroup;
  final String? imageUrl;

  factory Breed.fromJson(Map<String, dynamic> json) {
    return Breed(
      id: json['id'] as int,
      nameKo: json['name_ko'] as String,
      nameEn: json['name_en'] as String,
      top10: json['top10'] as bool,
      size: BreedSize.fromWire(json['size'] as String?),
      activityLevel: json['activity_level'] as String?,
      temperament: json['temperament'] as String?,
      breedGroup: json['breed_group'] as String?,
      imageUrl: json['image_url'] as String?,
    );
  }
}
