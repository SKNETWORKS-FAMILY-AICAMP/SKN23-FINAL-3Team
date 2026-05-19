import '../../core/api/api_client.dart';
import '../../shared/models/keyword.dart';

/// 키워드 카테고리 — 백엔드 `Keyword.category` ("PET" | "USER").
enum KeywordCategory {
  pet('PET'),
  user('USER');

  const KeywordCategory(this.wire);

  final String wire;
}

class KeywordApi {
  const KeywordApi(this._client);

  final ApiClient _client;

  /// `GET /api/keywords?category=PET|USER`
  Future<List<Keyword>> list(KeywordCategory category) async {
    final response = await _client.raw.get<List<dynamic>>(
      '/keywords',
      queryParameters: {'category': category.wire},
    );
    return (response.data ?? const [])
        .cast<Map<String, dynamic>>()
        .map(Keyword.fromJson)
        .toList();
  }
}
