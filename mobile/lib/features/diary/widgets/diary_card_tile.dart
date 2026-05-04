import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/diary.dart';
import '../../onboarding/onboarding_providers.dart';
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
    } on DioException catch (e) {
      // 백엔드 detail (HTTPException 메시지) 가 있으면 우선 노출 — Toast 만으론
      // 원인 추적 어려워 device-side 진단 도와주는 패턴.
      final detail = e.response?.data is Map
          ? (e.response!.data as Map)['detail']?.toString()
          : null;
      final code = e.response?.statusCode;
      Fluttertoast.showToast(
        msg: detail != null
            ? '즐겨찾기 토글 실패 ($code): $detail'
            : '즐겨찾기 토글 실패: ${e.type.name} ${e.message ?? ''}',
      );
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
                  // Bug #2 — imageId 있으면 그림 이미지 우선, 없으면 감정 emoji.
                  // diaryImageUrlProvider 가 family 캐시 — 같은 image 가 grid 에서
                  // 중복 fetch 안 됨.
                  ClipRRect(
                    borderRadius:
                        const BorderRadius.vertical(top: Radius.circular(12)),
                    child: SizedBox(
                      width: double.infinity,
                      child: diary.imageId != null
                          ? _DiaryImage(imageId: diary.imageId!, fallbackEmoji: diary.emotion)
                          : _EmotionPlaceholder(emoji: diary.emotion ?? '🐾'),
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

/// imageId 로 S3 file_url 받아 Image.network. URL fetch 실패 / 이미지 로드 실패
/// 시 감정 emoji placeholder 로 graceful degrade.
class _DiaryImage extends ConsumerWidget {
  const _DiaryImage({required this.imageId, this.fallbackEmoji});

  final int imageId;
  final String? fallbackEmoji;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urlAsync = ref.watch(diaryImageUrlProvider(imageId));
    return urlAsync.when(
      data: (url) {
        if (url == null || url.isEmpty) {
          return _EmotionPlaceholder(emoji: fallbackEmoji ?? '🐾');
        }
        return Image.network(
          url,
          fit: BoxFit.cover,
          errorBuilder: (_, _, _) =>
              _EmotionPlaceholder(emoji: fallbackEmoji ?? '🐾'),
        );
      },
      loading: () => Container(
        color: AppColors.peach,
        alignment: Alignment.center,
        child: const SizedBox(
          width: 18,
          height: 18,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      ),
      error: (_, _) => _EmotionPlaceholder(emoji: fallbackEmoji ?? '🐾'),
    );
  }
}

class _EmotionPlaceholder extends StatelessWidget {
  const _EmotionPlaceholder({required this.emoji});

  final String emoji;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.peach,
      alignment: Alignment.center,
      child: Text(emoji, style: const TextStyle(fontSize: 36)),
    );
  }
}
