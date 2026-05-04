/// `OAuthWebViewScreen` 의 반환값.
sealed class OAuthResult {
  const OAuthResult();

  factory OAuthResult.success({required String code, String? state}) =
      OAuthSuccess;

  factory OAuthResult.failure({required String message}) = OAuthFailure;
}

class OAuthSuccess extends OAuthResult {
  const OAuthSuccess({required this.code, this.state});

  final String code;
  final String? state;
}

class OAuthFailure extends OAuthResult {
  const OAuthFailure({required this.message});

  final String message;
}
