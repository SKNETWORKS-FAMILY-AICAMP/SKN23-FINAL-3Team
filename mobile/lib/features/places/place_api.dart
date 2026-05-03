import '../../core/api/api_client.dart';
import '../../shared/models/place.dart';

class PlaceApi {
  const PlaceApi(this._client);

  final ApiClient _client;

  /// `GET /api/places/search?query=&category=&city=&pet_id=&lat=&lng=` — 일반 장소 검색.
  ///
  /// **`lat`/`lng` 는 Optional**. 백엔드 `/places/search` (2026-05-04 검증) 가
  /// 아직 사용자 GPS 좌표를 직접 받지 않음 — landmark 기반 (query 의 "강남" 같은
  /// 키워드 → 카카오 좌표) 만 처리. 본 메서드의 lat/lng 는 백엔드 확장 시점까지는
  /// 무해한 추가 query (FastAPI extra param 무시 또는 200 응답 유지).
  /// 백엔드 확장 후 자연 동작. ops-todo §1 #25 후속 작업.
  Future<List<PlaceCard>> search({
    required String query,
    String? category,
    String? city,
    int? petId,
    double? lat,
    double? lng,
  }) async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/places/search',
      queryParameters: {
        'query': query,
        if (category != null && category.isNotEmpty) 'category': category,
        if (city != null && city.isNotEmpty) 'city': city,
        // ignore: use_null_aware_elements
        if (petId != null) 'pet_id': petId,
        // ignore: use_null_aware_elements
        if (lat != null) 'lat': lat,
        // ignore: use_null_aware_elements
        if (lng != null) 'lng': lng,
      },
    );
    final list = (response.data?['places'] as List<dynamic>?) ?? const [];
    return list.cast<Map<String, dynamic>>().map(PlaceCard.fromJson).toList();
  }

  /// `GET /api/places/by-name?name=` — 5/2 신규, 시설 단건 조회
  Future<FacilityCard> byName(String name) async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/places/by-name',
      queryParameters: {'name': name},
    );
    return FacilityCard.fromJson(response.data!);
  }

  /// `GET /api/places/favorites` — 5/2 신규
  Future<List<PlaceFavoriteItem>> listFavorites() async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/places/favorites',
    );
    final items = (response.data?['items'] as List<dynamic>?) ?? const [];
    return items
        .cast<Map<String, dynamic>>()
        .map(PlaceFavoriteItem.fromJson)
        .toList();
  }

  /// `PATCH /api/places/{content_id}/favorite` — 5/2 신규, 토글 (옵티미스틱)
  Future<PlaceFavoriteToggle> toggleFavorite(String contentId) async {
    final response = await _client.raw.patch<Map<String, dynamic>>(
      '/places/$contentId/favorite',
    );
    return PlaceFavoriteToggle.fromJson(response.data!);
  }
}
