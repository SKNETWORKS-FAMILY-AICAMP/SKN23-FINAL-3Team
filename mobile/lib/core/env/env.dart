/// 환경 설정 — monorepo 최상위 `.env` 단일 source.
///
/// 빌드 시 `--dart-define-from-file=../.env` 로 주입되는 컴파일 타임 상수.
/// front 가 `vite.config.ts envDir: '../'` 로 같은 패턴 사용 — 키 prefix 로 분리:
///   - `VITE_*` → 웹 + 모바일 공유 (OAuth client id, Kakao map key 등)
///   - `MOBILE_*` → 앱 전용
///   - prefix 없음 → 백엔드 공용
class Env {
  static const apiBaseUrl = String.fromEnvironment(
    'MOBILE_API_BASE_URL',
    defaultValue: 'https://withdog.kro.kr/api',
  );

  static const oauthCallbackUrl = String.fromEnvironment(
    'MOBILE_OAUTH_CALLBACK_URL',
    defaultValue: 'https://withdog.kro.kr/oauth/callback',
  );

  // OAuth client id 3종 — web 과 공유 (콘솔에 등록된 redirect_uri 동일)
  static const kakaoClientId = String.fromEnvironment('VITE_KAKAO_CLIENT_ID');
  static const googleClientId = String.fromEnvironment('VITE_GOOGLE_CLIENT_ID');
  static const naverClientId = String.fromEnvironment('VITE_NAVER_CLIENT_ID');

  // Google Android InstalledApp client id — `flutter_appauth` 분기 전용.
  // Cloud Console 에서 별도 발급 (Android 패키지명 + SHA-1 등록).
  static const googleOauthAndroidClientId = String.fromEnvironment(
    'MOBILE_GOOGLE_OAUTH_ANDROID_CLIENT_ID',
  );

  // 카카오맵 JS SDK (Step 3 진입 시 사용)
  static const kakaoMapsKey = String.fromEnvironment(
    'VITE_KAKAO_JAVASCRIPT_API_KEY',
  );
}
