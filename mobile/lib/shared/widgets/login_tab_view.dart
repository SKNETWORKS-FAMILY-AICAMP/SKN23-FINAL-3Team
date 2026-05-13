import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../features/auth/auth_providers.dart';
import '../../features/auth/google_appauth_helper.dart';
import '../../features/auth/oauth_provider.dart';
import '../../features/auth/oauth_webview_result.dart';
import '../../features/auth/oauth_webview_screen.dart';

/// 비로그인 탭 내에 인라인으로 삽입되는 로그인 UI.
/// LoginScreen 과 동일한 OAuth 흐름을 수행하되 Scaffold 없이 배치 — 하단 바 유지.
class LoginTabView extends ConsumerStatefulWidget {
  const LoginTabView({
    super.key,
    this.message = '로그인 후 더 많은 기능을 이용해요',
  });

  final String message;

  @override
  ConsumerState<LoginTabView> createState() => _LoginTabViewState();
}

class _LoginTabViewState extends ConsumerState<LoginTabView> {
  bool _busy = false;

  Future<void> _onProviderTap(OAuthProvider provider) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final result = switch (provider.flow) {
        OAuthFlow.webViewIntercept => await _signInWithWebView(provider),
        OAuthFlow.systemBrowserAppAuth => await _signInWithAppAuth(provider),
      };
      if (result == null || !mounted) return;
      if (result.isNewUser) {
        context.go(AppRoutes.onboarding);
      } else {
        context.go(AppRoutes.home);
      }
    } on GoogleAuthCancelledException {
      // 사용자가 취소 — 조용히 처리
    } on GoogleAuthMisconfiguredException catch (e) {
      if (mounted) Fluttertoast.showToast(msg: '구글 로그인 설정 오류: ${e.message}');
    } catch (e) {
      if (mounted) Fluttertoast.showToast(msg: '로그인 실패: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<dynamic> _signInWithWebView(OAuthProvider provider) async {
    final state = _generateState();
    final url = OAuthUrlBuilder.authUrl(provider, state: state);
    final result = await Navigator.of(context).push<OAuthResult>(
      MaterialPageRoute(
        builder: (_) =>
            OAuthWebViewScreen(provider: provider, authUrl: url, state: state),
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

  Future<dynamic> _signInWithAppAuth(OAuthProvider provider) async {
    final result = await GoogleAppAuthHelper.authorize();
    if (!mounted) return null;
    return ref.read(authProvider.notifier).completeLogin(
          provider: provider,
          code: result.code,
          codeVerifier: result.codeVerifier,
          redirectUri: result.redirectUri,
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
    return SafeArea(
      child: Container(
        width: double.infinity,
        color: const Color(0xFFFFFBF6),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(24, 80, 24, 120),
          child: ConstrainedBox(
            constraints: BoxConstraints(
              minHeight: MediaQuery.of(context).size.height - 220,
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 16),
                Image.asset(
                  'assets/logo.png',
                  height: 144,
                  semanticLabel: '위드독',
                  errorBuilder: (_, __, ___) => const _FallbackLogo(),
                ),
                const SizedBox(height: 16),
                Text(
                  _busy ? '로그인 중...' : '로그인',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                    color: AppColors.darkBrown,
                    letterSpacing: -0.4,
                  ),
                ),
                const SizedBox(height: 42),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 구글 — 준비중 (LoginScreen 과 동일)
                    _SocialLoginButton(
                      backgroundColor: Colors.white,
                      borderColor: const Color(0xFFD1D5DB),
                      disabled: true,
                      caption: '준비중',
                      onTap: null,
                      child: const Text(
                        'G',
                        style: TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF4285F4),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    // 카카오
                    _SocialLoginButton(
                      backgroundColor: const Color(0xFFFEE500),
                      onTap: _busy
                          ? null
                          : () => _onProviderTap(OAuthProvider.kakao),
                      child: const Icon(
                        Icons.chat_bubble_rounded,
                        size: 28,
                        color: Color(0xFF3C1E1E),
                      ),
                    ),
                    const SizedBox(width: 16),
                    // 네이버
                    _SocialLoginButton(
                      backgroundColor: const Color(0xFF03C75A),
                      onTap: _busy
                          ? null
                          : () => _onProviderTap(OAuthProvider.naver),
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
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SocialLoginButton extends StatelessWidget {
  const _SocialLoginButton({
    required this.backgroundColor,
    required this.child,
    required this.onTap,
    this.borderColor,
    this.disabled = false,
    this.caption,
  });

  final Color backgroundColor;
  final Color? borderColor;
  final Widget child;
  final VoidCallback? onTap;
  final bool disabled;
  final String? caption;

  @override
  Widget build(BuildContext context) {
    final button = Opacity(
      opacity: disabled ? 0.45 : 1.0,
      child: Material(
        color: backgroundColor,
        shape: CircleBorder(
          side: BorderSide(
            color: borderColor ?? Colors.transparent,
            width: 1.5,
          ),
        ),
        elevation: 0,
        child: InkWell(
          onTap: disabled ? null : onTap,
          customBorder: const CircleBorder(),
          child: SizedBox(
            width: 64,
            height: 64,
            child: Center(child: child),
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

class _FallbackLogo extends StatelessWidget {
  const _FallbackLogo();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Icon(Icons.pets_rounded, color: AppColors.brandOrange, size: 58),
        SizedBox(height: 6),
        Text(
          'withDOG',
          style: TextStyle(
            fontSize: 28,
            color: AppColors.brandOrange,
            fontWeight: FontWeight.w900,
          ),
        ),
      ],
    );
  }
}
