import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageKeys {
  static const accessToken = 'access_token';
}

class SecureStorageService {
  const SecureStorageService(this._storage);

  final FlutterSecureStorage _storage;

  Future<String?> readAccessToken() =>
      _storage.read(key: SecureStorageKeys.accessToken);

  Future<void> writeAccessToken(String token) =>
      _storage.write(key: SecureStorageKeys.accessToken, value: token);

  Future<void> clearAccessToken() =>
      _storage.delete(key: SecureStorageKeys.accessToken);
}
