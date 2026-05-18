import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../core/api/dio_error_format.dart';
import '../inquiry/inquiry_screen.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/login_tab_view.dart';
import '../../shared/models/breed.dart';
import '../../shared/models/pet.dart';
import '../../shared/models/place.dart';
import '../../shared/models/user.dart';
import '../auth/auth_providers.dart';
import '../../shared/models/diary.dart';
import '../diary/diary_detail_modal_sheet.dart';
import '../diary/diary_list_provider.dart';
import '../home/home_tab_index.dart';
import '../notification/notification_provider.dart';
import '../onboarding/onboarding_providers.dart';
import '../places/map_focus_provider.dart';
import '../places/place_providers.dart';
import 'widgets/pet_add_modal.dart';
import 'widgets/pet_edit_modal.dart';
import 'widgets/user_edit_modal.dart';

/// 마이페이지 탭 — 4 섹션 (사용자 결정 2026-05-03):
/// 1. 대표 반려견 / 2. 반려견 목록 / 3. 즐겨찾기 장소 / 4. 즐겨찾기 다이어리
///
/// Step 4 본격 구현 (2026-05-04). 비로그인 시 _Unauthenticated 분기.
class MyPageTab extends ConsumerWidget {
  const MyPageTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider);
    if (auth is! AuthAuthenticated) {
      return const LoginTabView(message: '로그인 후 더 많은 기능을 이용해요');
    }
    return _Authenticated(
      user: auth.user,
      onLogout: () async {
        await ref.read(authProvider.notifier).logout();
      },
    );
  }
}


class _Authenticated extends ConsumerWidget {
  const _Authenticated({required this.user, required this.onLogout});

  final User user;
  final Future<void> Function() onLogout;

  Future<void> _refresh(WidgetRef ref) async {
    ref.invalidate(userPetsProvider);
    ref.invalidate(favoritePlacesProvider);
    ref.invalidate(diaryListProvider);
    await ref.read(authProvider.notifier).refreshUser();
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () => _refresh(ref),
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _UserCard(user: user, onLogout: onLogout),
            const SizedBox(height: 16),
            _PrimaryPetSection(user: user),
            const SizedBox(height: 16),
            const _SubscriptionPassSection(),
            const SizedBox(height: 16),
            const _FavoritePlacesSection(),
            const SizedBox(height: 16),
            const _FavoriteDiariesSection(),
            const SizedBox(height: 16),
            const _NotificationSettingSection(),
            const SizedBox(height: 16),
            const _CustomerServiceSection(),
            const SizedBox(height: 16),
            const _PolicySection(),
            const SizedBox(height: 16),
            const _AppVersionSection(),
            const SizedBox(height: 24),
            _WithdrawButton(user: user, onLogout: onLogout),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}

class _UserCard extends StatelessWidget {
  const _UserCard({required this.user, required this.onLogout});

  final User user;
  final Future<void> Function() onLogout;

  void _openEditModal(BuildContext context) {
    showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => UserEditModal(user: user),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 헤더: 내 정보 + 수정/로그아웃 ──
            _SectionHeader(
              icon: LucideIcons.user,
              title: '내 정보',
              action: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    tooltip: '내 정보 수정',
                    icon: const Icon(LucideIcons.pencil, size: 16),
                    onPressed: () => _openEditModal(context),
                    constraints: const BoxConstraints(),
                    padding: const EdgeInsets.all(6),
                  ),
                  IconButton(
                    tooltip: '로그아웃',
                    icon: const Icon(LucideIcons.logOut, size: 16),
                    onPressed: onLogout,
                    constraints: const BoxConstraints(),
                    padding: const EdgeInsets.all(6),
                  ),
                ],
              ),
            ),
            // ── 프로필 사진 + 인사 + 이메일 + 소셜 배지 ──
            Row(
              children: [
                _ProfileAvatar(
                  radius: 28,
                  url: user.profileImageUrl,
                  fallbackIcon: LucideIcons.user,
                  iconSize: 24,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${user.nickname}님 안녕하세요!',
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w800,
                          color: AppColors.darkBrown,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              user.email,
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.mutedForeground,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.peach,
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(
                              '${user.provider} 로그인',
                              style: const TextStyle(
                                fontSize: 10,
                                color: AppColors.brandOrange,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            const Divider(height: 1, color: Color(0xFFF3E3D8)),
            const SizedBox(height: 14),
            // ── 구독패스 영역 ──
            const _SubscriptionBanner(),
          ],
        ),
      ),
    );
  }
}

class _SubscriptionBanner extends StatelessWidget {
  const _SubscriptionBanner();

  // TODO: 실제 구독 상태 연동 시 tier 파라미터 추가
  static const _currentTier = '무료';

  static const _tierData = <String, ({IconData icon, Color color, Color bg})>{
    '무료': (icon: LucideIcons.leaf, color: Color(0xFF43A047), bg: Color(0xFFE8F5E9)),
    '프리미엄': (icon: LucideIcons.zap, color: AppColors.brandOrange, bg: Color(0xFFFFF5EE)),
    '프로': (icon: LucideIcons.gem, color: Color(0xFF7B1FA2), bg: Color(0xFFF3E5F5)),
  };

  @override
  Widget build(BuildContext context) {
    final data = _tierData[_currentTier]!;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: data.bg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: data.color.withAlpha(60)),
      ),
      child: Row(
        children: [
          // 큰 아이콘
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: data.color.withAlpha(30),
              shape: BoxShape.circle,
            ),
            alignment: Alignment.center,
            child: Icon(data.icon, size: 26, color: data.color),
          ),
          const SizedBox(width: 14),
          // 티어명
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$_currentTier 구독패스',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: data.color,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '현재 이용 중인 플랜',
                  style: TextStyle(
                    fontSize: 11,
                    color: data.color.withAlpha(180),
                  ),
                ),
              ],
            ),
          ),
          // 혜택 보기 버튼
          OutlinedButton(
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => const _SubscriptionBenefitPage(
                    currentTier: _currentTier,
                  ),
                ),
              );
            },
            style: OutlinedButton.styleFrom(
              foregroundColor: data.color,
              side: BorderSide(color: data.color),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(999),
              ),
              minimumSize: Size.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: const Text(
              '혜택 보기',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _SubscriptionBenefitPage extends StatelessWidget {
  const _SubscriptionBenefitPage({required this.currentTier});

  final String currentTier;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9F5F0),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(LucideIcons.x, color: AppColors.darkBrown),
          onPressed: () => Navigator.of(context).pop(),
        ),
        centerTitle: true,
        title: const Text(
          '구독패스 혜택',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: AppColors.darkBrown,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
        child: Column(
          children: [
            // ── 현재 플랜 안내 ──
            _BenefitTierCard(
              tier: '무료',
              price: '₩0 / 월',
              color: const Color(0xFF43A047),
              bgColor: const Color(0xFFE8F5E9),
              icon: LucideIcons.leaf,
              features: const [
                'AI 일기 월 5회',
                'AI 그림 월 2회',
                '기본 산책 지도',
              ],
              isCurrent: currentTier == '무료',
            ),
            const SizedBox(height: 12),
            _BenefitTierCard(
              tier: '프리미엄',
              price: '₩4,900 / 월',
              color: AppColors.brandOrange,
              bgColor: const Color(0xFFFFF5EE),
              icon: LucideIcons.zap,
              features: const [
                'AI 일기 무제한',
                'AI 그림 월 30회',
                '사진 일러스트 변환',
              ],
              isCurrent: currentTier == '프리미엄',
            ),
            const SizedBox(height: 12),
            _BenefitTierCard(
              tier: '프로',
              price: '₩9,900 / 월',
              color: const Color(0xFF7B1FA2),
              bgColor: const Color(0xFFF3E5F5),
              icon: LucideIcons.gem,
              features: const [
                '모든 프리미엄 기능',
                'AI 그림 무제한',
                '우선 응답 · 광고 제거',
              ],
              isCurrent: currentTier == '프로',
            ),
            const SizedBox(height: 24),
            // ── 업그레이드 버튼 ──
            if (currentTier != '프로')
              SizedBox(
                width: double.infinity,
                height: 50,
                child: FilledButton(
                  onPressed: () {
                    Fluttertoast.showToast(msg: '업그레이드 기능은 준비 중입니다.');
                  },
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.brandOrange,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: const Text(
                    '업그레이드하기',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _BenefitTierCard extends StatelessWidget {
  const _BenefitTierCard({
    required this.tier,
    required this.price,
    required this.color,
    required this.bgColor,
    required this.icon,
    required this.features,
    required this.isCurrent,
  });

  final String tier;
  final String price;
  final Color color;
  final Color bgColor;
  final IconData icon;
  final List<String> features;
  final bool isCurrent;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isCurrent ? color : color.withAlpha(60),
          width: isCurrent ? 2 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: color.withAlpha(30),
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: Icon(icon, size: 20, color: color),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          tier,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: color,
                          ),
                        ),
                        if (isCurrent) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: color.withAlpha(40),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: Text(
                              '현재 이용 중',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: color,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      price,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: color.withAlpha(180),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ...features.map(
            (f) => Padding(
              padding: const EdgeInsets.only(bottom: 5),
              child: Row(
                children: [
                  Icon(LucideIcons.check, size: 14, color: color),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      f,
                      style: TextStyle(
                        fontSize: 13,
                        color: color.withAlpha(220),
                        height: 1.3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.icon, required this.title, this.action});

  final IconData icon;
  final String title;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Icon(icon, color: AppColors.brandOrange, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: AppColors.darkBrown,
              ),
            ),
          ),
          // ignore: use_null_aware_elements
          if (action != null) action!,
        ],
      ),
    );
  }
}

// (1) 반려견 ─────────────────────────────────────────────────
class _PrimaryPetSection extends ConsumerWidget {
  const _PrimaryPetSection({required this.user});

  final User user;

  void _openAddModal(BuildContext context) {
    showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const PetAddModal(),
    );
  }

  void _openEditModal(BuildContext context, Pet pet) {
    showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => PetEditModal(pet: pet),
    );
  }

  Future<void> _setPrimary(
    BuildContext context,
    WidgetRef ref,
    Pet pet,
  ) async {
    if (pet.id == user.primaryPetId) {
      Fluttertoast.showToast(msg: '이미 대표 반려견이에요');
      return;
    }
    try {
      final userApi = ref.read(userApiProvider);
      await userApi.update(user.id, UserUpdate(primaryPetId: pet.id));
      await ref.read(authProvider.notifier).refreshUser();
      Fluttertoast.showToast(msg: '"${pet.name}"이(가) 대표가 됐어요');
    } catch (e) {
      Fluttertoast.showToast(msg: formatDioError(e, '대표 변경 실패'));
    }
  }

  Future<void> _confirmDelete(
    BuildContext context,
    WidgetRef ref,
    Pet pet,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('반려견 삭제'),
        content: Text('"${pet.name}" 정보를 삭제할까요?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.destructive,
            ),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ref.read(petApiProvider).delete(pet.id);
      ref.invalidate(userPetsProvider);
      await ref.read(authProvider.notifier).refreshUser();
      Fluttertoast.showToast(msg: '"${pet.name}" 삭제됐어요');
    } catch (e) {
      Fluttertoast.showToast(msg: formatDioError(e, '삭제 실패'));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final petsAsync = ref.watch(userPetsProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SectionHeader(
              icon: LucideIcons.dog,
              title: '내 반려견',
              action: TextButton.icon(
                onPressed: () => _openAddModal(context),
                icon: const Icon(LucideIcons.plus, size: 14),
                label: const Text('추가'),
                style: TextButton.styleFrom(
                  foregroundColor: AppColors.brandOrange,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                ),
              ),
            ),
            petsAsync.when(
              data: (pets) {
                if (pets.isEmpty) {
                  return const Text(
                    '아직 등록된 반려견이 없어요. +추가 버튼으로 등록해보세요.',
                    style: TextStyle(color: AppColors.subBrown2),
                  );
                }
                final breeds = ref.watch(allBreedsProvider).valueOrNull ?? [];
                // 대표 반려견을 항상 첫 번째로 정렬
                final sorted = [...pets]..sort((a, b) {
                  if (a.id == user.primaryPetId) return -1;
                  if (b.id == user.primaryPetId) return 1;
                  return 0;
                });
                return SizedBox(
                  height: 280,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: sorted.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 12),
                    itemBuilder: (_, i) {
                      final pet = sorted[i];
                      final breedName = breeds
                          .where((b) => b.id == pet.breedId)
                          .map((b) => b.nameKo)
                          .firstOrNull;
                      return _PetCard(
                        pet: pet,
                        isPrimary: pet.id == user.primaryPetId,
                        breedName: breedName,
                        onSelect: () => _setPrimary(context, ref, pet),
                        onEdit: () => _openEditModal(context, pet),
                        onDelete: () => _confirmDelete(context, ref, pet),
                      );
                    },
                  ),
                );
              },
              loading: () => const SizedBox(
                height: 80,
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Text(
                '불러오기 실패: $e',
                style: const TextStyle(color: AppColors.destructive),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PetCard extends StatelessWidget {
  const _PetCard({
    required this.pet,
    required this.isPrimary,
    required this.onSelect,
    required this.onEdit,
    required this.onDelete,
    this.breedName,
  });

  final Pet pet;
  final bool isPrimary;
  final String? breedName;
  final VoidCallback onSelect;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final tags = <String>[
      if (pet.gender != null) pet.gender!.label,
      if (pet.isNeutered == true) '중성화 O' else if (pet.isNeutered == false) '중성화 X',
      ...?(pet.selectedTags?.cast<String>()),
    ];

    return Container(
      width: 175,
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
      decoration: BoxDecoration(
        color: isPrimary ? const Color(0xFFFFF5EE) : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isPrimary
              ? AppColors.brandOrange.withOpacity(0.5)
              : const Color(0xFFF3E4D3),
          width: isPrimary ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 상단 — 삭제 아이콘 우상단
          Align(
            alignment: Alignment.topRight,
            child: GestureDetector(
              onTap: onDelete,
              child: Icon(
                LucideIcons.trash2,
                size: 15,
                color: AppColors.mutedForeground.withOpacity(0.6),
              ),
            ),
          ),
          // 아바타
          _ProfileAvatar(
            radius: 30,
            url: pet.imageUrl,
            fallbackIcon: LucideIcons.dog,
            iconSize: 30,
          ),
          const SizedBox(height: 8),
          // 이름 + 대표 뱃지
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: Text(
                  pet.name,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppColors.darkBrown,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (isPrimary) ...[
                const SizedBox(width: 5),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                  decoration: BoxDecoration(
                    color: AppColors.brandOrange,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: const Text(
                    '대표 반려견',
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ],
          ),
          // 품종
          if (breedName != null) ...[
            const SizedBox(height: 3),
            Text(
              breedName!,
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.mutedForeground,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
          const SizedBox(height: 8),
          // 태그
          if (tags.isNotEmpty)
            Expanded(
              child: Wrap(
                spacing: 4,
                runSpacing: 4,
                alignment: WrapAlignment.center,
                children: tags
                    .take(4)
                    .map((t) => Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.peach,
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            t,
                            style: const TextStyle(
                              fontSize: 10,
                              color: AppColors.brandOrange,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ))
                    .toList(),
              ),
            )
          else
            const Spacer(),
          // 하단 버튼
          const SizedBox(height: 6),
          Row(
            children: [
              // 선택완료 / 선택
              Expanded(
                child: SizedBox(
                  height: 30,
                  child: isPrimary
                      ? OutlinedButton(
                          onPressed: null,
                          style: OutlinedButton.styleFrom(
                            padding: EdgeInsets.zero,
                            side: BorderSide(
                              color: AppColors.brandOrange.withOpacity(0.3),
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: Text(
                            '선택완료',
                            style: TextStyle(
                              fontSize: 11,
                              color: AppColors.brandOrange.withOpacity(0.5),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        )
                      : FilledButton(
                          onPressed: onSelect,
                          style: FilledButton.styleFrom(
                            backgroundColor: AppColors.brandOrange,
                            foregroundColor: Colors.white,
                            padding: EdgeInsets.zero,
                            minimumSize: Size.zero,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                            textStyle: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          child: const Text('선택'),
                        ),
                ),
              ),
              const SizedBox(width: 6),
              // 수정
              Expanded(
                child: SizedBox(
                  height: 30,
                  child: OutlinedButton(
                    onPressed: onEdit,
                    style: OutlinedButton.styleFrom(
                      padding: EdgeInsets.zero,
                      foregroundColor: AppColors.brandOrange,
                      side: const BorderSide(color: AppColors.brandOrange),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      textStyle: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    child: const Text('수정'),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// 네트워크 이미지 + 아이콘 폴백을 안전하게 처리하는 아바타.
///
/// [foregroundImage] 가 null 일 때 [onForegroundImageError] 를 설정하면
/// Flutter assertion 에러가 발생하므로, URL 유무에 따라 분기 처리한다.
class _ProfileAvatar extends StatelessWidget {
  const _ProfileAvatar({
    required this.radius,
    required this.url,
    required this.fallbackIcon,
    this.iconSize = 28,
    this.backgroundColor = AppColors.peach,
  });

  final double radius;
  final String? url;
  final IconData fallbackIcon;
  final double iconSize;
  final Color backgroundColor;

  @override
  Widget build(BuildContext context) {
    final hasUrl = url != null && url!.isNotEmpty;
    return CircleAvatar(
      radius: radius,
      backgroundColor: backgroundColor,
      foregroundImage: hasUrl ? NetworkImage(url!) : null,
      onForegroundImageError: hasUrl ? (_, __) {} : null,
      child: Icon(fallbackIcon, color: AppColors.brandOrange, size: iconSize),
    );
  }
}

// (2.5) 구독패스 ───────────────────────────────────────────────
class _SubscriptionPassSection extends StatefulWidget {
  const _SubscriptionPassSection();

  @override
  State<_SubscriptionPassSection> createState() =>
      _SubscriptionPassSectionState();
}

class _SubscriptionPassSectionState extends State<_SubscriptionPassSection> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── 헤더 (탭 시 접기/펼치기) ──────────────────────────
            InkWell(
              onTap: () => setState(() => _expanded = !_expanded),
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    const Icon(
                      LucideIcons.crown,
                      color: AppColors.brandOrange,
                      size: 18,
                    ),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        '구독패스',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppColors.darkBrown,
                        ),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFE8F5E9),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: const Text(
                        '무료',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF43A047),
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Icon(
                      _expanded
                          ? LucideIcons.chevronUp
                          : LucideIcons.chevronDown,
                      color: AppColors.mutedForeground,
                      size: 18,
                    ),
                  ],
                ),
              ),
            ),
            // ── 펼쳐진 콘텐츠 ──────────────────────────────────────
            if (_expanded) ...[
              const SizedBox(height: 12),
              SizedBox(
                height: 250,
                child: Center(
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    shrinkWrap: true,
                    children: [
                      _SubscriptionTierCard(
                        tier: '무료',
                        price: '₩0 / 월',
                        color: const Color(0xFF43A047),
                        bgColor: const Color(0xFFE8F5E9),
                        borderColor: const Color(0xFF43A047),
                        icon: LucideIcons.leaf,
                        features: const [
                          'AI 일기 월 5회',
                          'AI 그림 월 2회',
                          '기본 산책 지도',
                        ],
                        isActive: true,
                      ),
                      const SizedBox(width: 10),
                      _SubscriptionTierCard(
                        tier: '프리미엄',
                        price: '₩4,900 / 월',
                        color: AppColors.brandOrange,
                        bgColor: const Color(0xFFFFF5EE),
                        borderColor: AppColors.brandOrange,
                        icon: LucideIcons.zap,
                        features: const [
                          'AI 일기 무제한',
                          'AI 그림 월 30회',
                          '사진 일러스트 변환',
                        ],
                        isActive: false,
                      ),
                      const SizedBox(width: 10),
                      _SubscriptionTierCard(
                        tier: '프로',
                        price: '₩9,900 / 월',
                        color: const Color(0xFF7B1FA2),
                        bgColor: const Color(0xFFF3E5F5),
                        borderColor: const Color(0xFF7B1FA2),
                        icon: LucideIcons.gem,
                        features: const [
                          '모든 프리미엄 기능',
                          'AI 그림 무제한',
                          '우선 응답 · 광고 제거',
                        ],
                        isActive: false,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SubscriptionTierCard extends StatelessWidget {
  const _SubscriptionTierCard({
    required this.tier,
    required this.price,
    required this.color,
    required this.bgColor,
    required this.borderColor,
    required this.icon,
    required this.features,
    required this.isActive,
  });

  final String tier;
  final String price;
  final Color color;
  final Color bgColor;
  final Color borderColor;
  final IconData icon;
  final List<String> features;
  final bool isActive;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isActive ? borderColor : borderColor.withOpacity(0.3),
          width: isActive ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 아이콘 + 티어명
          Row(
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Text(
                tier,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            price,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: color.withOpacity(0.8),
            ),
          ),
          const SizedBox(height: 10),
          // 혜택 리스트
          ...features.map(
            (f) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(LucideIcons.check, size: 12, color: color),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      f,
                      style: TextStyle(
                        fontSize: 11,
                        color: color.withOpacity(0.9),
                        height: 1.3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const Spacer(),
          // 상태 버튼
          SizedBox(
            width: double.infinity,
            height: 28,
            child: isActive
                ? OutlinedButton(
                    onPressed: null,
                    style: OutlinedButton.styleFrom(
                      padding: EdgeInsets.zero,
                      side: BorderSide(color: color.withOpacity(0.4)),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: Text(
                      '현재 이용 중',
                      style: TextStyle(
                        fontSize: 11,
                        color: color.withOpacity(0.6),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  )
                : FilledButton(
                    onPressed: () {
                      Fluttertoast.showToast(msg: '준비 중인 기능이에요');
                    },
                    style: FilledButton.styleFrom(
                      backgroundColor: color,
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.zero,
                      minimumSize: Size.zero,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      textStyle: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    child: const Text('업그레이드'),
                  ),
          ),
        ],
      ),
    );
  }
}

// (3) 즐겨찾기 장소 — 접기/펼치기 + 지도탭 연결 ──────────────────
class _FavoritePlacesSection extends ConsumerStatefulWidget {
  const _FavoritePlacesSection();

  @override
  ConsumerState<_FavoritePlacesSection> createState() =>
      _FavoritePlacesSectionState();
}

class _FavoritePlacesSectionState
    extends ConsumerState<_FavoritePlacesSection> {
  bool _expanded = false;

  /// 지도탭으로 이동하고 특정 장소에 카메라·마커·하단 카드 포커싱.
  void _goToMapWithFocus(PlaceFavoriteItem item) {
    ref.read(mapFocusProvider.notifier).requestFocus(
      PlaceCard(
        name: item.name,
        contentId: item.contentId,
        subCategory: item.subCategory,
      ),
    );
    ref.read(homeTabIndexProvider.notifier).state = 2; // mapTabIndex
  }

  /// 지도탭으로 이동하고 즐겨찾기 목록 뷰로 리셋.
  void _goToMapFavorites() {
    ref.read(mapShowFavoritesProvider.notifier).state = true;
    ref.read(homeTabIndexProvider.notifier).state = 2;
  }

  @override
  Widget build(BuildContext context) {
    final favorites = ref.watch(favoritePlacesProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── 헤더 (탭 시 접기/펼치기) ──────────────────────────
            InkWell(
              onTap: () => setState(() => _expanded = !_expanded),
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    const Icon(
                      LucideIcons.heart,
                      color: AppColors.brandOrange,
                      size: 18,
                    ),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        '장소 즐겨찾기',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppColors.darkBrown,
                        ),
                      ),
                    ),
                    Icon(
                      _expanded
                          ? LucideIcons.chevronUp
                          : LucideIcons.chevronDown,
                      color: AppColors.mutedForeground,
                      size: 18,
                    ),
                  ],
                ),
              ),
            ),
            // ── 펼쳐진 콘텐츠 ──────────────────────────────────────
            if (_expanded) ...[
              const SizedBox(height: 12),
              favorites.when(
                data: (list) {
                  if (list.isEmpty) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Column(
                        children: [
                          Opacity(
                            opacity: 0.35,
                            child: Image.asset(
                              'assets/logo.png',
                              height: 56,
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            '아직 즐겨찾기한 장소가 없어요.\n장소 카드의 ❤️ 토글로 추가해보세요.',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: AppColors.mutedForeground,
                            ),
                          ),
                        ],
                      ),
                    );
                  }
                  final preview = list.take(3).toList();
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      for (final item in preview)
                        _FavoritePlaceTile(
                          item: item,
                          onTap: () => _goToMapWithFocus(item),
                        ),
                      const SizedBox(height: 4),
                      OutlinedButton.icon(
                        onPressed: _goToMapFavorites,
                        icon: const Icon(LucideIcons.mapPin, size: 14),
                        label: const Text('더보기'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.brandOrange,
                          side: const BorderSide(
                            color: AppColors.brandOrange,
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                      ),
                    ],
                  );
                },
                loading: () => const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Center(child: CircularProgressIndicator()),
                ),
                error: (e, _) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    '즐겨찾기 장소 로드 실패: $e',
                    style: const TextStyle(color: AppColors.destructive),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _FavoritePlaceTile extends StatelessWidget {
  const _FavoritePlaceTile({required this.item, required this.onTap});

  final PlaceFavoriteItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        child: Row(
          children: [
            const Icon(
              Icons.favorite,
              size: 18,
              color: AppColors.brandOrange,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.name,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                  ),
                  if (item.subCategory.isNotEmpty)
                    Text(
                      item.subCategory,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.mutedForeground,
                      ),
                    ),
                ],
              ),
            ),
            const Icon(
              LucideIcons.chevronRight,
              color: AppColors.mutedForeground,
              size: 16,
            ),
          ],
        ),
      ),
    );
  }
}

// (4) 다이어리 즐겨찾기 — 접기/펼치기 + 가로형 리스트 ─────────────
class _FavoriteDiariesSection extends ConsumerStatefulWidget {
  const _FavoriteDiariesSection();

  @override
  ConsumerState<_FavoriteDiariesSection> createState() =>
      _FavoriteDiariesSectionState();
}

class _FavoriteDiariesSectionState
    extends ConsumerState<_FavoriteDiariesSection> {
  bool _expanded = false;

  void _goToCalendar() {
    ref.read(homeTabIndexProvider.notifier).state = 1;
  }

  void _openDetail(int diaryId) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DiaryDetailModalSheet(diaryId: diaryId),
    );
  }

  @override
  Widget build(BuildContext context) {
    final all = ref.watch(diaryListProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── 헤더 (탭 시 접기/펼치기) ──────────────────────────
            InkWell(
              onTap: () => setState(() => _expanded = !_expanded),
              borderRadius: BorderRadius.circular(8),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    const Icon(
                      LucideIcons.star,
                      color: AppColors.brandOrange,
                      size: 18,
                    ),
                    const SizedBox(width: 8),
                    const Expanded(
                      child: Text(
                        '다이어리 즐겨찾기',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppColors.darkBrown,
                        ),
                      ),
                    ),
                    Icon(
                      _expanded
                          ? LucideIcons.chevronUp
                          : LucideIcons.chevronDown,
                      color: AppColors.mutedForeground,
                      size: 18,
                    ),
                  ],
                ),
              ),
            ),
            // ── 펼쳐진 콘텐츠 ──────────────────────────────────────
            if (_expanded) ...[
              const SizedBox(height: 12),
              all.when(
                data: (list) {
                  final favs = list.where((d) => d.isFavorite).toList();
                  if (favs.isEmpty) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Text(
                        '즐겨찾기한 일기가 없어요.\n캘린더·목록의 ⭐ 토글로 추가해보세요.',
                        textAlign: TextAlign.center,
                        style: GoogleFonts.gaegu(
                          fontSize: 14,
                          color: AppColors.mutedForeground,
                        ),
                      ),
                    );
                  }
                  final preview = favs.take(3).toList();
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      for (final diary in preview)
                        _FavoriteDiaryTile(
                          diary: diary,
                          onTap: () => _openDetail(diary.id),
                        ),
                      const SizedBox(height: 4),
                      OutlinedButton.icon(
                        onPressed: _goToCalendar,
                        icon: const Icon(LucideIcons.bookOpen, size: 14),
                        label: const Text('더보기'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.brandOrange,
                          side: const BorderSide(
                            color: AppColors.brandOrange,
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                      ),
                    ],
                  );
                },
                loading: () => const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Center(child: CircularProgressIndicator()),
                ),
                error: (e, _) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    '다이어리 로드 실패: $e',
                    style: const TextStyle(color: AppColors.destructive),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _FavoriteDiaryTile extends ConsumerWidget {
  const _FavoriteDiaryTile({required this.diary, required this.onTap});

  final Diary diary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        child: Row(
          children: [
            // 감정 이모지 or 이미지 썸네일
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: AppColors.peach,
                borderRadius: BorderRadius.circular(10),
              ),
              clipBehavior: Clip.antiAlias,
              child: diary.imageId != null
                  ? _TinyDiaryImage(imageId: diary.imageId!)
                  : Center(
                      child: Text(
                        diary.emotion ?? '🐾',
                        style: const TextStyle(fontSize: 20),
                      ),
                    ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    diary.title ?? '오늘의 일기',
                    style: GoogleFonts.gaegu(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    _formatDate(diary.diaryDate),
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              LucideIcons.chevronRight,
              color: AppColors.mutedForeground,
              size: 16,
            ),
          ],
        ),
      ),
    );
  }

  static String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';
}

/// 다이어리 즐겨찾기 타일용 작은 이미지 위젯.
class _TinyDiaryImage extends ConsumerWidget {
  const _TinyDiaryImage({required this.imageId});

  final int imageId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urlAsync = ref.watch(diaryImageUrlProvider(imageId));
    return urlAsync.when(
      data: (url) {
        if (url == null || url.isEmpty) {
          return const Center(child: Text('🐾', style: TextStyle(fontSize: 20)));
        }
        return Image.network(
          url,
          fit: BoxFit.cover,
          width: 40,
          height: 40,
          errorBuilder: (_, _, _) =>
              const Center(child: Text('🐾', style: TextStyle(fontSize: 20))),
        );
      },
      loading: () => const Center(
        child: SizedBox(
          width: 14,
          height: 14,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
      error: (_, _) => const Center(child: Text('🐾', style: TextStyle(fontSize: 20))),
    );
  }
}

// ─── 회원탈퇴 ────────────────────────────────────────────────────
class _NotificationSettingSection extends ConsumerWidget {
  const _NotificationSettingSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final enabled = ref.watch(notificationEnabledProvider);

    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            const Icon(
              LucideIcons.bell,
              color: AppColors.brandOrange,
              size: 18,
            ),
            const SizedBox(width: 8),
            const Expanded(
              child: Text(
                '알림 설정',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: AppColors.darkBrown,
                ),
              ),
            ),
            Switch.adaptive(
              value: enabled,
              activeColor: AppColors.brandOrange,
              onChanged: (_) =>
                  ref.read(notificationEnabledProvider.notifier).toggle(),
            ),
          ],
        ),
      ),
    );
  }
}

class _CustomerServiceSection extends StatelessWidget {
  const _CustomerServiceSection();

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) => const InquiryScreen(),
          ),
        ),
        borderRadius: BorderRadius.circular(16),
        child: const Padding(
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Row(
            children: [
              Icon(LucideIcons.mailQuestion, size: 20,
                  color: AppColors.brandOrange),
              SizedBox(width: 12),
              Text(
                '문의하기',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
              ),
              Spacer(),
              Icon(LucideIcons.chevronRight, size: 18,
                  color: AppColors.mutedForeground),
            ],
          ),
        ),
      ),
    );
  }
}

class _PolicySection extends StatelessWidget {
  const _PolicySection();

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
        child: Column(
          children: [
            _CsRow(
              icon: LucideIcons.fileText,
              label: '이용약관',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => const _PolicyPage(
                    title: '이용약관',
                    content: _termsOfService,
                  ),
                ),
              ),
            ),
            _CsRow(
              icon: LucideIcons.shield,
              label: '개인정보 처리방침',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => const _PolicyPage(
                    title: '개인정보 처리방침',
                    content: _privacyPolicy,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CsRow extends StatelessWidget {
  const _CsRow({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Icon(icon, size: 18, color: AppColors.mutedForeground),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.w500),
              ),
            ),
            const Icon(LucideIcons.chevronRight, size: 16,
                color: AppColors.mutedForeground),
          ],
        ),
      ),
    );
  }
}

class _PolicyPage extends StatelessWidget {
  const _PolicyPage({required this.title, required this.content});

  final String title;
  final String content;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9F5F0),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(LucideIcons.arrowLeft, color: AppColors.darkBrown),
          onPressed: () => Navigator.of(context).pop(),
        ),
        centerTitle: true,
        title: Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: AppColors.darkBrown,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
        child: Card(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Text(
              content,
              style: const TextStyle(
                fontSize: 13,
                height: 1.7,
                color: AppColors.darkBrown,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

const _termsOfService = '''
제1조 (목적)
이 약관은 위드독(이하 "회사")이 제공하는 모바일 애플리케이션 서비스(이하 "서비스")의 이용 조건 및 절차에 관한 사항을 규정함을 목적으로 합니다.

제2조 (서비스의 내용)
① 회사는 다음과 같은 서비스를 제공합니다.
  1. AI 기반 반려견 동반 장소 추천
  2. AI 그림일기 생성
  3. AI 챗봇 상담
② 서비스의 세부 내용은 회사의 정책에 따라 변경될 수 있습니다.

제3조 (이용자의 의무)
① 이용자는 관계 법령, 이 약관의 규정, 이용 안내 등을 준수하여야 합니다.
② 이용자는 타인의 정보를 도용하거나 서비스를 부정하게 이용해서는 안 됩니다.

제4조 (면책 조항)
① AI가 생성한 콘텐츠(그림, 텍스트 등)는 참고용이며, 정확성을 보장하지 않습니다.
② 장소 추천 정보는 실제와 다를 수 있으며, 방문 전 확인을 권장합니다.

제5조 (서비스 변경 및 중단)
회사는 운영상, 기술상 필요에 따라 서비스를 변경하거나 중단할 수 있습니다.
''';

const _privacyPolicy = '''
위드독(이하 "회사")은 이용자의 개인정보를 소중히 보호합니다.

1. 수집하는 개인정보 항목
  • 소셜 로그인 시: 이름, 이메일, 프로필 사진 (OAuth 제공 범위)
  • 반려견 정보: 이름, 견종, 생년월일, 성별, 성격 태그
  • 서비스 이용 기록: 일기 내용, 채팅 기록, 즐겨찾기 장소

2. 개인정보 이용 목적
  • 서비스 제공 및 운영
  • AI 맞춤 콘텐츠 생성 (그림일기, 장소 추천)
  • 서비스 개선 및 통계 분석

3. 개인정보 보유 기간
  • 회원 탈퇴 시 즉시 파기
  • 관계 법령에 의한 보존 기간이 있는 경우 해당 기간 보관

4. 개인정보 제3자 제공
  • 이용자의 동의 없이 제3자에게 개인정보를 제공하지 않습니다.
  • 단, AI 서비스 운영을 위해 OpenAI API에 텍스트 데이터가 전송될 수 있습니다.

5. 개인정보 보호 책임자
  • 위드독 개발팀 (withdog.dev@gmail.com)
''';

class _AppVersionSection extends StatelessWidget {
  const _AppVersionSection();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<PackageInfo>(
      future: PackageInfo.fromPlatform(),
      builder: (context, snapshot) {
        final version = snapshot.hasData
            ? 'v${snapshot.data!.version} (${snapshot.data!.buildNumber})'
            : '...';
        return Card(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Row(
              children: [
                const Icon(LucideIcons.info, size: 20, color: AppColors.mutedForeground),
                const SizedBox(width: 12),
                const Text(
                  '앱 버전',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
                ),
                const Spacer(),
                Text(
                  version,
                  style: const TextStyle(
                    fontSize: 14,
                    color: AppColors.mutedForeground,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _WithdrawButton extends ConsumerWidget {
  const _WithdrawButton({required this.user, required this.onLogout});

  final User user;
  final Future<void> Function() onLogout;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Center(
      child: TextButton(
        onPressed: () => _confirmWithdraw(context, ref),
        style: TextButton.styleFrom(
          foregroundColor: AppColors.mutedForeground,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        ),
        child: const Text(
          '회원탈퇴',
          style: TextStyle(fontSize: 12, decoration: TextDecoration.underline),
        ),
      ),
    );
  }

  Future<void> _confirmWithdraw(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('회원탈퇴'),
        content: const Text(
          '정말 탈퇴하시겠습니까?\n탈퇴 후 10일 이내에 다시 로그인하면 계정을 복구할 수 있습니다.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('취소'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.destructive,
            ),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('탈퇴'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ref.read(authProvider.notifier).withdraw();
      Fluttertoast.showToast(msg: '회원탈퇴가 완료되었습니다.');
    } catch (e) {
      Fluttertoast.showToast(msg: '회원탈퇴 실패: $e');
    }
  }
}
