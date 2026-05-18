import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/auth_providers.dart';
import '../../features/auth/login_screen.dart';
import '../../features/chat/chat_screen.dart';
import '../../features/diary/diary_draft_screen.dart';
import '../../features/home/home_screen.dart';
import '../../features/onboarding/onboarding_screen.dart';
import '../../shared/models/place.dart';

/// 앱 소개 온보딩 완료 여부 — 앱 시작 시 1회 로드 후 캐시.
final introCompletedProvider = StateProvider<bool>((ref) => false);

class AppRoutes {
  static const home = '/';
  static const login = '/login';
  static const intro = '/intro';
  static const onboarding = '/step';
  static const chat = '/chat';
  static const diaryDraft = '/diary/draft';
  // /mypage 와 /calendar 는 HomeScreen 의 BottomNavigationBar 탭으로 흡수
  // (사용자 결정 2026-05-03 — 4탭 + 챗봇 FAB 구조). 별도 라우트 불필요.

  AppRoutes._();
}

GoRouter buildAppRouter(WidgetRef ref) {
  return GoRouter(
    initialLocation: AppRoutes.home,
    refreshListenable: _AuthListenable(ref),
    redirect: (context, state) {
      final auth = ref.read(authProvider);
      final loc = state.matchedLocation;
      // 앱 소개 온보딩은 HomeScreen 위 카드 다이얼로그로 표시 (라우트 리다이렉트 불필요)

      // 인증 없이도 접근 허용: 홈(게스트), 로그인
      const guestAllowed = {AppRoutes.home, AppRoutes.login};
      if (auth is AuthAuthenticated) {
        if (loc == AppRoutes.login) return AppRoutes.home;
        return null;
      }
      // 인증 안된 상태에서 보호 라우트 진입 시 → 로그인
      if (!guestAllowed.contains(loc)) {
        return AppRoutes.login;
      }
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.home,
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: AppRoutes.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (context, state) => const OnboardingScreen(),
      ),
      GoRoute(
        path: AppRoutes.chat,
        builder: (context, state) => const ChatScreen(),
      ),
      GoRoute(
        path: AppRoutes.diaryDraft,
        builder: (context, state) {
          final place = state.extra is PlaceCard
              ? state.extra as PlaceCard
              : null;
          return DiaryDraftScreen(contextPlace: place);
        },
      ),
    ],
    errorBuilder: (context, state) =>
        Scaffold(body: Center(child: Text('경로를 찾을 수 없습니다: ${state.uri}'))),
  );
}

/// `authProvider` 변경 시 GoRouter `refresh` 트리거.
class _AuthListenable extends ChangeNotifier {
  _AuthListenable(this._ref) {
    _sub = _ref.listenManual<AuthState>(authProvider, (_, _) {
      notifyListeners();
    });
  }

  final WidgetRef _ref;
  late final ProviderSubscription<AuthState> _sub;

  @override
  void dispose() {
    _sub.close();
    super.dispose();
  }
}
