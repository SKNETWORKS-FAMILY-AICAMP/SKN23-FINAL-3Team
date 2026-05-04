/// 백엔드 `schemas/chat_message.py PlaceCard` 와 1:1.
/// 장소추천 의도 응답에 첨부되는 카드.
class PlaceCard {
  const PlaceCard({
    required this.name,
    this.address = '',
    this.category = '',
    this.subCategory = '',
    this.contentId = '',
    this.lat = 0.0,
    this.lng = 0.0,
    this.tel = '',
    this.conditions = '',
    this.petZone = '',
    this.petSize = '',
    this.hasParking = '',
    this.operation = '',
    this.indoor = '',
    this.outdoor = '',
    this.description = '',
    this.firstimage = '',
    this.image = '',
    this.reason = '',
    this.similarity = 0.0,
    this.finalScore = 0.0,
  });

  final String name;
  final String address;
  final String category;
  final String subCategory;
  final String contentId;
  final double lat;
  final double lng;
  final String tel;
  final String conditions;
  final String petZone;
  final String petSize;
  final String hasParking;
  final String operation;
  final String indoor;
  final String outdoor;
  final String description;
  final String firstimage;
  final String image;
  final String reason;
  final double similarity;
  final double finalScore;

  /// 카드 표시용 이미지 — `image` 우선, 없으면 `firstimage`.
  String? get imageUrl {
    if (image.isNotEmpty) return image;
    if (firstimage.isNotEmpty) return firstimage;
    return null;
  }

  factory PlaceCard.fromJson(Map<String, dynamic> json) {
    return PlaceCard(
      name: json['name'] as String,
      address: json['address'] as String? ?? '',
      category: json['category'] as String? ?? '',
      subCategory: json['sub_category'] as String? ?? '',
      contentId: json['content_id'] as String? ?? '',
      lat: (json['lat'] as num?)?.toDouble() ?? 0.0,
      lng: (json['lng'] as num?)?.toDouble() ?? 0.0,
      tel: json['tel'] as String? ?? '',
      conditions: json['conditions'] as String? ?? '',
      petZone: json['pet_zone'] as String? ?? '',
      petSize: json['pet_size'] as String? ?? '',
      hasParking: json['has_parking'] as String? ?? '',
      operation: json['operation'] as String? ?? '',
      indoor: json['indoor'] as String? ?? '',
      outdoor: json['outdoor'] as String? ?? '',
      description: json['description'] as String? ?? '',
      firstimage: json['firstimage'] as String? ?? '',
      image: json['image'] as String? ?? '',
      reason: json['reason'] as String? ?? '',
      similarity: (json['similarity'] as num?)?.toDouble() ?? 0.0,
      finalScore: (json['final_score'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

/// 백엔드 `schemas/chat_message.py FacilityCard` 와 1:1.
/// 시설정보 의도 응답 단일 카드.
class FacilityCard {
  const FacilityCard({
    required this.name,
    this.address = '',
    this.category = '',
    this.subCategory = '',
    this.contentId = '',
    this.lat = 0.0,
    this.lng = 0.0,
    this.tel = '',
    this.operation = '',
    this.hasParking = '',
    this.indoor = '',
    this.outdoor = '',
    this.conditions = '',
    this.description = '',
    this.firstimage = '',
    this.image = '',
    this.entranceFeeAmount,
    this.entranceFeeType = 'unknown',
    this.extraFeeAmount,
    this.extraFeeType = 'unknown',
    this.matchSource = 'vector',
    this.matchConfidence = 0.0,
  });

  final String name;
  final String address;
  final String category;
  final String subCategory;
  final String contentId;
  final double lat;
  final double lng;
  final String tel;
  final String operation;
  final String hasParking;
  final String indoor;
  final String outdoor;
  final String conditions;
  final String description;
  /// 백엔드 by-name 응답이 image 필드를 추가할 시 자동 picking (R3 #56, 2026-05-05).
  /// 현재 운영 응답엔 부재 — 빈 문자열 fallback. 향후 백엔드 확장 시 mobile 변경 X.
  final String firstimage;
  final String image;
  final int? entranceFeeAmount;
  final String entranceFeeType;
  final int? extraFeeAmount;
  final String extraFeeType;
  final String matchSource;
  final double matchConfidence;

  /// PlaceCard.imageUrl 와 동일한 우선순위 — image > firstimage > null.
  String? get imageUrl {
    if (image.isNotEmpty) return image;
    if (firstimage.isNotEmpty) return firstimage;
    return null;
  }

  factory FacilityCard.fromJson(Map<String, dynamic> json) {
    return FacilityCard(
      name: json['name'] as String,
      address: json['address'] as String? ?? '',
      category: json['category'] as String? ?? '',
      subCategory: json['sub_category'] as String? ?? '',
      contentId: json['content_id'] as String? ?? '',
      lat: (json['lat'] as num?)?.toDouble() ?? 0.0,
      lng: (json['lng'] as num?)?.toDouble() ?? 0.0,
      tel: json['tel'] as String? ?? '',
      operation: json['operation'] as String? ?? '',
      hasParking: json['has_parking'] as String? ?? '',
      indoor: json['indoor'] as String? ?? '',
      outdoor: json['outdoor'] as String? ?? '',
      conditions: json['conditions'] as String? ?? '',
      description: json['description'] as String? ?? '',
      firstimage: json['firstimage'] as String? ?? '',
      image: json['image'] as String? ?? '',
      entranceFeeAmount: json['entrance_fee_amount'] as int?,
      entranceFeeType: json['entrance_fee_type'] as String? ?? 'unknown',
      extraFeeAmount: json['extra_fee_amount'] as int?,
      extraFeeType: json['extra_fee_type'] as String? ?? 'unknown',
      matchSource: json['match_source'] as String? ?? 'vector',
      matchConfidence: (json['match_confidence'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

/// `PATCH /api/places/{content_id}/favorite` 응답.
class PlaceFavoriteToggle {
  const PlaceFavoriteToggle({
    required this.contentId,
    required this.isFavorite,
    this.favoritedAt,
  });

  final String contentId;
  final bool isFavorite;
  final DateTime? favoritedAt;

  factory PlaceFavoriteToggle.fromJson(Map<String, dynamic> json) {
    return PlaceFavoriteToggle(
      contentId: json['content_id'] as String,
      isFavorite: json['is_favorite'] as bool,
      favoritedAt: json['favorited_at'] == null
          ? null
          : DateTime.parse(json['favorited_at'] as String),
    );
  }
}

/// `GET /api/places/favorites` items.
class PlaceFavoriteItem {
  const PlaceFavoriteItem({
    required this.contentId,
    required this.name,
    this.subCategory = '',
    required this.favoritedAt,
  });

  final String contentId;
  final String name;
  final String subCategory;
  final DateTime favoritedAt;

  factory PlaceFavoriteItem.fromJson(Map<String, dynamic> json) {
    return PlaceFavoriteItem(
      contentId: json['content_id'] as String,
      name: json['name'] as String,
      subCategory: json['sub_category'] as String? ?? '',
      favoritedAt: DateTime.parse(json['favorited_at'] as String),
    );
  }
}
