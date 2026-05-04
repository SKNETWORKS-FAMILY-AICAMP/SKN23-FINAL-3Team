import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/diary.dart';
import '../auth/auth_providers.dart';
import 'diary_api.dart';
import 'diary_list_provider.dart';

final diaryApiProvider = Provider<DiaryApi>((ref) {
  return DiaryApi(ref.watch(apiClientProvider));
});

/// 캘린더 화면용 — `(year, month)` 별 즐겨찾기 일기 셀 페이로드.
///
/// 1순위: 백엔드 `GET /api/diaries/calendar` (5/2 신규).
/// 2순위 (fallback): 배포 백엔드가 stale 하여 404/422 응답 시
/// `diaryListProvider` 의 `is_favorite=true` 항목으로 클라이언트 합성.
/// 백엔드 재배포 후 자동 1순위 경로 복귀.
final favoriteCalendarProvider = FutureProvider.autoDispose
    .family<FavoriteCalendar, ({int year, int month})>((ref, key) async {
  try {
    return await ref.read(diaryApiProvider).calendar(
          year: key.year,
          month: key.month,
        );
  } on DioException catch (e) {
    final code = e.response?.statusCode;
    if (code != 404 && code != 422) rethrow;
    // 폴백 — 같은 월의 즐겨찾기 일기를 클라이언트에서 합성
    final diaries = await ref.read(diaryListProvider.future);
    final items = diaries
        .where((d) =>
            d.isFavorite &&
            d.diaryDate.year == key.year &&
            d.diaryDate.month == key.month)
        .map((d) => FavoriteCalendarItem(
              date: d.diaryDate,
              diaryId: d.id,
              emotion: d.emotion ?? '',
            ))
        .toList();
    return FavoriteCalendar(year: key.year, month: key.month, items: items);
  }
});
