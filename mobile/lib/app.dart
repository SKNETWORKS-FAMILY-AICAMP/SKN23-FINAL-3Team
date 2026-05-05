import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/auth_providers.dart';

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
    // 앱 부팅 시 secure storage 토큰 → me 조회로 인증 상태 복원
    Future.microtask(() => ref.read(authProvider.notifier).bootstrap());
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
