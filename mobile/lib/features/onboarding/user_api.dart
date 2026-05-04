import '../../core/api/api_client.dart';
import '../../shared/models/user.dart';

class UserApi {
  const UserApi(this._client);

  final ApiClient _client;

  /// `PATCH /api/users/{id}`
  Future<User> update(int userId, UserUpdate data) async {
    final response = await _client.raw.patch<Map<String, dynamic>>(
      '/users/$userId',
      data: data.toJson(),
    );
    return User.fromJson(response.data!);
  }

  /// `GET /api/users/{id}`
  Future<User> get(int userId) async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/users/$userId',
    );
    return User.fromJson(response.data!);
  }
}
