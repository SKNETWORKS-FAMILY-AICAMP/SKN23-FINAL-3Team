import '../../core/env/env.dart';

/// OAuth provider 식별자 — 백엔드 `Provider` Literal 과 1:1.
enum OAuthProvider {
  kakao('kakao', '카카오'),
  google('google', '구글'),
  naver('naver', '네이버');

  const OAuthProvider(this.wire, this.label);

  final String wire;
  final String label;
}

/// OAuth 흐름 분기 — 사용자 결정 2026-05-04.
/// 카카오·네이버는 WebView 가로채기 / 구글은 시스템 브라우저(`flutter_appauth`).
/// 구글 WebView 차단 (`Error 403: disallowed_useragent`) 우회.
enum OAuthFlow { webViewIntercept, systemBrowserAppAuth }

extension OAuthProviderFlow on OAuthProvider {
  OAuthFlow get flow {
    return switch (this) {
      OAuthProvider.kakao => OAuthFlow.webViewIntercept,
      OAuthProvider.naver => OAuthFlow.webViewIntercept,
      OAuthProvider.google => OAuthFlow.systemBrowserAppAuth,
    };
  }
}

/// React `LoginPage.tsx` 의 OAuth URL 빌드 패턴 1:1 포팅.
///
/// `redirect_uri` 는 콘솔에 등록된 운영 URL (`https://withdog.kro.kr/oauth/callback`)
/// 그대로 사용. 모바일은 deep link 등록 X — `flutter_inappwebview` 의
/// `shouldOverrideUrlLoading` 으로 콜백 URL 도달 시 가로채서 `code` 추출.
class OAuthUrlBuilder {
  static String authUrl(OAuthProvider provider, {required String state}) {
    switch (provider) {
      case OAuthProvider.kakao:
        return 'https://kauth.kakao.com/oauth/authorize'
            '?client_id=${Env.kakaoClientId}'
            '&redirect_uri=${Uri.encodeComponent(Env.oauthCallbackUrl)}'
            '&response_type=code';
      case OAuthProvider.google:
        return 'https://accounts.google.com/o/oauth2/v2/auth'
            '?client_id=${Env.googleClientId}'
            '&redirect_uri=${Uri.encodeComponent(Env.oauthCallbackUrl)}'
            '&response_type=code'
            '&scope=email%20profile';
      case OAuthProvider.naver:
        return 'https://nid.naver.com/oauth2.0/authorize'
            '?client_id=${Env.naverClientId}'
            '&redirect_uri=${Uri.encodeComponent(Env.oauthCallbackUrl)}'
            '&response_type=code'
            '&state=$state';
    }
  }
}
