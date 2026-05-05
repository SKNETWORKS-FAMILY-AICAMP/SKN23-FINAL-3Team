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

  /// `PATCH /api/pets/{pet_id}` — 본인 반려견 정보 수정
  Future<Pet> update(int petId, PetUpdate data) async {
    final response = await _client.raw.patch<Map<String, dynamic>>(
      '/pets/$petId',
      data: data.toJson(),
    );
    return Pet.fromJson(response.data!);
  }

  /// `DELETE /api/pets/{pet_id}` — Soft Delete (본인만)
  Future<void> delete(int petId) async {
    await _client.raw.delete('/pets/$petId');
  }
}
