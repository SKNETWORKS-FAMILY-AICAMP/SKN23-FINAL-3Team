import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../core/api/api_client.dart';
import '../../core/storage/secure_storage.dart';
import '../../shared/models/auth.dart';
import '../../shared/models/user.dart';
import 'auth_api.dart';
import 'oauth_provider.dart';

/// 로그인 세션 상태 — `AuthNotifier` 가 발행.
sealed class AuthState {
  const AuthState();
}

class AuthInitial extends AuthState {
  const AuthInitial();
}

class AuthAuthenticating extends AuthState {
  const AuthAuthenticating();
}

class AuthAuthenticated extends AuthState {
  const AuthAuthenticated({required this.user, required this.isNewUser});

  final User user;
  final bool isNewUser;
}

class AuthUnauthenticated extends AuthState {
  const AuthUnauthenticated({this.message});

  final String? message;
}

final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return const SecureStorageService(FlutterSecureStorage());
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  late ApiClient client;
  client = ApiClient(
    storage: storage,
    onUnauthorized: () async {
      // 401 인터셉터 → 로그아웃 상태로 리셋
      ref.read(authProvider.notifier).onUnauthorized();
    },
  );
  return client;
});

final authApiProvider = Provider<AuthApi>((ref) {
  return AuthApi(ref.watch(apiClientProvider));
});

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this._ref) : super(const AuthInitial());

  final Ref _ref;

  /// 앱 부팅 시 호출 — secure storage 토큰 있으면 `me` 조회 후 인증 상태 복원.
  Future<void> bootstrap() async {
    final storage = _ref.read(secureStorageProvider);
    final token = await storage.readAccessToken();
    if (token == null || token.isEmpty) {
      state = const AuthUnauthenticated();
      return;
    }
    try {
      final user = await _ref.read(authApiProvider).me();
      state = AuthAuthenticated(user: user, isNewUser: false);
    } catch (_) {
      // 토큰 무효 → secure storage clear (interceptor 가 처리)
      state = const AuthUnauthenticated(message: '세션이 만료되었습니다.');
    }
  }

  /// OAuth WebView 가로채기 / `flutter_appauth` 진입점 공통 후속 처리.
  ///
  /// `code` 받아 백엔드 토큰 교환 → secure storage 저장 → `me` 조회.
  /// 구글 InstalledApp 흐름은 `codeVerifier` + `redirectUri` 추가 전달 (PKCE).
  Future<AuthResponse> completeLogin({
    required OAuthProvider provider,
    required String code,
    String? state,
    String? codeVerifier,
    String? redirectUri,
  }) async {
    this.state = const AuthAuthenticating();
    final api = _ref.read(authApiProvider);
    final auth = await api.exchangeCode(
      provider: provider,
      code: code,
      state: state,
      codeVerifier: codeVerifier,
      redirectUri: redirectUri,
    );
    await _ref.read(secureStorageProvider).writeAccessToken(auth.accessToken);

    try {
      final user = await api.me();
      this.state = AuthAuthenticated(user: user, isNewUser: auth.isNewUser);
    } catch (e) {
      // me 조회 실패해도 토큰은 저장됨 — 추후 재시도 가능. 일단 unauthenticated.
      this.state = AuthUnauthenticated(message: '사용자 정보 조회에 실패했습니다: $e');
      rethrow;
    }
    return auth;
  }

  Future<void> logout() async {
    await _ref.read(secureStorageProvider).clearAccessToken();
    state = const AuthUnauthenticated();
  }

  /// dio 401 인터셉터에서 호출.
  void onUnauthorized() {
    state = const AuthUnauthenticated(message: '세션이 만료되었습니다.');
  }

  /// 온보딩 등 외부에서 user 갱신 시.
  void updateUser(User user) {
    final current = state;
    if (current is AuthAuthenticated) {
      state = AuthAuthenticated(user: user, isNewUser: false);
    }
  }

  /// 백엔드 자동 처리 (예: 첫 pet 등록 시 primary_pet 자동 채움) 후
  /// `auth.user` 와 server 간 drift 동기화 — `GET /api/users/me` 재조회.
  /// 호출 후 nested `primary_pet` / `primary_pet_id` 갱신 가능.
  Future<void> refreshUser() async {
    final current = state;
    if (current is! AuthAuthenticated) return;
    try {
      final user = await _ref.read(authApiProvider).me();
      state = AuthAuthenticated(user: user, isNewUser: current.isNewUser);
    } catch (_) {
      // 실패 시 기존 state 유지 — 다음 화면에서 자연 복구
    }
  }
}
