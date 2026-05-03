import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/pet.dart';
import '../../shared/models/place.dart';
import '../../shared/models/user.dart';
import '../auth/auth_providers.dart';
import '../diary/diary_list_provider.dart';
import '../diary/widgets/diary_card_tile.dart';
import '../onboarding/onboarding_providers.dart';
import '../places/place_providers.dart';
import '../places/widgets/facility_modal_sheet.dart';
import 'widgets/primary_pet_change_modal.dart';

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
      return const _Unauthenticated();
    }
    return _Authenticated(
      user: auth.user,
      onLogout: () async {
        await ref.read(authProvider.notifier).logout();
      },
    );
  }
}

class _Unauthenticated extends StatelessWidget {
  const _Unauthenticated();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 96,
                height: 96,
                decoration: const BoxDecoration(
                  color: AppColors.peach,
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: const Icon(
                  LucideIcons.user,
                  size: 40,
                  color: AppColors.brandOrange,
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                '로그인 후 더 많은 기능을 이용해요',
                style: TextStyle(
                  fontSize: 16,
                  color: AppColors.subBrown2,
                ),
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: () => context.go(AppRoutes.login),
                icon: const Icon(LucideIcons.logIn, size: 18),
                label: const Text('로그인하기'),
              ),
            ],
          ),
        ),
      ),
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
            const _PetListSection(),
            const SizedBox(height: 16),
            const _FavoritePlacesSection(),
            const SizedBox(height: 16),
            const _FavoriteDiariesSection(),
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

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const CircleAvatar(
              radius: 28,
              backgroundColor: AppColors.peach,
              child: Icon(
                LucideIcons.user,
                color: AppColors.brandOrange,
                size: 28,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '${user.nickname}님',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user.email,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.mutedForeground,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.peach,
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      '${user.provider} 로그인',
                      style: const TextStyle(
                        fontSize: 10,
                        color: AppColors.brandOrange,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              tooltip: '로그아웃',
              icon: const Icon(LucideIcons.logOut, size: 18),
              onPressed: onLogout,
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.icon,
    required this.title,
    this.action,
  });

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

// (1) 대표 반려견 ─────────────────────────────────────────────────
class _PrimaryPetSection extends StatelessWidget {
  const _PrimaryPetSection({required this.user});

  final User user;

  void _openChangeModal(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => PrimaryPetChangeModal(user: user),
    );
  }

  @override
  Widget build(BuildContext context) {
    final pet = user.primaryPet;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SectionHeader(
              icon: LucideIcons.crown,
              title: '대표 반려견',
              action: pet == null
                  ? null
                  : TextButton(
                      onPressed: () => _openChangeModal(context),
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.brandOrange,
                        padding:
                            const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      ),
                      child: const Text('변경'),
                    ),
            ),
            if (pet == null)
              const Text(
                '아직 등록된 반려견이 없어요. 시작 흐름에서 반려견을 등록하면 자동으로 대표가 돼요.',
                style: TextStyle(color: AppColors.subBrown2),
              )
            else
              _PrimaryPetCardBody(pet: pet),
          ],
        ),
      ),
    );
  }
}

class _PrimaryPetCardBody extends StatelessWidget {
  const _PrimaryPetCardBody({required this.pet});

  final Pet pet;

  @override
  Widget build(BuildContext context) {
    final tags = pet.selectedTags?.cast<dynamic>() ?? const [];
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const CircleAvatar(
          radius: 32,
          backgroundColor: AppColors.peach,
          child: Icon(LucideIcons.dog, color: AppColors.brandOrange, size: 32),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                pet.name,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: AppColors.darkBrown,
                ),
              ),
              const SizedBox(height: 4),
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: [
                  if (pet.age != null) _Chip(text: '${pet.age}세'),
                  if (pet.birthDate != null)
                    _Chip(text: _formatDate(pet.birthDate!)),
                  if (pet.gender != null) _Chip(text: pet.gender!.label),
                  _Chip(
                    text: pet.isNeutered == true
                        ? '중성화 O'
                        : pet.isNeutered == false
                            ? '중성화 X'
                            : '중성화 미상',
                  ),
                ],
              ),
              if (tags.isNotEmpty) ...[
                const SizedBox(height: 6),
                Text(
                  '성격 태그 ${tags.length}건',
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.mutedForeground,
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  static String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';
}

class _Chip extends StatelessWidget {
  const _Chip({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.peach,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 11,
          color: AppColors.brandOrange,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}

// (2) 반려견 목록 그리드 ───────────────────────────────────────────
class _PetListSection extends ConsumerWidget {
  const _PetListSection();

  Future<void> _confirmDelete(
    BuildContext context,
    WidgetRef ref,
    Pet pet,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('반려견 삭제'),
        content: Text('"${pet.name}" 정보를 삭제할까요? (soft delete)'),
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
      // PetApi.delete 가 미구현 — 현재 구조엔 PATCH/DELETE 메서드만 listByUser·create.
      // Step 4 1차 진척 = 메뉴 골격 박힘. 실제 API 호출은 PetApi 확장 후 (별도 작업).
      Fluttertoast.showToast(
        msg: '반려견 삭제 API 는 PetApi 확장 후 활성 (다음 작업)',
      );
    } catch (e) {
      Fluttertoast.showToast(msg: '삭제 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pets = ref.watch(userPetsProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _SectionHeader(
              icon: LucideIcons.dog,
              title: '반려견 목록',
              action: TextButton.icon(
                onPressed: () => Fluttertoast.showToast(
                  msg: '반려견 추가는 시작 흐름 또는 Step 7 폴리싱에서 본격 구현 예정',
                ),
                icon: const Icon(LucideIcons.plus, size: 14),
                label: const Text('추가'),
                style: TextButton.styleFrom(
                  foregroundColor: AppColors.brandOrange,
                ),
              ),
            ),
            pets.when(
              data: (list) {
                if (list.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text(
                      '등록된 반려견이 없어요.',
                      style: TextStyle(color: AppColors.mutedForeground),
                    ),
                  );
                }
                return GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate:
                      const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 1.4,
                    crossAxisSpacing: 8,
                    mainAxisSpacing: 8,
                  ),
                  itemCount: list.length,
                  itemBuilder: (_, i) => _PetGridCard(
                    pet: list[i],
                    onDelete: () => _confirmDelete(context, ref, list[i]),
                  ),
                );
              },
              loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Text(
                  '반려견 목록 로드 실패: $e',
                  style: const TextStyle(color: AppColors.destructive),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PetGridCard extends StatelessWidget {
  const _PetGridCard({required this.pet, required this.onDelete});

  final Pet pet;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.beige),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.peach,
                  child: Icon(
                    LucideIcons.dog,
                    color: AppColors.brandOrange,
                    size: 14,
                  ),
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    pet.name,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                PopupMenuButton<String>(
                  iconSize: 16,
                  padding: EdgeInsets.zero,
                  onSelected: (v) {
                    if (v == 'delete') onDelete();
                  },
                  itemBuilder: (_) => const [
                    PopupMenuItem(value: 'delete', child: Text('삭제')),
                  ],
                ),
              ],
            ),
            const Spacer(),
            Text(
              pet.age != null ? '${pet.age}세' : '',
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.mutedForeground,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// (3) 즐겨찾기 장소 그리드 ─────────────────────────────────────────
class _FavoritePlacesSection extends ConsumerWidget {
  const _FavoritePlacesSection();

  void _openFacility(BuildContext context, PlaceFavoriteItem item) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => FacilityModalSheet(name: item.name),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(favoritePlacesProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const _SectionHeader(
              icon: LucideIcons.heart,
              title: '즐겨찾기 장소',
            ),
            favorites.when(
              data: (list) {
                if (list.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text(
                      '아직 즐겨찾기한 장소가 없어요.\n장소 카드의 ❤️ 토글로 추가해보세요.',
                      style: TextStyle(color: AppColors.mutedForeground),
                    ),
                  );
                }
                return Column(
                  children: [
                    for (final item in list)
                      _FavoritePlaceTile(
                        item: item,
                        onTap: () => _openFacility(context, item),
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
            const Icon(LucideIcons.mapPin, size: 18, color: AppColors.brandOrange),
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

// (4) 즐겨찾기 다이어리 그리드 ────────────────────────────────────
class _FavoriteDiariesSection extends ConsumerWidget {
  const _FavoriteDiariesSection();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final all = ref.watch(diaryListProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const _SectionHeader(
              icon: LucideIcons.star,
              title: '즐겨찾기 다이어리',
            ),
            all.when(
              data: (list) {
                final favs = list.where((d) => d.isFavorite).toList();
                if (favs.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text(
                      '즐겨찾기한 일기가 없어요.\n캘린더·목록의 ⭐ 토글로 추가해보세요.',
                      style: TextStyle(color: AppColors.mutedForeground),
                    ),
                  );
                }
                return GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate:
                      const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 0.78,
                    crossAxisSpacing: 8,
                    mainAxisSpacing: 8,
                  ),
                  itemCount: favs.length,
                  itemBuilder: (_, i) => DiaryCardTile(diary: favs[i]),
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
        ),
      ),
    );
  }
}
