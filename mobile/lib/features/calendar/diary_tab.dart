import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/models/diary.dart';
import '../../shared/widgets/login_tab_view.dart';
import '../auth/auth_providers.dart';
import '../diary/diary_detail_modal_sheet.dart';
import '../diary/diary_list_provider.dart';
import '../diary/diary_providers.dart';
import '../onboarding/onboarding_providers.dart';

final DateTime _epoch = DateTime.utc(1970);

class DiaryTab extends ConsumerStatefulWidget {
  const DiaryTab({super.key});

  @override
  ConsumerState<DiaryTab> createState() => _DiaryTabState();
}

class _DiaryTabState extends ConsumerState<DiaryTab> {
  DateTime _focusedMonth = DateTime(DateTime.now().year, DateTime.now().month);
  DateTime _selectedDay = DateTime.now();

  /// 대표일기 스와이프 뷰 표시 여부.
  bool _showFavDetail = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      ref.invalidate(diaryListProvider);
      ref.invalidate(favoriteCalendarProvider);
    });
  }

  void _moveMonth(int delta) {
    setState(() {
      _focusedMonth = DateTime(
        _focusedMonth.year,
        _focusedMonth.month + delta,
      );
      _showFavDetail = false;
    });
    ref.invalidate(favoriteCalendarProvider);
  }

  void _onDaySelected(DateTime day, List<FavoriteCalendarItem> favItems) {
    final hasFav = favItems.any((item) => isSameDay(item.date, day) && item.diaryId > 0);
    setState(() {
      _selectedDay = day;
      _showFavDetail = hasFav;
    });
  }

  void _openEmotionStats(BuildContext context, List<Diary> diaries) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => _EmotionStatsPage(
          focusedMonth: _focusedMonth,
          diaries: diaries,
        ),
      ),
    );
  }

  void _openDiaryDetail(int diaryId) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => DiaryDetailModalSheet(diaryId: diaryId),
    );
  }

  Future<void> _toggleFavorite(int diaryId) async {
    try {
      await ref.read(diaryApiProvider).toggleFavorite(diaryId);
      ref.invalidate(diaryListProvider);
      ref.invalidate(favoriteCalendarProvider);
    } on DioException catch (e) {
      final detail = e.response?.data is Map
          ? (e.response!.data as Map)['detail']?.toString()
          : null;
      Fluttertoast.showToast(msg: detail ?? '즐겨찾기 토글 실패');
    } catch (e) {
      Fluttertoast.showToast(msg: '즐겨찾기 토글 실패: $e');
    }
  }

  Future<void> _deleteDiary(int diaryId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('일기 삭제'),
        content: const Text('이 일기를 정말 삭제할까요?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('취소')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('삭제', style: TextStyle(color: AppColors.destructive)),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ref.read(diaryApiProvider).delete(diaryId);
      ref.invalidate(diaryListProvider);
      ref.invalidate(favoriteCalendarProvider);
      Fluttertoast.showToast(msg: '일기가 삭제됐어요');
    } catch (e) {
      Fluttertoast.showToast(msg: '삭제 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);

    if (auth is! AuthAuthenticated) {
      return const LoginTabView(message: '로그인 후 일기를 확인할 수 있어요');
    }

    final calendarAsync = ref.watch(
      favoriteCalendarProvider(
        (year: _focusedMonth.year, month: _focusedMonth.month),
      ),
    );

    final diaryListAsync = ref.watch(diaryListProvider);
    final favItems = calendarAsync.valueOrNull?.items ?? const [];

    return Scaffold(
      backgroundColor: const Color(0xFFFFFAF3),
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.brandOrange,
          onRefresh: () async {
            ref.invalidate(diaryListProvider);
            ref.invalidate(favoriteCalendarProvider);
          },
          child: diaryListAsync.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (e, _) => _DiaryErrorView(
              message: '일기 목록을 불러오지 못했어요.\n$e',
              onRetry: () {
                ref.invalidate(diaryListProvider);
                ref.invalidate(favoriteCalendarProvider);
              },
            ),
            data: (diaries) {
              return CustomScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                slivers: [
                  // ── 헤더 ──
                  SliverToBoxAdapter(
                    child: _Header(
                      title: '일기',
                      onBack: () => Navigator.of(context).maybePop(),
                    ),
                  ),
                  // ── 월 네비게이터 ──
                  SliverToBoxAdapter(
                    child: _MonthNavigator(
                      focusedMonth: _focusedMonth,
                      onPrev: () => _moveMonth(-1),
                      onNext: () => _moveMonth(1),
                      onStats: () => _openEmotionStats(context, diaries),
                    ),
                  ),
                  // ── 캘린더 ──
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
                      child: _CalendarCard(
                        focusedMonth: _focusedMonth,
                        selectedDay: _selectedDay,
                        calendarAsync: calendarAsync,
                        onPageChanged: (day) {
                          setState(() {
                            _focusedMonth = DateTime(day.year, day.month);
                            _showFavDetail = false;
                          });
                        },
                        onDaySelected: (day) => _onDaySelected(day, favItems),
                      ),
                    ),
                  ),
                  // ── 대표 그림일기 스와이프 뷰 ──
                  if (_showFavDetail)
                    SliverToBoxAdapter(
                      child: _FavoriteDiarySwiper(
                        selectedDay: _selectedDay,
                        favItems: favItems,
                        onTapDetail: _openDiaryDetail,
                        onClose: () => setState(() => _showFavDetail = false),
                      ),
                    ),
                  // ── 일기 목록 상단 여백 ──
                  const SliverToBoxAdapter(
                    child: SizedBox(height: 20),
                  ),
                  // ── 날짜별 그림일기 그리드 ──
                  if (diaries.isEmpty)
                    const SliverToBoxAdapter(
                      child: _EmptyGalleryCard(),
                    )
                  else
                    ..._buildDateGroupedGallery(diaries),
                  const SliverToBoxAdapter(child: SizedBox(height: 104)),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  /// 날짜별로 그룹핑 → 날짜 헤더 + 이미지 그리드 반복.
  List<Widget> _buildDateGroupedGallery(List<Diary> diaries) {
    // 날짜 내림차순 정렬 (최신 날짜 먼저), 같은 날짜 안에서는 최신 생성순
    final sorted = List<Diary>.from(diaries)
      ..sort((a, b) {
        final dateCmp = b.diaryDate.compareTo(a.diaryDate);
        if (dateCmp != 0) return dateCmp;
        return b.createdAt.compareTo(a.createdAt);
      });

    // 날짜별 그룹핑 (LinkedHashMap 순서 보존)
    final groups = <String, List<Diary>>{};
    for (final d in sorted) {
      final key = _formatDateKey(d.diaryDate);
      groups.putIfAbsent(key, () => []).add(d);
    }

    final slivers = <Widget>[];
    for (final entry in groups.entries) {
      final groupCount = entry.value.length;
      // 날짜 헤더 + 해당 날짜의 일기 개수
      slivers.add(
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 16, 24, 8),
            child: Row(
              children: [
                Text(
                  entry.key,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.subBrown2,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Container(
                    margin: const EdgeInsets.only(top: 2),
                    height: 1,
                    color: const Color(0xFFE8D5C0),
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFEFE3),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    '$groupCount개',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppColors.brandOrange,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
      // 이미지 그리드 (3열)
      slivers.add(
        SliverPadding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          sliver: SliverGrid(
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: 0.75,
            ),
            delegate: SliverChildBuilderDelegate(
              (_, index) {
                final diary = entry.value[index];
                return _GalleryTile(
                  diary: diary,
                  onTap: () => _openDiaryDetail(diary.id),
                  onToggleFavorite: () => _toggleFavorite(diary.id),
                  onDelete: () => _deleteDiary(diary.id),
                );
              },
              childCount: entry.value.length,
            ),
          ),
        ),
      );
    }
    return slivers;
  }

  static String _formatDateKey(DateTime d) {
    const weekdays = ['월', '화', '수', '목', '금', '토', '일'];
    return '${d.year}년 ${d.month}월 ${d.day}일 (${weekdays[d.weekday - 1]})';
  }
}

// ── 헤더 ─────────────────────────────────────────────────────────────────────
class _Header extends StatelessWidget {
  const _Header({required this.title, required this.onBack});

  final String title;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: const BoxDecoration(
        color: Color(0xFFFFFAF3),
        border: Border(
          bottom: BorderSide(color: Color(0xFFF3E4D3), width: 0.8),
        ),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: onBack,
            icon: const Icon(LucideIcons.chevronLeft, color: AppColors.darkBrown),
          ),
          Expanded(
            child: Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.w800,
                color: AppColors.darkBrown,
              ),
            ),
          ),
          const SizedBox(width: 48), // 좌우 균형
        ],
      ),
    );
  }
}

// ── 월 네비게이터 ────────────────────────────────────────────────────────────
class _MonthNavigator extends StatelessWidget {
  const _MonthNavigator({
    required this.focusedMonth,
    required this.onPrev,
    required this.onNext,
    required this.onStats,
  });

  final DateTime focusedMonth;
  final VoidCallback onPrev;
  final VoidCallback onNext;
  final VoidCallback onStats;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 8),
      child: Row(
        children: [
          _RoundIconButton(icon: LucideIcons.chevronLeft, onTap: onPrev),
          Expanded(
            child: Text(
              '${focusedMonth.year}년 ${focusedMonth.month}월',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: AppColors.darkBrown,
              ),
            ),
          ),
          _RoundIconButton(icon: LucideIcons.chevronRight, onTap: onNext),
          const SizedBox(width: 6),
          _RoundIconButton(icon: LucideIcons.barChart2, onTap: onStats),
        ],
      ),
    );
  }
}

class _RoundIconButton extends StatelessWidget {
  const _RoundIconButton({required this.icon, required this.onTap});

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      shape: const CircleBorder(),
      elevation: 0,
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: SizedBox(
          width: 38,
          height: 38,
          child: Icon(icon, size: 20, color: AppColors.darkBrown),
        ),
      ),
    );
  }
}

// ── 캘린더 카드 ──────────────────────────────────────────────────────────────
class _CalendarCard extends StatelessWidget {
  const _CalendarCard({
    required this.focusedMonth,
    required this.selectedDay,
    required this.calendarAsync,
    required this.onPageChanged,
    required this.onDaySelected,
  });

  final DateTime focusedMonth;
  final DateTime selectedDay;
  final AsyncValue<FavoriteCalendar> calendarAsync;
  final ValueChanged<DateTime> onPageChanged;
  final ValueChanged<DateTime> onDaySelected;

  @override
  Widget build(BuildContext context) {
    final favoriteItems = calendarAsync.valueOrNull?.items ?? const [];

    return Container(
      padding: const EdgeInsets.fromLTRB(8, 10, 8, 14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: const Color(0xFFF1DEC8)),
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: Colors.brown.withValues(alpha: 0.06),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Stack(
        children: [
          TableCalendar<FavoriteCalendarItem>(
            locale: 'ko_KR',
            firstDay: DateTime.utc(2020, 1, 1),
            lastDay: DateTime.utc(2030, 12, 31),
            focusedDay: focusedMonth,
            selectedDayPredicate: (day) => isSameDay(day, selectedDay),
            onDaySelected: (selected, focused) {
              onDaySelected(selected);
              if (focused.year != focusedMonth.year ||
                  focused.month != focusedMonth.month) {
                onPageChanged(focused);
              }
            },
            onPageChanged: onPageChanged,
            eventLoader: (day) {
              final hit = favoriteItems.firstWhere(
                (item) => isSameDay(item.date, day),
                orElse: () => FavoriteCalendarItem(
                  date: _epoch,
                  diaryId: -1,
                  emotion: '',
                ),
              );
              if (hit.diaryId <= 0) return const <FavoriteCalendarItem>[];
              return [hit];
            },
            rowHeight: 72,
            daysOfWeekHeight: 34,
            headerVisible: false,
            sixWeekMonthsEnforced: false,
            calendarStyle: CalendarStyle(
              outsideDaysVisible: false,
              isTodayHighlighted: true,
              cellMargin: const EdgeInsets.all(0),
              markersMaxCount: 0,
              // 커스텀 빌더 사용하지만, 폴백 시 circle+borderRadius 충돌 방지
              selectedDecoration: BoxDecoration(
                color: AppColors.brandOrange,
                borderRadius: BorderRadius.circular(14),
              ),
              todayDecoration: BoxDecoration(
                color: Colors.transparent,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppColors.brandOrange, width: 2),
              ),
              defaultDecoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
              ),
              weekendDecoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
              ),
              outsideDecoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
              ),
              disabledDecoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
              ),
              markerDecoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
              ),
              rangeStartDecoration: BoxDecoration(
                color: AppColors.brandOrange,
                borderRadius: BorderRadius.circular(14),
              ),
              rangeEndDecoration: BoxDecoration(
                color: AppColors.brandOrange,
                borderRadius: BorderRadius.circular(14),
              ),
            ),
            daysOfWeekStyle: const DaysOfWeekStyle(
              weekdayStyle: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: AppColors.subBrown2,
              ),
              weekendStyle: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: AppColors.subBrown2,
              ),
            ),
            calendarBuilders: CalendarBuilders<FavoriteCalendarItem>(
              dowBuilder: (context, day) {
                final labels = ['일', '월', '화', '수', '목', '금', '토'];
                final text = labels[day.weekday % 7];
                final color = day.weekday == DateTime.sunday
                    ? const Color(0xFFFF4B2B)
                    : day.weekday == DateTime.saturday
                        ? const Color(0xFF2288FF)
                        : AppColors.subBrown2;
                return Center(
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: color,
                    ),
                  ),
                );
              },
              defaultBuilder: (context, day, focusedDay) {
                final events = favoriteItems.where((e) => isSameDay(e.date, day)).toList();
                return _DayCell(
                  day: day,
                  textColor: AppColors.darkBrown,
                  bgColor: const Color(0xFFFFFCF8),
                  events: events,
                );
              },
              selectedBuilder: (context, day, focusedDay) {
                final events = favoriteItems.where((e) => isSameDay(e.date, day)).toList();
                return _DayCell(
                  day: day,
                  textColor: Colors.white,
                  bgColor: AppColors.brandOrange,
                  events: events,
                );
              },
              todayBuilder: (context, day, focusedDay) {
                final events = favoriteItems.where((e) => isSameDay(e.date, day)).toList();
                return _DayCell(
                  day: day,
                  textColor: AppColors.brandOrange,
                  bgColor: Colors.transparent,
                  borderColor: AppColors.brandOrange,
                  events: events,
                );
              },
              outsideBuilder: (context, day, focusedDay) =>
                  const SizedBox.shrink(),
            ),
          ),
          if (calendarAsync.isLoading)
            Positioned.fill(
              child: IgnorePointer(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.45),
                    borderRadius: BorderRadius.circular(24),
                  ),
                  alignment: Alignment.center,
                  child: const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

}

// ── 커스텀 날짜 셀 (숫자 좌상단 + 이모지 중앙) ─────────────────────────────────
class _DayCell extends StatelessWidget {
  const _DayCell({
    required this.day,
    required this.textColor,
    required this.bgColor,
    this.borderColor,
    this.events = const [],
  });

  final DateTime day;
  final Color textColor;
  final Color bgColor;
  final Color? borderColor;
  final List<FavoriteCalendarItem> events;

  @override
  Widget build(BuildContext context) {
    final emotion = events.isNotEmpty ? events.first.emotion.trim() : '';
    final emoji = emotion.isNotEmpty ? _normalizeEmotionEmoji(emotion) : null;

    return Container(
      margin: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(14),
        border: borderColor != null
            ? Border.all(color: borderColor!, width: 2)
            : null,
      ),
      child: Stack(
        children: [
          // 날짜 숫자 — 좌상단
          Positioned(
            top: 6,
            left: 8,
            child: Text(
              '${day.day}',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: textColor,
              ),
            ),
          ),
          // 이모지 — 중앙 하단
          if (emoji != null)
            Positioned(
              left: 0,
              right: 0,
              bottom: 4,
              child: Center(
                child: Text(
                  emoji,
                  style: const TextStyle(fontSize: 24),
                ),
              ),
            ),
        ],
      ),
    );
  }

  static String _normalizeEmotionEmoji(String value) {
    if (value.runes.length <= 2 && value.contains(RegExp(r'[^\w\s가-힣]'))) {
      return value;
    }
    switch (value) {
      case '행복':
      case '기쁨':
      case '좋음':
        return '😊';
      case '신남':
      case '즐거움':
        return '😄';
      case '평온':
      case '차분':
        return '😌';
      case '졸림':
      case '피곤':
        return '😪';
      case '슬픔':
      case '우울':
        return '🥺';
      case '화남':
      case '분노':
        return '😡';
      default:
        return value;
    }
  }
}

// ── 대표 일기 스와이프 뷰 ───────────────────────────────────────────────────
class _FavoriteDiarySwiper extends ConsumerWidget {
  const _FavoriteDiarySwiper({
    required this.selectedDay,
    required this.favItems,
    required this.onTapDetail,
    required this.onClose,
  });

  final DateTime selectedDay;
  final List<FavoriteCalendarItem> favItems;
  final ValueChanged<int> onTapDetail;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // 선택 날짜의 즐겨찾기 아이템들
    final dayItems = favItems
        .where((item) => isSameDay(item.date, selectedDay) && item.diaryId > 0)
        .toList();

    if (dayItems.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(LucideIcons.star, size: 16, color: AppColors.brandOrange),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  '${selectedDay.month}월 ${selectedDay.day}일 대표 그림일기',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppColors.darkBrown,
                  ),
                ),
              ),
              GestureDetector(
                onTap: onClose,
                child: const Icon(LucideIcons.x, size: 18, color: AppColors.subBrown2),
              ),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: 320,
            child: PageView.builder(
              itemCount: dayItems.length,
              controller: PageController(viewportFraction: 0.92),
              itemBuilder: (_, index) {
                final item = dayItems[index];
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: _FavoriteDiaryCard(
                    diaryId: item.diaryId,
                    emotion: item.emotion,
                    onTap: () => onTapDetail(item.diaryId),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// 대표 일기 카드 — 이미지 + 제목 + 내용 미리보기.
class _FavoriteDiaryCard extends ConsumerStatefulWidget {
  const _FavoriteDiaryCard({
    required this.diaryId,
    required this.emotion,
    required this.onTap,
  });

  final int diaryId;
  final String emotion;
  final VoidCallback onTap;

  @override
  ConsumerState<_FavoriteDiaryCard> createState() => _FavoriteDiaryCardState();
}

class _FavoriteDiaryCardState extends ConsumerState<_FavoriteDiaryCard> {
  late Future<Diary> _future;

  @override
  void initState() {
    super.initState();
    _future = ref.read(diaryApiProvider).get(widget.diaryId);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Diary>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFF1DEC8)),
            ),
            alignment: Alignment.center,
            child: const CircularProgressIndicator(strokeWidth: 2),
          );
        }
        if (snapshot.hasError || !snapshot.hasData) {
          return Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFF1DEC8)),
            ),
            alignment: Alignment.center,
            child: const Text('불러오기 실패', style: TextStyle(color: AppColors.subBrown2)),
          );
        }
        final diary = snapshot.data!;
        return GestureDetector(
          onTap: widget.onTap,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFF1DEC8)),
              boxShadow: [
                BoxShadow(
                  color: Colors.brown.withValues(alpha: 0.06),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 이미지
                Expanded(
                  child: ClipRRect(
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                    child: SizedBox(
                      width: double.infinity,
                      child: diary.imageId != null
                          ? _NetworkDiaryImage(
                              imageId: diary.imageId!,
                              fallbackEmoji: diary.emotion ?? '🐾',
                            )
                          : _EmojiPlaceholder(emoji: diary.emotion ?? '🐾'),
                    ),
                  ),
                ),
                // 제목 + 내용
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          if (widget.emotion.isNotEmpty) ...[
                            Text(widget.emotion, style: const TextStyle(fontSize: 18)),
                            const SizedBox(width: 6),
                          ],
                          Expanded(
                            child: Text(
                              diary.title ?? '오늘의 일기',
                              style: GoogleFonts.gaegu(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.darkBrown,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                      if (diary.content?.isNotEmpty == true) ...[
                        const SizedBox(height: 4),
                        Text(
                          diary.content!,
                          style: GoogleFonts.gaegu(
                            fontSize: 13,
                            color: AppColors.subBrown2,
                            height: 1.4,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ],
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

// ── 갤러리 타일 (3열 그리드) ─────────────────────────────────────────────────
class _GalleryTile extends ConsumerWidget {
  const _GalleryTile({
    required this.diary,
    required this.onTap,
    required this.onToggleFavorite,
    required this.onDelete,
  });

  final Diary diary;
  final VoidCallback onTap;
  final VoidCallback onToggleFavorite;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.beige),
          boxShadow: [
            BoxShadow(
              color: Colors.brown.withValues(alpha: 0.04),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          children: [
            // 이미지 영역
            Expanded(
              child: Stack(
                fit: StackFit.expand,
                children: [
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(14)),
                    child: diary.imageId != null
                        ? _NetworkDiaryImage(
                            imageId: diary.imageId!,
                            fallbackEmoji: diary.emotion ?? '🐾',
                          )
                        : _EmojiPlaceholder(emoji: diary.emotion ?? '🐾'),
                  ),
                  // 즐겨찾기 + 삭제 오버레이
                  Positioned(
                    top: 4,
                    left: 4,
                    child: _SmallIconButton(
                      icon: diary.isFavorite ? Icons.star : Icons.star_border,
                      color: Colors.white,
                      onTap: onToggleFavorite,
                    ),
                  ),
                  Positioned(
                    top: 4,
                    right: 4,
                    child: _SmallIconButton(
                      icon: LucideIcons.trash2,
                      color: Colors.white.withValues(alpha: 0.8),
                      onTap: onDelete,
                    ),
                  ),
                ],
              ),
            ),
            // 제목
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
              child: Text(
                diary.title ?? '일기',
                style: GoogleFonts.gaegu(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: AppColors.darkBrown,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SmallIconButton extends StatelessWidget {
  const _SmallIconButton({
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.black.withValues(alpha: 0.3),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: onTap,
        child: SizedBox(
          width: 36,
          height: 36,
          child: Icon(icon, size: 18, color: color),
        ),
      ),
    );
  }
}

// ── 이미지 로딩 위젯 ─────────────────────────────────────────────────────────
class _NetworkDiaryImage extends ConsumerWidget {
  const _NetworkDiaryImage({required this.imageId, required this.fallbackEmoji});

  final int imageId;
  final String fallbackEmoji;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final urlAsync = ref.watch(diaryImageUrlProvider(imageId));
    return urlAsync.when(
      data: (url) {
        if (url == null || url.isEmpty) {
          return _EmojiPlaceholder(emoji: fallbackEmoji);
        }
        return Image.network(
          url,
          fit: BoxFit.cover,
          errorBuilder: (_, e, st) => _EmojiPlaceholder(emoji: fallbackEmoji),
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
      error: (e, st) => _EmojiPlaceholder(emoji: fallbackEmoji),
    );
  }
}

class _EmojiPlaceholder extends StatelessWidget {
  const _EmojiPlaceholder({required this.emoji});

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

// ── 빈 갤러리 카드 ───────────────────────────────────────────────────────────
class _EmptyGalleryCard extends StatelessWidget {
  const _EmptyGalleryCard();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 28),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: const Color(0xFFF1DEC8)),
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: Colors.brown.withValues(alpha: 0.05),
              blurRadius: 18,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: const Column(
          children: [
            Text('🐾', style: TextStyle(fontSize: 36)),
            SizedBox(height: 14),
            Text(
              '아직 그림일기가 없어요',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: AppColors.darkBrown,
              ),
            ),
            SizedBox(height: 6),
            Text(
              '챗봇에서 그림일기를 만들어보세요!',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: AppColors.subBrown2,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 에러 뷰 ──────────────────────────────────────────────────────────────────
class _DiaryErrorView extends StatelessWidget {
  const _DiaryErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(LucideIcons.alertCircle, color: AppColors.destructive, size: 32),
            const SizedBox(height: 12),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.subBrown2, height: 1.5),
            ),
            const SizedBox(height: 18),
            FilledButton(onPressed: onRetry, child: const Text('다시 불러오기')),
          ],
        ),
      ),
    );
  }
}

// ── 월별 감정 통계 전체 화면 ──────────────────────────────────────────────────
class _EmotionStatsPage extends StatefulWidget {
  const _EmotionStatsPage({
    required this.focusedMonth,
    required this.diaries,
  });

  final DateTime focusedMonth;
  final List<Diary> diaries;

  @override
  State<_EmotionStatsPage> createState() => _EmotionStatsPageState();
}

class _EmotionStatsPageState extends State<_EmotionStatsPage> {
  String? _selectedEmoji;

  @override
  Widget build(BuildContext context) {
    final focusedMonth = widget.focusedMonth;
    // 해당 월의 일기만 필터
    final monthDiaries = widget.diaries.where((d) =>
        d.diaryDate.year == focusedMonth.year &&
        d.diaryDate.month == focusedMonth.month).toList();

    // 감정별 카운트 집계
    final emotionCounts = <String, int>{};
    for (final d in monthDiaries) {
      if (d.emotion == null || d.emotion!.trim().isEmpty) continue;
      final emoji = _normalizeStatsEmoji(d.emotion!);
      emotionCounts[emoji] = (emotionCounts[emoji] ?? 0) + 1;
    }

    // 내림차순 정렬
    final sorted = emotionCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final totalWithEmotion = sorted.fold<int>(0, (sum, e) => sum + e.value);
    final topEmoji = sorted.isNotEmpty ? sorted.first.key : null;

    // 연속 기록 계산 (해당 월 기준)
    final streakDays = _calcStreak(monthDiaries);

    // 선택된 이모지에 해당하는 일기 필터
    final filteredDiaries = _selectedEmoji == null
        ? <Diary>[]
        : monthDiaries.where((d) {
            if (d.emotion == null) return false;
            return _normalizeStatsEmoji(d.emotion!) == _selectedEmoji;
          }).toList()
      ..sort((a, b) => b.diaryDate.compareTo(a.diaryDate));

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(LucideIcons.arrowLeft, color: AppColors.darkBrown),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(LucideIcons.barChart2,
                size: 18, color: AppColors.brandOrange),
            const SizedBox(width: 6),
            Text(
              '${focusedMonth.year}년 ${focusedMonth.month}월 감정 통계',
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: AppColors.darkBrown,
              ),
            ),
          ],
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          children: [
            // 요약 — 총 일기 / 연속 기록
            Row(
              children: [
                _StatsBadge(
                  icon: LucideIcons.bookOpen,
                  label: '총 일기',
                  value: '${monthDiaries.length}편',
                ),
                const SizedBox(width: 10),
                _StatsBadge(
                  icon: LucideIcons.flame,
                  label: '연속 기록',
                  value: '$streakDays일',
                ),
              ],
            ),
            const SizedBox(height: 20),
            // 가장 많은 감정 하이라이트
            if (topEmoji != null) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                    vertical: 16, horizontal: 20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFFF5EE), Color(0xFFFFE8D6)],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AppColors.brandOrange.withValues(alpha: 0.25),
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(topEmoji, style: const TextStyle(fontSize: 36)),
                    const SizedBox(width: 14),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '이번 달 가장 많은 감정',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppColors.subBrown2,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${sorted.first.value}편 (${totalWithEmotion > 0 ? (sorted.first.value / totalWithEmotion * 100).round() : 0}%)',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                            color: AppColors.brandOrange,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
            ],
            // 세로 바 차트 (센터)
            if (sorted.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 60),
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('🐾', style: TextStyle(fontSize: 36)),
                      const SizedBox(height: 12),
                      Text(
                        '${focusedMonth.month}월에 기록된 감정이 없어요',
                        style: const TextStyle(
                          fontSize: 14,
                          color: AppColors.subBrown2,
                        ),
                      ),
                    ],
                  ),
                ),
              )
            else
              Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 400),
                  child: SizedBox(
                    height: 280,
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        // 표시할 최대 감정 수를 화면 너비에 맞게 제한
                        // 각 바 최소 폭 28px + 간격 8px 기준
                        final maxBars = ((constraints.maxWidth + 8) / 36)
                            .floor()
                            .clamp(1, sorted.length);
                        final displayItems = sorted.take(maxBars).toList();
                        final displayMax = displayItems.isNotEmpty
                            ? displayItems.first.value
                            : 1;
                        return Row(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            for (int i = 0; i < displayItems.length; i++) ...[
                              if (i > 0) const SizedBox(width: 8),
                              Expanded(
                                child: _EmotionBarColumn(
                                  emoji: displayItems[i].key,
                                  count: displayItems[i].value,
                                  ratio: displayItems[i].value / displayMax,
                                  percentage: totalWithEmotion > 0
                                      ? (displayItems[i].value /
                                              totalWithEmotion *
                                              100)
                                          .round()
                                      : 0,
                                  rank: i,
                                  isSelected:
                                      displayItems[i].key == _selectedEmoji,
                                  onTap: () {
                                    setState(() {
                                      _selectedEmoji =
                                          _selectedEmoji == displayItems[i].key
                                              ? null
                                              : displayItems[i].key;
                                    });
                                  },
                                ),
                              ),
                            ],
                          ],
                        );
                      },
                    ),
                  ),
                ),
              ),
            // 이모지 안내 텍스트 — 선택 전에만 표시
            if (_selectedEmoji == null && sorted.isNotEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 14),
                child: Center(
                  child: Text(
                    '이모지를 누르면 해당하는 일기가 나와요!',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.subBrown2,
                    ),
                  ),
                ),
              ),
            // 선택된 감정의 일기 목록
            if (_selectedEmoji != null && filteredDiaries.isNotEmpty) ...[
              const SizedBox(height: 20),
              const Divider(color: Color(0xFFF3E4D3)),
              const SizedBox(height: 12),
              Row(
                children: [
                  Text(
                    _selectedEmoji!,
                    style: const TextStyle(fontSize: 20),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '감정 일기 ${filteredDiaries.length}편',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: AppColors.darkBrown,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => setState(() => _selectedEmoji = null),
                    child: const Icon(LucideIcons.x,
                        size: 18, color: AppColors.mutedForeground),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              for (final diary in filteredDiaries)
                _EmotionDiaryTile(
                  diary: diary,
                  onTap: () {
                    showModalBottomSheet<void>(
                      context: context,
                      isScrollControlled: true,
                      backgroundColor: Colors.transparent,
                      builder: (_) =>
                          DiaryDetailModalSheet(diaryId: diary.id),
                    );
                  },
                ),
            ],
          ],
        ),
      ),
    );
  }

  static String _normalizeStatsEmoji(String value) {
    if (value.runes.length <= 2 &&
        value.contains(RegExp(r'[^\w\s가-힣]'))) {
      return value;
    }
    switch (value) {
      case '행복':
      case '기쁨':
      case '좋음':
        return '😊';
      case '신남':
      case '즐거움':
        return '😄';
      case '평온':
      case '차분':
        return '😌';
      case '졸림':
      case '피곤':
        return '😪';
      case '슬픔':
      case '우울':
        return '🥺';
      case '화남':
      case '분노':
        return '😡';
      default:
        return value;
    }
  }

  /// 해당 월 최대 연속 기록 일수 계산.
  static int _calcStreak(List<Diary> monthDiaries) {
    if (monthDiaries.isEmpty) return 0;
    final dates = monthDiaries
        .map((d) => DateTime(d.diaryDate.year, d.diaryDate.month, d.diaryDate.day))
        .toSet()
        .toList()
      ..sort();
    int maxStreak = 1;
    int current = 1;
    for (int i = 1; i < dates.length; i++) {
      if (dates[i].difference(dates[i - 1]).inDays == 1) {
        current++;
        if (current > maxStreak) maxStreak = current;
      } else {
        current = 1;
      }
    }
    return maxStreak;
  }
}

/// 감정 통계에서 선택된 감정의 일기 타일.
class _EmotionDiaryTile extends StatelessWidget {
  const _EmotionDiaryTile({required this.diary, required this.onTap});

  final Diary diary;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final dateStr =
        '${diary.diaryDate.month}/${diary.diaryDate.day}';
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF8F3),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFF3E4D3)),
        ),
        child: Row(
          children: [
            // 감정 이모지
            Text(
              diary.emotion ?? '',
              style: const TextStyle(fontSize: 24),
            ),
            const SizedBox(width: 12),
            // 제목 + 날짜
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    diary.title ?? '제목 없음',
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.darkBrown,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    dateStr,
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.mutedForeground,
                    ),
                  ),
                ],
              ),
            ),
            // 즐겨찾기
            if (diary.isFavorite)
              const Icon(LucideIcons.star,
                  size: 14, color: AppColors.brandOrange),
            const SizedBox(width: 4),
            const Icon(LucideIcons.chevronRight,
                size: 16, color: AppColors.mutedForeground),
          ],
        ),
      ),
    );
  }
}

class _StatsBadge extends StatelessWidget {
  const _StatsBadge({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF8F3),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFFFE8D6)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 20, color: AppColors.brandOrange),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppColors.brandOrange,
                  ),
                ),
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 10,
                    color: AppColors.subBrown2,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _EmotionBarColumn extends StatelessWidget {
  const _EmotionBarColumn({
    required this.emoji,
    required this.count,
    required this.ratio,
    required this.percentage,
    required this.rank,
    this.isSelected = false,
    this.onTap,
  });

  final String emoji;
  final int count;
  final double ratio;
  final int percentage;
  final int rank;
  final bool isSelected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final barColor = isSelected
        ? AppColors.brandOrange
        : rank == 0
            ? AppColors.brandOrange
            : rank == 1
                ? const Color(0xFFFFB088)
                : rank == 2
                    ? const Color(0xFFFFD2B8)
                    : AppColors.beige;

    const maxBarHeight = 160.0;
    const barWidth = 20.0;

    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          // 수치
          Text(
            '$percentage%',
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: AppColors.subBrown2,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '$count편',
            style: const TextStyle(
              fontSize: 9,
              color: AppColors.mutedForeground,
            ),
          ),
          const SizedBox(height: 6),
          // 세로 바 — 얇게
          Center(
            child: SizedBox(
              width: barWidth,
              height: maxBarHeight,
              child: Stack(
                alignment: Alignment.bottomCenter,
                children: [
                  // 배경
                  Container(
                    width: barWidth,
                    height: maxBarHeight,
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF3EB),
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  // 채움
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 400),
                    curve: Curves.easeOutCubic,
                    width: barWidth,
                    height: maxBarHeight * ratio.clamp(0.06, 1.0),
                    decoration: BoxDecoration(
                      color: barColor,
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          // 이모지 — 선택 시 강조
          Container(
            padding: const EdgeInsets.all(4),
            decoration: isSelected
                ? BoxDecoration(
                    color: AppColors.peach,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: AppColors.brandOrange.withValues(alpha: 0.5),
                    ),
                  )
                : null,
            child: Text(
              emoji,
              style: const TextStyle(fontSize: 22),
              textAlign: TextAlign.center,
              overflow: TextOverflow.clip,
              maxLines: 1,
            ),
          ),
        ],
      ),
    );
  }
}
