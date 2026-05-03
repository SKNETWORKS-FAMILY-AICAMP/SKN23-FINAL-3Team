import '../../core/api/api_client.dart';
import '../../shared/models/pet.dart';

class PetApi {
  const PetApi(this._client);

  final ApiClient _client;

  /// `POST /api/pets`
  Future<Pet> create(PetCreate data) async {
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/pets',
      data: data.toJson(),
    );
    return Pet.fromJson(response.data!);
  }

  /// `GET /api/pets?user_id={id}`
  Future<List<Pet>> listByUser(int userId) async {
    final response = await _client.raw.get<List<dynamic>>(
      '/pets',
      queryParameters: {'user_id': userId},
    );
    return (response.data ?? const [])
        .cast<Map<String, dynamic>>()
        .map(Pet.fromJson)
        .toList();
  }
}
