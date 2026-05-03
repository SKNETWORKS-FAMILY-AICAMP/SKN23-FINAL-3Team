import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/diary.dart';
import '../auth/auth_providers.dart';
import '../diary/diary_detail_modal_sheet.dart';
import '../diary/diary_list_provider.dart';
import '../diary/diary_providers.dart';
import '../diary/widgets/diary_card_tile.dart';

enum DiaryViewMode { calendar, list }

// FavoriteCalendarItem.firstWhere 의 orElse 용 sentinel.
final DateTime _epoch = DateTime.utc(1970);

void _openDiaryModal(BuildContext context, int diaryId) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (_) => DiaryDetailModalSheet(diaryId: diaryId),
  );
}

class DiaryTab extends ConsumerStatefulWidget {
  const DiaryTab({super.key});

  @override
  ConsumerState<DiaryTab> createState() => _DiaryTabState();
}

class _DiaryTabState extends ConsumerState<DiaryTab> {
  DiaryViewMode _mode = DiaryViewMode.calendar;
  DateTime _focusedMonth = DateTime(DateTime.now().year, DateTime.now().month);
  DateTime? _selectedDay;

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    if (auth is! AuthAuthenticated) {
      return const _DiaryTabUnauthenticated();
    }
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('다이어리'),
        backgroundColor: Colors.transparent,
        foregroundColor: AppColors.darkBrown,
        elevation: 0,
        actions: [
          SegmentedButton<DiaryViewMode>(
            segments: const [
              ButtonSegment(
                value: DiaryViewMode.calendar,
                icon: Icon(LucideIcons.calendar, size: 16),
                label: Text('캘린더'),
              ),
              ButtonSegment(
                value: DiaryViewMode.list,
                icon: Icon(LucideIcons.list, size: 16),
                label: Text('목록'),
              ),
            ],
            selected: {_mode},
            onSelectionChanged: (s) => setState(() => _mode = s.first),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: switch (_mode) {
        DiaryViewMode.calendar => _CalendarView(
            focused: _focusedMonth,
            selected: _selectedDay,
            onMonthChanged: (m) => setState(() => _focusedMonth = m),
            onDaySelected: (day) => setState(() => _selectedDay = day),
          ),
        DiaryViewMode.list => const _ListView(),
      },
    );
  }
}

class _DiaryTabUnauthenticated extends StatelessWidget {
  const _DiaryTabUnauthenticated();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              LucideIcons.bookOpen,
              size: 64,
              color: AppColors.brandOrange,
            ),
            const SizedBox(height: 16),
            const Text(
              '로그인 후 일기를 작성할 수 있어요',
              style: TextStyle(fontSize: 16, color: AppColors.subBrown2),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => context.go(AppRoutes.login),
              child: const Text('로그인하기'),
            ),
          ],
        ),
      ),
    );
  }
}

class _CalendarView extends ConsumerWidget {
  const _CalendarView({
    required this.focused,
    required this.selected,
    required this.onMonthChanged,
    required this.onDaySelected,
  });

  final DateTime focused;
  final DateTime? selected;
  final ValueChanged<DateTime> onMonthChanged;
  final ValueChanged<DateTime> onDaySelected;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(
      favoriteCalendarProvider((year: focused.year, month: focused.month)),
    );
    // 즐겨찾기가 아닌 날짜 셀 클릭 시 같은 날짜 다이어리 lookup 용
    final allDiaries = ref.watch(diaryListProvider);
    return Column(
      children: [
        Card(
          margin: const EdgeInsets.all(12),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
            child: TableCalendar<FavoriteCalendarItem>(
              firstDay: DateTime.utc(2020, 1, 1),
              lastDay: DateTime.utc(2030, 12, 31),
              focusedDay: focused,
              selectedDayPredicate: (day) => selected != null && isSameDay(day, selected),
              onDaySelected: (day, _) {
                onDaySelected(day);
                // 1) 즐겨찾기 셀 hit 우선
                final favList = favorites.valueOrNull?.items ?? const [];
                final favHit = favList.firstWhere(
                  (item) => isSameDay(item.date, day),
                  orElse: () => FavoriteCalendarItem(
                    date: _epoch,
                    diaryId: -1,
                    emotion: '',
                  ),
                );
                if (favHit.diaryId > 0) {
                  _openDiaryModal(context, favHit.diaryId);
                  return;
                }
                // 2) 비-즐겨찾기 셀 — 같은 날짜 다이어리 lookup (clientside filter).
                //    `diaryListProvider` = 사용자 본인 모든 다이어리 (Step 2-C).
                final all = allDiaries.valueOrNull ?? const [];
                final dayHit = all.where(
                  (d) => isSameDay(d.diaryDate, day),
                );
                if (dayHit.isNotEmpty) {
                  // 같은 날 여러 건이면 첫 번째 (목록 정렬 = created_at DESC) 우선.
                  // 다중 처리는 Step 7 폴리싱 후보 (예: 선택 시트).
                  _openDiaryModal(context, dayHit.first.id);
                  return;
                }
                // 3) 다이어리 없는 셀 — 토스트 안내
                Fluttertoast.showToast(
                  msg: '이 날짜에 작성된 일기가 없어요',
                );
              },
              onPageChanged: onMonthChanged,
              eventLoader: (day) {
                final list = favorites.valueOrNull?.items ?? const [];
                return list.where((item) => isSameDay(item.date, day)).toList();
              },
              calendarStyle: const CalendarStyle(
                outsideDaysVisible: false,
                selectedDecoration: BoxDecoration(
                  color: AppColors.brandOrange,
                  shape: BoxShape.circle,
                ),
                todayDecoration: BoxDecoration(
                  color: AppColors.peach,
                  shape: BoxShape.circle,
                ),
                todayTextStyle: TextStyle(color: AppColors.brandOrange),
              ),
              headerStyle: const HeaderStyle(
                formatButtonVisible: false,
                titleCentered: true,
              ),
              calendarBuilders: CalendarBuilders<FavoriteCalendarItem>(
                markerBuilder: (context, day, events) {
                  if (events.isEmpty) return const SizedBox.shrink();
                  return Align(
                    alignment: Alignment.bottomCenter,
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        events.first.emotion,
                        style: const TextStyle(fontSize: 14),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ),
        if (favorites.isLoading)
          const Padding(
            padding: EdgeInsets.all(16),
            child: CircularProgressIndicator(),
          ),
        if (favorites.hasError)
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              '캘린더 로드 실패: ${favorites.error}',
              style: const TextStyle(color: AppColors.destructive),
            ),
          ),
        const Expanded(child: _EmotionLegend()),
      ],
    );
  }
}

class _EmotionLegend extends StatelessWidget {
  const _EmotionLegend();

  static const _emotions = [
    ('😊', '행복'),
    ('🤣', '신남'),
    ('😌', '평온'),
    ('😪', '졸림'),
    ('🥺', '슬픔'),
    ('😡', '화남'),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Text(
            '감정 기록',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: AppColors.darkBrown,
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final e in _emotions)
                Chip(
                  label: Text('${e.$1} ${e.$2}'),
                  backgroundColor: AppColors.peach,
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _ListView extends ConsumerWidget {
  const _ListView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final list = ref.watch(diaryListProvider);
    return list.when(
      data: (diaries) {
        if (diaries.isEmpty) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                '아직 작성된 일기가 없어요.\n챗봇이나 장소 카드에서 시작해보세요.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.mutedForeground),
              ),
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(diaryListProvider);
          },
          child: GridView.builder(
            padding: const EdgeInsets.all(12),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 0.78,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
            ),
            itemCount: diaries.length,
            itemBuilder: (_, i) => DiaryCardTile(diary: diaries[i]),
          ),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '일기 목록 로드 실패: $e',
            style: const TextStyle(color: AppColors.destructive),
          ),
        ),
      ),
    );
  }
}
