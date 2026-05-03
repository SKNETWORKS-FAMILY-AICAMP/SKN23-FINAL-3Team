import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/diary.dart';
import '../diary_detail_modal_sheet.dart';
import '../diary_list_provider.dart';
import '../diary_providers.dart';

/// 다이어리 카드 그리드 셀 — DiaryTab 목록 + MyPage 즐겨다이어리 공용.
///
/// 이미지 placeholder = 감정 emoji 36px (1차 동작 우선원칙). 좌상단 ⭐ 토글
/// (5/2 신규 `PATCH /diaries/{id}/favorite`, atomic SWAP). 카드 탭 →
/// `DiaryDetailModalSheet`.
class DiaryCardTile extends ConsumerWidget {
  const DiaryCardTile({super.key, required this.diary});

  final Diary diary;

  Future<void> _toggleFavorite(WidgetRef ref) async {
    try {
      await ref.read(diaryApiProvider).toggleFavorite(diary.id);
      ref.invalidate(diaryListProvider);
      ref.invalidate(favoriteCalendarProvider);
    } catch (e) {
      Fluttertoast.showToast(msg: '즐겨찾기 토글 실패: $e');
    }
  }

  void _openDetail(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => DiaryDetailModalSheet(diaryId: diary.id),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () => _openDetail(context),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: AppColors.beige),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Stack(
                children: [
                  Container(
                    width: double.infinity,
                    decoration: const BoxDecoration(
                      color: AppColors.peach,
                      borderRadius:
                          BorderRadius.vertical(top: Radius.circular(12)),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      diary.emotion ?? '🐾',
                      style: const TextStyle(fontSize: 36),
                    ),
                  ),
                  Positioned(
                    top: 4,
                    left: 4,
                    child: IconButton(
                      visualDensity: VisualDensity.compact,
                      icon: Icon(
                        LucideIcons.star,
                        size: 18,
                        color: diary.isFavorite
                            ? AppColors.brandOrange
                            : Colors.white,
                      ),
                      tooltip: '즐겨찾기',
                      onPressed: () => _toggleFavorite(ref),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    diary.title ?? '오늘의 일기',
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
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
          ],
        ),
      ),
    );
  }

  static String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';
}
