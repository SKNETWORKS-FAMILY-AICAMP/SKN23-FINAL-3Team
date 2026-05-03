import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import 'auth_providers.dart';
import 'google_appauth_helper.dart';
import 'oauth_provider.dart';
import 'oauth_webview_result.dart';
import 'oauth_webview_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  bool _busy = false;

  Future<void> _onProviderTap(OAuthProvider provider) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final auth = switch (provider.flow) {
        OAuthFlow.webViewIntercept => await _signInWithWebView(provider),
        OAuthFlow.systemBrowserAppAuth => await _signInWithAppAuth(provider),
      };
      if (auth == null || !mounted) return;
      if (auth.isNewUser) {
        context.go(AppRoutes.onboarding);
      } else {
        context.go(AppRoutes.home);
      }
    } on GoogleAuthCancelledException {
      // 사용자가 시스템 브라우저에서 취소 — 토스트 생략 (조용히)
    } on GoogleAuthMisconfiguredException catch (e) {
      if (mounted) Fluttertoast.showToast(msg: '구글 로그인 설정 오류: ${e.message}');
    } catch (e) {
      if (mounted) Fluttertoast.showToast(msg: '로그인 실패: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// 카카오·네이버 — `flutter_inappwebview` 가로채기 흐름 (기존).
  Future<dynamic> _signInWithWebView(OAuthProvider provider) async {
    final state = _generateState();
    final url = OAuthUrlBuilder.authUrl(provider, state: state);
    final result = await Navigator.of(context).push<OAuthResult>(
      MaterialPageRoute(
        builder: (_) => OAuthWebViewScreen(
          provider: provider,
          authUrl: url,
          state: state,
        ),
        fullscreenDialog: true,
      ),
    );
    if (!mounted || result == null) return null;
    if (result is OAuthFailure) {
      Fluttertoast.showToast(msg: result.message);
      return null;
    }
    final success = result as OAuthSuccess;
    return ref.read(authProvider.notifier).completeLogin(
          provider: provider,
          code: success.code,
          state: success.state,
        );
  }

  /// 구글 — `flutter_appauth` 시스템 브라우저 + PKCE 흐름.
  /// WebView 차단 (`Error 403: disallowed_useragent`) 우회.
  Future<dynamic> _signInWithAppAuth(OAuthProvider provider) async {
    final result = await GoogleAppAuthHelper.authorize();
    if (!mounted) return null;
    return ref.read(authProvider.notifier).completeLogin(
          provider: provider,
          code: result.code,
          codeVerifier: result.codeVerifier,
          redirectUri: result.redirectUri,
          // state 미사용 — PKCE 가 CSRF 보호 대체
          state: '',
        );
  }

  String _generateState() {
    final r = Random.secure();
    final bytes = List<int>.generate(12, (_) => r.nextInt(36));
    return bytes.map((b) => b.toRadixString(36)).join();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: DecoratedBox(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFFFFF7ED), // orange-50
                Colors.white,
                Color(0xFFFFEDD5), // orange-100
              ],
            ),
          ),
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 400),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _LogoHeader(busy: _busy),
                    const SizedBox(height: 32),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 구글 = `No stored state` 미해결 (2026-05-04 fallback 결정).
                        // 시연은 카카오·네이버만, 구글은 발표 후 정식 fix
                        // ([[ops-todo-2026-05-02]] §1 #40 / [[feature-oauth-mobile-google]] §8-A 권위).
                        // onTap = null 이면 InkResponse 자동 disabled — opacity 효과 + 캡션으로 의도 표시.
                        _ProviderButton(
                          provider: OAuthProvider.google,
                          onTap: null,
                          tooltip: '준비중 — 발표 후 지원',
                          backgroundColor: Colors.white,
                          borderColor: const Color(0xFFD1D5DB),
                          disabled: true,
                          caption: '준비중',
                          child: const _GoogleLogo(),
                        ),
                        const SizedBox(width: 16),
                        _ProviderButton(
                          provider: OAuthProvider.kakao,
                          onTap: () => _onProviderTap(OAuthProvider.kakao),
                          backgroundColor: const Color(0xFFFEE500),
                          child: const Icon(
                            LucideIcons.messageCircle,
                            size: 28,
                            color: Color(0xFF000000),
                          ),
                        ),
                        const SizedBox(width: 16),
                        _ProviderButton(
                          provider: OAuthProvider.naver,
                          onTap: () => _onProviderTap(OAuthProvider.naver),
                          backgroundColor: const Color(0xFF03C75A),
                          child: const Text(
                            'N',
                            style: TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.w900,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 32),
                    TextButton(
                      onPressed: _busy ? null : () => context.go(AppRoutes.home),
                      child: const Text(
                        '홈으로 돌아가기',
                        style: TextStyle(color: AppColors.subBrown2),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _LogoHeader extends StatelessWidget {
  const _LogoHeader({required this.busy});

  final bool busy;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFFB923C), Color(0xFFEA580C)],
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                LucideIcons.dog,
                color: Colors.white,
                size: 28,
              ),
            ),
            const SizedBox(width: 12),
            const Text(
              'withDOG',
              style: TextStyle(
                fontSize: 30,
                fontWeight: FontWeight.bold,
                color: Color(0xFF111827),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Text(
          busy ? '로그인 중...' : '로그인',
          style: const TextStyle(
            fontSize: 18,
            color: Color(0xFF111827),
          ),
        ),
      ],
    );
  }
}

class _ProviderButton extends StatelessWidget {
  const _ProviderButton({
    required this.provider,
    required this.onTap,
    required this.backgroundColor,
    required this.child,
    this.borderColor,
    this.disabled = false,
    this.caption,
    this.tooltip,
  });

  final OAuthProvider provider;
  final VoidCallback? onTap;
  final Color backgroundColor;
  final Color? borderColor;
  final Widget child;

  /// 비활성화 — opacity 50% + onTap 차단. fallback (준비중) 표시 시 사용.
  final bool disabled;

  /// 버튼 아래에 표시할 작은 캡션 (예: "준비중"). null = 캡션 없음.
  final String? caption;

  /// tooltip override. null 이면 default `'${provider.label}로 로그인'`.
  final String? tooltip;

  @override
  Widget build(BuildContext context) {
    final button = Tooltip(
      message: tooltip ?? '${provider.label}로 로그인',
      child: Opacity(
        opacity: disabled ? 0.45 : 1.0,
        child: InkResponse(
          onTap: disabled ? null : onTap,
          radius: 40,
          child: Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: backgroundColor,
              shape: BoxShape.circle,
              border: borderColor != null
                  ? Border.all(color: borderColor!, width: 2)
                  : null,
            ),
            alignment: Alignment.center,
            child: child,
          ),
        ),
      ),
    );
    if (caption == null) return button;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        button,
        const SizedBox(height: 6),
        Text(
          caption!,
          style: const TextStyle(
            fontSize: 11,
            color: AppColors.mutedForeground,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}

/// 구글 로고 (간이 4색) — Step 1 시연 수준. 2차 폴리싱에서 SVG 자산 교체 후보.
class _GoogleLogo extends StatelessWidget {
  const _GoogleLogo();

  @override
  Widget build(BuildContext context) {
    return const Text(
      'G',
      style: TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.bold,
        color: Color(0xFF4285F4),
      ),
    );
  }
}
