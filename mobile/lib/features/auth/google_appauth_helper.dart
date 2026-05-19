import 'package:flutter_appauth/flutter_appauth.dart';

import '../../core/env/env.dart';

/// 구글 OAuth — 시스템 브라우저(Custom Tabs) 진입 + PKCE 흐름.
///
/// WebView 차단 (`Error 403: disallowed_useragent`) 우회. `flutter_appauth` 가
/// authorization 만 처리 (token 교환은 백엔드 `/api/auth/google` 가 code +
/// code_verifier 받아서 직접 token endpoint 호출).
///
/// Android InstalledApp client (Cloud Console 등록 — `com.withdog.app` +
/// SHA-1) 사용. PKCE 가 client_secret 대체.
class GoogleAppAuthHelper {
  static const _appAuth = FlutterAppAuth();

  /// `clientId` (`<prefix>.apps.googleusercontent.com`) →
  /// reverse client ID (`com.googleusercontent.apps.<prefix>`).
  /// Google InstalledApp redirect_uri 표준 형식.
  static String _toReverseClientId(String clientId) {
    const suffix = '.apps.googleusercontent.com';
    if (!clientId.endsWith(suffix)) {
      // 예외 케이스 — 그냥 그대로 반환 (잘못 입력된 키 진단용)
      return clientId;
    }
    final prefix = clientId.substring(0, clientId.length - suffix.length);
    return 'com.googleusercontent.apps.$prefix';
  }

  /// 외부 호출 진입점 — 인증만 (token 교환 X). code + codeVerifier + redirectUri 반환.
  ///
  /// Throws:
  ///   - `GoogleAuthCancelledException` — 사용자 취소
  ///   - `GoogleAuthMisconfiguredException` — Env / Cloud Console 설정 누락
  ///   - 그 외 — `flutter_appauth` 가 던지는 PlatformException 등
  static Future<GoogleAuthResult> authorize() async {
    final clientId = Env.googleOauthAndroidClientId;
    if (clientId.isEmpty) {
      throw const GoogleAuthMisconfiguredException(
        'MOBILE_GOOGLE_OAUTH_ANDROID_CLIENT_ID 환경변수가 비어있습니다. '
        '`.env` + `--dart-define-from-file=../.env` 빌드 옵션 확인.',
      );
    }
    final reverseClientId = _toReverseClientId(clientId);
    final redirectUri = '$reverseClientId:/oauth2redirect';

    // flutter_appauth 6.x — authorize() nullable 반환 (사용자 취소·OS 차단 등).
    //
    // `No stored state - unable to handle response` 트러블슈팅 (2026-05-04 진단 #2):
    // - Service endpoint 직접 명시 → discoveryUrl 로 전환 (Google issuer 자동 발견).
    //   일부 환경에서 AuthorizationManagementActivity 의 state 저장 race 회피 보고됨.
    // - additionalParameters: prompt=select_account — 매 진입 계정 선택, 캐시된 세션 재사용
    //   회피로 lib 내부 cache lookup race 우회.
    // - 기존 endpoint 명시는 주석 보존 (롤백 즉시 가능).
    //
    // 기존:
    //   serviceConfiguration: AuthorizationServiceConfiguration(
    //     authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
    //     tokenEndpoint: 'https://oauth2.googleapis.com/token',
    //   ),
    final AuthorizationResponse? response = await _appAuth.authorize(
      AuthorizationRequest(
        clientId,
        redirectUri,
        discoveryUrl:
            'https://accounts.google.com/.well-known/openid-configuration',
        scopes: const ['openid', 'email', 'profile'],
        promptValues: ['select_account'],
        // PKCE: flutter_appauth 가 code_verifier 자동 생성 + codeChallenge 첨부
      ),
    );

    if (response == null) {
      throw const GoogleAuthCancelledException('인증이 취소되었습니다.');
    }
    final code = response.authorizationCode;
    final codeVerifier = response.codeVerifier;
    if (code == null || code.isEmpty) {
      throw const GoogleAuthCancelledException('인증이 취소되었습니다.');
    }
    if (codeVerifier == null || codeVerifier.isEmpty) {
      throw const GoogleAuthMisconfiguredException(
        'PKCE code_verifier 가 비어있습니다. flutter_appauth 동작 이상.',
      );
    }
    return GoogleAuthResult(
      code: code,
      codeVerifier: codeVerifier,
      redirectUri: redirectUri,
    );
  }
}

class GoogleAuthResult {
  const GoogleAuthResult({
    required this.code,
    required this.codeVerifier,
    required this.redirectUri,
  });

  final String code;
  final String codeVerifier;
  final String redirectUri;
}

class GoogleAuthCancelledException implements Exception {
  const GoogleAuthCancelledException(this.message);
  final String message;

  @override
  String toString() => message;
}

class GoogleAuthMisconfiguredException implements Exception {
  const GoogleAuthMisconfiguredException(this.message);
  final String message;

  @override
  String toString() => message;
}
