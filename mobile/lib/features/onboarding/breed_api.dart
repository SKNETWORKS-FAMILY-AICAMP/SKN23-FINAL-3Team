import '../../core/api/api_client.dart';
import '../../shared/models/breed.dart';

class BreedApi {
  const BreedApi(this._client);

  final ApiClient _client;

  /// `GET /api/breeds` (전체) / `?top10=true` / `?search=`.
  Future<List<Breed>> list({bool? top10, String? search}) async {
    final query = <String, dynamic>{
      if (top10 == true) 'top10': true,
      if (search != null && search.isNotEmpty) 'search': search,
    };
    final response = await _client.raw.get<List<dynamic>>(
      '/breeds',
      queryParameters: query.isEmpty ? null : query,
    );
    return (response.data ?? const [])
        .cast<Map<String, dynamic>>()
        .map(Breed.fromJson)
        .toList();
  }
}
