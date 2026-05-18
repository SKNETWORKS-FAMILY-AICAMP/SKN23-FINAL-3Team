import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/models/app_notification.dart';
import '../../shared/models/diary.dart';
import '../notification/notification_provider.dart';
import '../onboarding/onboarding_providers.dart';
import 'diary_list_provider.dart';
import 'diary_providers.dart';
import 'widgets/diary_edit_modal.dart';

/// 다이어리 상세 모달 시트 — 캘린더 셀 / 목록 카드 클릭 진입 공용.
/// UI 디테일 #4 정합 (`showModalBottomSheet isScrollControlled: true`).
class DiaryDetailModalSheet extends ConsumerStatefulWidget {
  const DiaryDetailModalSheet({super.key, required this.diaryId});

  final int diaryId;

  @override
  ConsumerState<DiaryDetailModalSheet> createState() =>
      _DiaryDetailModalSheetState();
}

class _DiaryDetailModalSheetState extends ConsumerState<DiaryDetailModalSheet> {
  late Future<Diary> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(diaryApiProvider).get(widget.diaryId);
  }

  Future<void> _openEditModal(Diary diary) async {
    final updated = await showModalBottomSheet<Diary>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DiaryEditModal(diary: diary),
    );
    if (updated != null && mounted) {
      setState(() => _future = Future.value(updated));
      ref.invalidate(diaryListProvider);
      ref.invalidate(favoriteCalendarProvider);
    }
  }

  Future<void> _toggleFavorite(Diary diary) async {
    try {
      final updated = await ref.read(diaryApiProvider).toggleFavorite(diary.id);
      setState(() => _future = Future.value(updated));
      ref.invalidate(diaryListProvider);
      ref.invalidate(favoriteCalendarProvider);
      Fluttertoast.showToast(msg: updated.isFavorite ? '즐겨찾기 추가' : '즐겨찾기 해제');
      if (updated.isFavorite) {
        ref.read(notificationProvider.notifier).push(
              type: NotificationType.favoriteAdded,
              title: '즐겨찾기에 추가했어요!',
              body: '${updated.title ?? '일기'}를 즐겨찾기에 추가했어요 ⭐',
            );
      }
    } catch (e) {
      Fluttertoast.showToast(msg: '즐겨찾기 토글 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.92,
      minChildSize: 0.5,
      maxChildSize: 0.98,
      expand: false,
      builder: (_, scrollController) {
        return FutureBuilder<Diary>(
          future: _future,
          builder: (_, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _Error(
                message: '${snapshot.error}',
                onClose: () {
                  Navigator.of(context).pop();
                },
              );
            }
            final diary = snapshot.data!;
            return _Body(
              diary: diary,
              scrollController: scrollController,
              onToggleFavorite: () => _toggleFavorite(diary),
              onEdit: () => _openEditModal(diary),
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
    required this.onEdit,
    required this.onClose,
  });

  final Diary diary;
  final ScrollController scrollController;
  final VoidCallback onToggleFavorite;
  final VoidCallback onEdit;
  final VoidCallback onClose;

  static const _creamBg = Color(0xFFFFFAF3);
  static const _paperBg = Color(0xFFFFF8EE);
  static const _borderColor = Color(0xFFF1DEC8);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      decoration: const BoxDecoration(
        color: _creamBg,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          // ── 상단 핸들 + 헤더 바 ──
          Container(
            decoration: const BoxDecoration(
              color: _creamBg,
              borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
              border: Border(bottom: BorderSide(color: _borderColor, width: 0.8)),
            ),
            child: Column(
              children: [
                const SizedBox(height: 10),
                // 드래그 핸들
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: const Color(0xFFD4C4B0),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Padding(
                  padding: const EdgeInsets.fromLTRB(4, 0, 4, 8),
                  child: Row(
                    children: [
                      IconButton(
                        tooltip: '닫기',
                        icon: const Icon(LucideIcons.chevronLeft, color: AppColors.darkBrown),
                        onPressed: onClose,
                      ),
                      Expanded(
                        child: Text(
                          '그림일기',
                          textAlign: TextAlign.center,
                          style: GoogleFonts.gaegu(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                            color: AppColors.darkBrown,
                          ),
                        ),
                      ),
                      IconButton(
                        tooltip: diary.isFavorite ? '즐겨찾기 해제' : '즐겨찾기',
                        icon: Icon(
                          diary.isFavorite ? Icons.star : Icons.star_border,
                          color: diary.isFavorite
                              ? AppColors.brandOrange
                              : AppColors.mutedForeground,
                        ),
                        onPressed: onToggleFavorite,
                      ),
                      IconButton(
                        tooltip: '수정',
                        icon: const Icon(LucideIcons.pencil, color: AppColors.mutedForeground),
                        onPressed: onEdit,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // ── 본문 ──
          Expanded(
            child: SingleChildScrollView(
              controller: scrollController,
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: _paperBg,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: _borderColor),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.brown.withValues(alpha: 0.06),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // 부제목
                    Text(
                      '오늘의 그림일기',
                      style: GoogleFonts.gaegu(
                        fontSize: 14,
                        color: AppColors.subBrown2,
                      ),
                    ),
                    const SizedBox(height: 4),
                    // 제목
                    Text(
                      diary.title ?? '오늘의 일기',
                      textAlign: TextAlign.center,
                      style: GoogleFonts.gaegu(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: AppColors.darkBrown,
                      ),
                    ),
                    const SizedBox(height: 10),
                    // 태그 행
                    Wrap(
                      alignment: WrapAlignment.center,
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
                          _Tag(icon: Icons.location_pin, text: diary.whereText!),
                      ],
                    ),
                    // 요약
                    if (diary.summary?.isNotEmpty == true) ...[
                      const SizedBox(height: 14),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFEFE3),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          diary.summary!,
                          textAlign: TextAlign.center,
                          style: GoogleFonts.gaegu(
                            fontSize: 13,
                            color: AppColors.brandOrange,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 18),
                    // 그림 이미지
                    if (diary.imageId != null) ...[
                      _DetailImage(imageId: diary.imageId!),
                      const SizedBox(height: 18),
                    ],
                    // 구분선
                    Container(
                      width: 60,
                      height: 1,
                      color: _borderColor,
                    ),
                    const SizedBox(height: 16),
                    // 일기 본문
                    if (diary.content?.isNotEmpty == true)
                      SizedBox(
                        width: double.infinity,
                        child: Text(
                          diary.content!,
                          style: GoogleFonts.gaegu(
                            fontSize: 17,
                            color: AppColors.darkBrown,
                            height: 1.8,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
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
