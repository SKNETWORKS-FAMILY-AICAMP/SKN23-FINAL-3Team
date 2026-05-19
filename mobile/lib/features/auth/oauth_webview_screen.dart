import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

import '../../core/env/env.dart';
import '../../core/theme/app_colors.dart';
import 'oauth_provider.dart';
import 'oauth_webview_result.dart';

/// OAuth WebView 가로채기 화면.
///
/// `flutter_inappwebview` 가 provider 인증 페이지를 띄우고,
/// `shouldOverrideUrlLoading` 이 콜백 URL (`Env.oauthCallbackUrl`) 을 가로채서
/// `code` (+ `state`) 추출 → `Navigator.pop` 으로 결과 반환.
///
/// 호출 측은 `await Navigator.push<OAuthResult>(...)` 로 결과 받음.
class OAuthWebViewScreen extends StatefulWidget {
  const OAuthWebViewScreen({
    super.key,
    required this.provider,
    required this.authUrl,
    required this.state,
  });

  final OAuthProvider provider;
  final String authUrl;
  final String state;

  @override
  State<OAuthWebViewScreen> createState() => _OAuthWebViewScreenState();
}

class _OAuthWebViewScreenState extends State<OAuthWebViewScreen> {
  bool _consumed = false;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    // 이전 OAuth 세션 쿠키 제거 — 실패 후 재시도 시 오래된 세션으로 인한 오류 방지
    CookieManager.instance().deleteAllCookies();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.provider.label} 로그인'),
        backgroundColor: Colors.white,
        foregroundColor: AppColors.darkBrown,
        elevation: 0,
      ),
      body: Stack(
        children: [
          InAppWebView(
            initialUrlRequest: URLRequest(url: WebUri(widget.authUrl)),
            initialSettings: InAppWebViewSettings(
              useShouldOverrideUrlLoading: true,
              javaScriptEnabled: true,
              cacheEnabled: false,
              clearCache: true,
            ),
            shouldOverrideUrlLoading: (controller, action) async {
              final uri = action.request.url;
              final url = uri?.toString();
              if (url == null) return NavigationActionPolicy.ALLOW;
              // http/https 가 아닌 딥링크 (naverapp://, intent://, kakaokompassauth:// 등)
              // → WebView 에서 열 수 없으므로 조용히 취소 (실패 처리 없이)
              final scheme = uri!.scheme.toLowerCase();
              if (scheme != 'http' && scheme != 'https') {
                return NavigationActionPolicy.CANCEL;
              }
              return _interceptCallback(url);
            },
            onLoadStart: (_, _) => setState(() => _loading = true),
            onLoadStop: (_, _) => setState(() => _loading = false),
            onReceivedError: (controller, request, error) {
              // 서브리소스(이미지·폰트 등) 오류나 딥링크 취소로 인한 오류는 무시
              if (request.isForMainFrame != true) return;
              if (!mounted || _consumed) return;
              _consumed = true;
              Navigator.of(context).pop(
                OAuthResult.failure(
                  message: '인증 페이지 로드 실패: ${error.description}',
                ),
              );
            },
          ),
          if (_loading)
            const LinearProgressIndicator(
              valueColor: AlwaysStoppedAnimation(AppColors.brandOrange),
              backgroundColor: Colors.transparent,
              minHeight: 2,
            ),
        ],
      ),
    );
  }

  NavigationActionPolicy _interceptCallback(String url) {
    if (_consumed) return NavigationActionPolicy.CANCEL;
    if (!url.startsWith(Env.oauthCallbackUrl)) {
      return NavigationActionPolicy.ALLOW;
    }
    _consumed = true;
    final parsed = Uri.parse(url);
    final code = parsed.queryParameters['code'];
    final error = parsed.queryParameters['error'];
    final state = parsed.queryParameters['state'];

    if (error != null && error.isNotEmpty) {
      _popWith(OAuthResult.failure(message: 'provider 오류: $error'));
      return NavigationActionPolicy.CANCEL;
    }
    if (code == null || code.isEmpty) {
      _popWith(OAuthResult.failure(message: 'authorization_code 누락'));
      return NavigationActionPolicy.CANCEL;
    }
    // 네이버는 state 검증 — 나간 state 와 다르면 실패
    if (widget.provider == OAuthProvider.naver && state != widget.state) {
      _popWith(OAuthResult.failure(message: 'state 검증 실패 — CSRF 의심'));
      return NavigationActionPolicy.CANCEL;
    }
    _popWith(OAuthResult.success(code: code, state: state));
    return NavigationActionPolicy.CANCEL;
  }

  void _popWith(OAuthResult result) {
    if (!mounted) return;
    Navigator.of(context).pop(result);
  }
}
