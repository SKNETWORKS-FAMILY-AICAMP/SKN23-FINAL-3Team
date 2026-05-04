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
              final url = action.request.url?.toString();
              if (url == null) return NavigationActionPolicy.ALLOW;
              return _interceptCallback(url);
            },
            onLoadStart: (_, _) => setState(() => _loading = true),
            onLoadStop: (_, _) => setState(() => _loading = false),
            onReceivedError: (controller, request, error) {
              // OAuth 페이지 로드 자체 실패 — 사용자 안내 후 닫기
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
    if (widget.provider == OAuthProvider.naver &&
        state != widget.state) {
      _popWith(
        OAuthResult.failure(
          message: 'state 검증 실패 — CSRF 의심',
        ),
      );
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
