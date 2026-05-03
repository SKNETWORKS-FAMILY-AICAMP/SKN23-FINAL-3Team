import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../auth/auth_providers.dart';
import 'home_tab_index.dart';

/// 메인 진입 화면 — React `HomePage HomeIntro` 1:1 변환.
///
/// 데스크톱은 좌측 글래스 카드 + 우측 인트로 영상 / 모바일은 세로 배치.
/// 인트로 영상은 Step 7 폴리싱에서 `video_player` 추가 후보. 1차 = 정적 그라데이션 + 일러스트.
class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    final greeting = switch (auth) {
      AuthAuthenticated(:final user) => '${user.nickname}님 안녕하세요!',
      _ => 'withDOG 에 오신 걸 환영해요',
    };
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _Greeting(text: greeting),
            const SizedBox(height: 16),
            const _IntroCard(),
            const SizedBox(height: 24),
            const _Section(title: 'AI 맞춤 반려견 도우미'),
            const SizedBox(height: 12),
            _ActionGrid(authenticated: auth is AuthAuthenticated),
          ],
        ),
      ),
    );
  }
}

/// HomeScreen BottomNav 탭 인덱스 — `home_tab_index.dart` 권위.
const _diaryTabIndex = 1;
const _mapTabIndex = 2;
const _myTabIndex = 3;

class _Greeting extends StatelessWidget {
  const _Greeting({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFFFB923C), Color(0xFFEA580C)],
            ),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(LucideIcons.dog, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppColors.darkBrown,
            ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}

class _IntroCard extends StatelessWidget {
  const _IntroCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFF7ED), Colors.white, Color(0xFFFFEDD5)],
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.beige),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(999),
            ),
            child: const Text(
              'AI 맞춤 반려견 도우미',
              style: TextStyle(
                color: Color(0xFFB86A2E),
                fontWeight: FontWeight.w600,
                fontSize: 12,
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            '반려견과\n추억을 남겨요',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: AppColors.darkBrown,
              height: 1.2,
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            '산책로, 카페, 실내 장소, 여행지까지\n우리 아이의 성향과 상황에 맞춰 AI가 추천해드려요.',
            style: TextStyle(
              fontSize: 14,
              height: 1.7,
              color: AppColors.subBrown,
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: const [
              _IntroChip(label: '#실내추천'),
              _IntroChip(label: '#산책코스'),
              _IntroChip(label: '#AI그림일기'),
            ],
          ),
        ],
      ),
    );
  }
}

class _IntroChip extends StatelessWidget {
  const _IntroChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.beige),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: const TextStyle(color: AppColors.subBrown2, fontSize: 12),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.bold,
        color: AppColors.subBrown2,
      ),
    );
  }
}

class _ActionGrid extends ConsumerWidget {
  const _ActionGrid({required this.authenticated});

  final bool authenticated;

  void _switchTab(WidgetRef ref, int index) {
    ref.read(homeTabIndexProvider.notifier).state = index;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cards = <_ActionCardData>[
      _ActionCardData(
        icon: LucideIcons.mapPin,
        title: 'AI 장소 추천',
        subtitle: '산책로, 카페, 실내 장소를 AI가 추천해줘요.',
        onTap: () => _switchTab(ref, _mapTabIndex),
      ),
      _ActionCardData(
        icon: LucideIcons.bookOpen,
        title: '오늘 일기 쓰기',
        subtitle: '오늘 있었던 일을 기록해요.',
        onTap: () => _switchTab(ref, _diaryTabIndex),
      ),
      _ActionCardData(
        icon: LucideIcons.messageCircle,
        title: 'AI 멍봇과 대화',
        subtitle: '챗봇으로 장소 추천 받고 일기 작성까지.',
        onTap: () => context.push(AppRoutes.chat),
      ),
      _ActionCardData(
        icon: LucideIcons.user,
        title: authenticated ? '마이페이지' : '로그인하기',
        subtitle: authenticated
            ? '반려견 정보와 즐겨찾기를 관리해요.'
            : '소셜 로그인으로 시작해요.',
        onTap: () {
          if (authenticated) {
            _switchTab(ref, _myTabIndex);
          } else {
            context.go(AppRoutes.login);
          }
        },
      ),
    ];
    return Column(
      children: [
        for (final c in cards)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _ActionCard(data: c),
          ),
      ],
    );
  }
}

class _ActionCardData {
  const _ActionCardData({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({required this.data});

  final _ActionCardData data;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: data.onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppColors.beige),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: AppColors.peach,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Icon(data.icon, color: AppColors.brandOrange, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    data.title,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    data.subtitle,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.subBrown2,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              LucideIcons.chevronRight,
              color: AppColors.mutedForeground,
              size: 20,
            ),
          ],
        ),
      ),
    );
  }
}
