import '../../core/api/api_client.dart';
import '../../shared/models/breed.dart';

class BreedApi {
  const BreedApi(this._client);

  final ApiClient _client;

  /// GET /api/breeds
  /// GET /api/breeds?top10=true
  /// GET /api/breeds?search=푸들
  Future<List<Breed>> list({bool top10 = false, String? search}) async {
    final keyword = search?.trim();

    final query = <String, dynamic>{
      if (top10) 'top10': true,
      if (keyword != null && keyword.isNotEmpty) 'search': keyword,
    };

    final response = await _client.raw.get<List<dynamic>>(
      '/breeds',
      queryParameters: query.isEmpty ? null : query,
    );

    return (response.data ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(Breed.fromJson)
        .toList();
  }
}
