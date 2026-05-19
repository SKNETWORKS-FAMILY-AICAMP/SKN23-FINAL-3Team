import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/diary.dart';
import '../auth/auth_providers.dart';
import 'diary_providers.dart';

/// 사용자 본인의 다이어리 전체 목록 — DiaryTab `_ListView` 가 watch.
/// 인증 상태 변경 시 자동 invalidate.
final diaryListProvider = FutureProvider.autoDispose<List<Diary>>((ref) async {
  final auth = ref.watch(authProvider);
  if (auth is! AuthAuthenticated) return const [];
  return ref.read(diaryApiProvider).listByUser(userId: auth.user.id);
});
