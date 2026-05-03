import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../calendar/diary_tab.dart';
import '../mypage/mypage_tab.dart';
import '../places/map_tab.dart';
import 'home_tab.dart';
import 'home_tab_index.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  static const _tabs = <Widget>[
    HomeTab(),
    DiaryTab(),
    MapTab(),
    MyPageTab(),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final index = ref.watch(homeTabIndexProvider);
    return Scaffold(
      body: _tabs[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) =>
            ref.read(homeTabIndexProvider.notifier).state = i,
        destinations: const [
          NavigationDestination(icon: Icon(LucideIcons.home), label: '홈'),
          NavigationDestination(icon: Icon(LucideIcons.bookOpen), label: '다이어리'),
          NavigationDestination(icon: Icon(LucideIcons.mapPin), label: '지도'),
          NavigationDestination(icon: Icon(LucideIcons.user), label: '마이'),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push(AppRoutes.chat),
        backgroundColor: AppColors.brandOrange,
        foregroundColor: Colors.white,
        tooltip: 'AI 멍봇',
        child: const Icon(LucideIcons.messageCircle),
      ),
    );
  }
}
