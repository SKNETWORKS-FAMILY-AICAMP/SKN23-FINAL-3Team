import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/models/diary.dart';
import '../onboarding/onboarding_providers.dart';
import 'diary_providers.dart';

/// 다이어리 상세 모달 시트 — 캘린더 셀 / 목록 카드 클릭 진입 공용.
/// UI 디테일 #4 정합 (`showModalBottomSheet isScrollControlled: true`).
class DiaryDetailModalSheet extends ConsumerStatefulWidget {
  const DiaryDetailModalSheet({super.key, required this.diaryId});

  final int diaryId;

  @override
  ConsumerState<DiaryDetailModalSheet> createState() =>
      _DiaryDetailModalSheetState();
}

class _DiaryDetailModalSheetState
    extends ConsumerState<DiaryDetailModalSheet> {
  late Future<Diary> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(diaryApiProvider).get(widget.diaryId);
  }

  Future<void> _toggleFavorite(Diary diary) async {
    try {
      final updated =
          await ref.read(diaryApiProvider).toggleFavorite(diary.id);
      setState(() => _future = Future.value(updated));
      Fluttertoast.showToast(
        msg: updated.isFavorite ? '즐겨찾기 추가' : '즐겨찾기 해제',
      );
    } catch (e) {
      Fluttertoast.showToast(msg: '즐겨찾기 토글 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, scrollController) {
        return FutureBuilder<Diary>(
          future: _future,
          builder: (_, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _Error(message: '${snapshot.error}', onClose: () {
                Navigator.of(context).pop();
              });
            }
            final diary = snapshot.data!;
            return _Body(
              diary: diary,
              scrollController: scrollController,
              onToggleFavorite: () => _toggleFavorite(diary),
              onClose: () => Navigator.of(context).pop(),
            );
          },
        );
      },
    );
  }
}

class _Body extends ConsumerWidget {
  const _Body({
    required this.diary,
    required this.scrollController,
    required this.onToggleFavorite,
    required this.onClose,
  });

  final Diary diary;
  final ScrollController scrollController;
  final VoidCallback onToggleFavorite;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 12, 4),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  diary.title ?? '오늘의 일기',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.darkBrown,
                  ),
                ),
              ),
              IconButton(
                tooltip: diary.isFavorite ? '즐겨찾기 해제' : '즐겨찾기',
                icon: Icon(
                  LucideIcons.star,
                  color: diary.isFavorite
                      ? AppColors.brandOrange
                      : AppColors.mutedForeground,
                ),
                onPressed: onToggleFavorite,
              ),
              IconButton(
                icon: const Icon(LucideIcons.x),
                onPressed: onClose,
              ),
            ],
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Bug #1 — imageId 있으면 상단 그림 이미지. autoDispose family
                // 캐시 (`diaryImageUrlProvider`) 라 grid 와 detail 간 중복 fetch X.
                if (diary.imageId != null)
                  _DetailImage(imageId: diary.imageId!),
                if (diary.imageId != null)
                  const SizedBox(height: 16),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _Tag(
                      icon: Icons.calendar_today,
                      text: _formatDate(diary.diaryDate),
                    ),
                    if (diary.emotion?.isNotEmpty == true)
                      _Tag(text: diary.emotion!),
                    if (diary.whereText?.isNotEmpty == true)
                      _Tag(
                        icon: Icons.location_pin,
                        text: diary.whereText!,
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                if (diary.summary?.isNotEmpty == true)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.peach,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      diary.summary!,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.brandOrange,
                      ),
                    ),
                  ),
                if (diary.content?.isNotEmpty == true) ...[
                  const SizedBox(height: 16),
                  Text(
                    diary.content!,
                    style: const TextStyle(
                      fontSize: 14,
                      color: AppColors.darkBrown,
                      height: 1.7,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  String _formatDate(DateTime d) =>
      '${d.year}.${d.month.toString().padLeft(2, '0')}.${d.day.toString().padLeft(2, '0')}';
}

class _DetailImage extends ConsumerWidget {
  const _DetailImage({required this.imageId});

  final int imageId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urlAsync = ref.watch(diaryImageUrlProvider(imageId));
    return urlAsync.when(
      data: (url) {
        if (url == null || url.isEmpty) return const SizedBox.shrink();
        return ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Image.network(
            url,
            width: double.infinity,
            fit: BoxFit.cover,
            errorBuilder: (_, _, _) => const SizedBox.shrink(),
          ),
        );
      },
      loading: () => Container(
        height: 200,
        decoration: BoxDecoration(
          color: AppColors.peach,
          borderRadius: BorderRadius.circular(16),
        ),
        alignment: Alignment.center,
        child: const CircularProgressIndicator(),
      ),
      error: (_, _) => const SizedBox.shrink(),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag({this.icon, required this.text});

  final IconData? icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.peach,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 12, color: AppColors.brandOrange),
            const SizedBox(width: 4),
          ],
          Text(
            text,
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.brandOrange,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class _Error extends StatelessWidget {
  const _Error({required this.message, required this.onClose});

  final String message;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(LucideIcons.alertCircle, color: AppColors.destructive),
          const SizedBox(height: 12),
          Text(
            '일기를 불러오지 못했습니다.\n$message',
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.subBrown2),
          ),
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onClose, child: const Text('닫기')),
        ],
      ),
    );
  }
}
