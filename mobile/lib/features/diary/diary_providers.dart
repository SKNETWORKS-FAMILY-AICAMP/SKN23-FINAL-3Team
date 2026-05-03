import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/diary.dart';
import '../auth/auth_providers.dart';
import 'diary_api.dart';

final diaryApiProvider = Provider<DiaryApi>((ref) {
  return DiaryApi(ref.watch(apiClientProvider));
});

/// 캘린더 화면용 — `(year, month)` 별 즐겨찾기 일기 셀 페이로드.
/// `is_favorite=true` 만 반환 — 모든 일기는 [[feature-favorites-diary]] 권위.
final favoriteCalendarProvider = FutureProvider.autoDispose
    .family<FavoriteCalendar, ({int year, int month})>((ref, key) async {
  return ref.read(diaryApiProvider).calendar(
        year: key.year,
        month: key.month,
      );
});
