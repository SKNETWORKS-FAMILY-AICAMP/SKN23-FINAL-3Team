import '../../core/api/api_client.dart';
import '../../core/env/env.dart';
import '../../shared/models/auth.dart';
import '../../shared/models/user.dart';
import 'oauth_provider.dart';

class AuthApi {
  const AuthApi(this._client);

  final ApiClient _client;

  /// `POST /api/auth/{provider}` (query: code / redirect_uri / state / code_verifier).
  ///
  /// - WebView 가로채기 흐름 (카카오·네이버): `redirectUri` / `codeVerifier` 모두 null →
  ///   `Env.oauthCallbackUrl` 디폴트 + state 만 전달
  /// - `flutter_appauth` 흐름 (구글 InstalledApp): `redirectUri` =
  ///   `com.googleusercontent.apps.<prefix>:/oauth2redirect` + `codeVerifier` 필수
  Future<AuthResponse> exchangeCode({
    required OAuthProvider provider,
    required String code,
    String? state,
    String? codeVerifier,
    String? redirectUri,
  }) async {
    final query = <String, dynamic>{
      'code': code,
      'redirect_uri': redirectUri ?? Env.oauthCallbackUrl,
      if (state != null && state.isNotEmpty) 'state': state,
      if (codeVerifier != null && codeVerifier.isNotEmpty)
        'code_verifier': codeVerifier,
    };
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/auth/${provider.wire}',
      queryParameters: query,
    );
    return AuthResponse.fromJson(response.data!);
  }

  /// `GET /api/users/me`
  Future<User> me() async {
    final response = await _client.get<Map<String, dynamic>>('/users/me');
    return User.fromJson(response);
  }
}
