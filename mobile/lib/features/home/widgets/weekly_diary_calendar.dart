import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/diary.dart';
import '../../diary/diary_detail_modal_sheet.dart';
import '../../diary/diary_list_provider.dart';
import '../../diary/diary_providers.dart';
import '../../onboarding/onboarding_providers.dart';
import '../home_tab_index.dart';

// ── 날짜 유틸 ─────────────────────────────────────────────────────────────

/// DateTime을 yyyy-MM-dd 문자열로 정규화 (시/분/초 제거).
String _dateKey(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-'
    '${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

/// 오늘 기준 이번 주 월요일~일요일 7일을 반환.
List<DateTime> _weekDays(DateTime today) {
  final mondayOffset = today.weekday - 1;
  final monday = DateTime(today.year, today.month, today.day - mondayOffset);
  return List.generate(7, (i) => monday.add(Duration(days: i)));
}

const _weekLabels = ['월', '화', '수', '목', '금', '토', '일'];

// ── Provider ─────────────────────────────────────────────────────────────

/// 이번 주 7일 각각에 일기가 작성됐는지 여부를 반환.
final weeklyDiaryDatesProvider = Provider.autoDispose<Set<String>>((ref) {
  final diaryAsync = ref.watch(diaryListProvider);
  return diaryAsync.when(
    data: (diaries) => diaries.map((d) => _dateKey(d.diaryDate)).toSet(),
    loading: () => const {},
    error: (_, __) => const {},
  );
});

/// 날짜별 일기 목록 (최신순 정렬).
final weeklyDiariesByDateProvider =
    Provider.autoDispose<Map<String, List<Diary>>>((ref) {
  final diaryAsync = ref.watch(diaryListProvider);
  return diaryAsync.when(
    data: (diaries) {
      final map = <String, List<Diary>>{};
      final sorted = List<Diary>.from(diaries)
        ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
      for (final d in sorted) {
        final key = _dateKey(d.diaryDate);
        map.putIfAbsent(key, () => []).add(d);
      }
      return map;
    },
    loading: () => const {},
    error: (_, __) => const {},
  );
});

// ── 메인 위젯 ─────────────────────────────────────────────────────────────

class WeeklyDiaryCalendar extends ConsumerStatefulWidget {
  const WeeklyDiaryCalendar({super.key});

  @override
  ConsumerState<WeeklyDiaryCalendar> createState() =>
      _WeeklyDiaryCalendarState();
}

class _WeeklyDiaryCalendarState extends ConsumerState<WeeklyDiaryCalendar> {
  String? _selectedDateKey;

  @override
  Widget build(BuildContext context) {
    final today = DateTime.now();
    final days = _weekDays(today);
    final writtenDates = ref.watch(weeklyDiaryDatesProvider);
    final diariesByDate = ref.watch(weeklyDiariesByDateProvider);
    final todayKey = _dateKey(today);

    // 선택된 날짜의 일기 목록
    final selectedDiaries =
        _selectedDateKey != null ? (diariesByDate[_selectedDateKey] ?? []) : <Diary>[];
    final latestDiary = selectedDiaries.isNotEmpty ? selectedDiaries.first : null;
    final hasMoreDiaries = selectedDiaries.length > 1;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 12,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── 헤더 + 날짜 행 ──
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
            child: Column(
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.edit_note_rounded,
                      color: AppColors.brandOrange,
                      size: 18,
                    ),
                    const SizedBox(width: 6),
                    const Text(
                      '주간 달력',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: AppColors.darkBrown,
                      ),
                    ),
                    const Spacer(),
                    _DiaryCountBadge(writtenDates: writtenDates, days: days),
                  ],
                ),
                const SizedBox(height: 14),
                // ── 7일 날짜 행 ──
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(7, (i) {
                    final day = days[i];
                    final key = _dateKey(day);
                    final isToday = key == todayKey;
                    final hasEntry = writtenDates.contains(key);
                    final isSelected = _selectedDateKey == key;

                    return _DayCell(
                      day: day,
                      weekLabel: _weekLabels[i],
                      isToday: isToday,
                      hasEntry: hasEntry,
                      isSelected: isSelected,
                      onTap: () {
                        setState(() {
                          _selectedDateKey = _selectedDateKey == key ? null : key;
                        });
                      },
                    );
                  }),
                ),
                const SizedBox(height: 10),
              ],
            ),
          ),
          // ── 선택된 날짜의 최신 일기 1건 ──
          if (latestDiary != null) ...[
            const Divider(height: 1, color: Color(0xFFF3E4D3)),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _RecentDiaryTile(diary: latestDiary),
                  if (hasMoreDiaries) ...[
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      child: TextButton(
                        onPressed: () {
                          ref.read(homeTabIndexProvider.notifier).state = 1;
                        },
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                            side: const BorderSide(color: AppColors.beige),
                          ),
                        ),
                        child: const Text(
                          '더보기',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: AppColors.brandOrange,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ] else
            const SizedBox(height: 4),
        ],
      ),
    );
  }
}

// ── 날짜 셀 (체크 표시만) ──────────────────────────────────────────────

class _DayCell extends StatelessWidget {
  const _DayCell({
    required this.day,
    required this.weekLabel,
    required this.isToday,
    required this.hasEntry,
    required this.isSelected,
    required this.onTap,
  });

  final DateTime day;
  final String weekLabel;
  final bool isToday;
  final bool hasEntry;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isSaturday = day.weekday == 6;
    final isSunday = day.weekday == 7;

    final weekLabelColor = isToday
        ? AppColors.brandOrange
        : isSaturday
            ? const Color(0xFF5B8DEF)
            : isSunday
                ? const Color(0xFFEF5B5B)
                : AppColors.subBrown2;

    final dayNumColor = isToday
        ? Colors.white
        : isSelected
            ? AppColors.brandOrange
            : AppColors.darkBrown;

    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 40,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 요일 라벨
            Text(
              weekLabel,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: weekLabelColor,
              ),
            ),
            const SizedBox(height: 4),
            // 날짜 숫자 + 오늘 강조 원 / 선택 강조 테두리
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isToday ? AppColors.brandOrange : Colors.transparent,
                border: isSelected && !isToday
                    ? Border.all(color: AppColors.brandOrange, width: 2)
                    : null,
              ),
              alignment: Alignment.center,
              child: Text(
                '${day.day}',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: dayNumColor,
                ),
              ),
            ),
            const SizedBox(height: 4),
            // 일기 작성 시 체크 표시
            SizedBox(
              height: 20,
              child: hasEntry
                  ? const Icon(
                      Icons.check,
                      size: 16,
                      color: AppColors.brandOrange,
                    )
                  : const SizedBox.shrink(),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 주간 작성 수 배지 ─────────────────────────────────────────────────────

class _DiaryCountBadge extends StatelessWidget {
  const _DiaryCountBadge({required this.writtenDates, required this.days});

  final Set<String> writtenDates;
  final List<DateTime> days;

  @override
  Widget build(BuildContext context) {
    final count = days.where((d) => writtenDates.contains(_dateKey(d))).length;
    if (count == 0) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.peach,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        '이번 주 $count일 작성',
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w700,
          color: AppColors.brandOrange,
        ),
      ),
    );
  }
}

// ── 최근 일기 미리보기 타일 ───────────────────────────────────────────────

class _RecentDiaryTile extends ConsumerWidget {
  const _RecentDiaryTile({required this.diary});

  final Diary diary;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final emoji = diary.emotion != null && diary.emotion!.isNotEmpty
        ? diary.emotion!
        : '🐾';

    return GestureDetector(
      onTap: () {
        showModalBottomSheet<void>(
          context: context,
          isScrollControlled: true,
          backgroundColor: Colors.transparent,
          builder: (_) => DiaryDetailModalSheet(diaryId: diary.id),
        );
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF8F3),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            // 이모지 or 썸네일
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.peach,
                borderRadius: BorderRadius.circular(8),
              ),
              clipBehavior: Clip.antiAlias,
              child: diary.imageId != null
                  ? _TinyImage(imageId: diary.imageId!)
                  : Center(
                      child: Text(emoji, style: const TextStyle(fontSize: 16)),
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
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.darkBrown,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    _formatShortDate(diary.diaryDate),
                    style: const TextStyle(
                      fontSize: 10,
                      color: AppColors.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
            Text(emoji, style: const TextStyle(fontSize: 14)),
            const SizedBox(width: 4),
            const Icon(
              LucideIcons.chevronRight,
              size: 14,
              color: AppColors.mutedForeground,
            ),
          ],
        ),
      ),
    );
  }

  static String _formatShortDate(DateTime d) =>
      '${d.month}/${d.day}';
}

class _TinyImage extends ConsumerWidget {
  const _TinyImage({required this.imageId});

  final int imageId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urlAsync = ref.watch(diaryImageUrlProvider(imageId));
    return urlAsync.when(
      data: (url) {
        if (url == null || url.isEmpty) {
          return const Center(
              child: Text('🐾', style: TextStyle(fontSize: 14)));
        }
        return Image.network(
          url,
          fit: BoxFit.cover,
          width: 32,
          height: 32,
          errorBuilder: (_, _, _) =>
              const Center(child: Text('🐾', style: TextStyle(fontSize: 14))),
        );
      },
      loading: () => const Center(
        child: SizedBox(
          width: 12,
          height: 12,
          child: CircularProgressIndicator(strokeWidth: 1.5),
        ),
      ),
      error: (_, _) =>
          const Center(child: Text('🐾', style: TextStyle(fontSize: 14))),
    );
  }
}
