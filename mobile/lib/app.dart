import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/auth_providers.dart';
import 'features/intro/intro_screen.dart';
import 'features/notification/notification_provider.dart';

class WithdogApp extends ConsumerStatefulWidget {
  const WithdogApp({super.key});

  @override
  ConsumerState<WithdogApp> createState() => _WithdogAppState();
}

class _WithdogAppState extends ConsumerState<WithdogApp> {
  late final _router = buildAppRouter(ref);

  @override
  void initState() {
    super.initState();
    Future.microtask(() async {
      // 앱 소개 온보딩 완료 여부 로드
      final prefs = await SharedPreferences.getInstance();
      // TODO: 디버그용 — 매번 온보딩 표시. 배포 시 아래 주석 해제하고 강제 false 줄 삭제.
      // ref.read(introCompletedProvider.notifier).state =
      //     prefs.getBool(introCompletedKey) ?? false;
      ref.read(introCompletedProvider.notifier).state = false;

      // 앱 부팅 시 secure storage 토큰 → me 조회로 인증 상태 복원
      ref.read(authProvider.notifier).bootstrap();
      // 알림 초기화 — 오래된 알림 정리 + 일기 리마인더 체크
      ref.read(notificationProvider.notifier).checkDiaryReminder();
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'withDOG',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: _router,
    );
  }
}
