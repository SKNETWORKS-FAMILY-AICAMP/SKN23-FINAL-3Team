import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import 'place_api.dart';

final placeApiProvider = Provider<PlaceApi>((ref) {
  return PlaceApi(ref.watch(apiClientProvider));
});

/// 즐겨찾기 content_id 집합 — 옵티미스틱 UI 의 권위 source.
/// 카드 ❤️ 토글 시 즉시 갱신, 백엔드 PATCH 실패 시 롤백.
class FavoriteContentIdsNotifier extends StateNotifier<Set<String>> {
  FavoriteContentIdsNotifier(this._ref) : super(const {});

  final Ref _ref;

  /// 백엔드에서 즐겨찾기 목록을 받아 set 초기화 (마이페이지 진입 등에서 호출).
  Future<void> reload() async {
    final api = _ref.read(placeApiProvider);
    final favorites = await api.listFavorites();
    state = favorites.map((f) => f.contentId).toSet();
  }

  /// 옵티미스틱 토글 — 먼저 set 갱신 → 백그라운드 PATCH → 실패 시 롤백.
  Future<bool> toggle(String contentId) async {
    final wasFavorite = state.contains(contentId);
    state = wasFavorite
        ? (state.toSet()..remove(contentId))
        : (state.toSet()..add(contentId));
    try {
      final api = _ref.read(placeApiProvider);
      final result = await api.toggleFavorite(contentId);
      // 백엔드 결과로 정합성 보정 (state drift 방지)
      state = result.isFavorite
          ? (state.toSet()..add(contentId))
          : (state.toSet()..remove(contentId));
      return result.isFavorite;
    } catch (_) {
      // 롤백
      state = wasFavorite
          ? (state.toSet()..add(contentId))
          : (state.toSet()..remove(contentId));
      rethrow;
    }
  }

  bool isFavorite(String contentId) => state.contains(contentId);
}

final favoriteContentIdsProvider =
    StateNotifierProvider<FavoriteContentIdsNotifier, Set<String>>((ref) {
  return FavoriteContentIdsNotifier(ref);
});

/// MyPage 즐겨찾기 장소 그리드용 — 풀 페이로드 (`PlaceFavoriteItem` 리스트).
/// `favoriteContentIdsProvider` 와 별개 — 후자는 ❤️ 토글 시 빠른 set lookup 용.
///
/// 배포 백엔드 (2026-05-04 기준 stale) 가 `/api/places/favorites` 미포함 → 404
/// 시 빈 리스트로 폴백 (UI 그레이스풀 표시). 백엔드 재배포 후 자연 동작.
final favoritePlacesProvider =
    FutureProvider.autoDispose<List<PlaceFavoriteItem>>((ref) async {
  final auth = ref.watch(authProvider);
  if (auth is! AuthAuthenticated) return const [];
  try {
    return await ref.read(placeApiProvider).listFavorites();
  } on DioException catch (e) {
    if (e.response?.statusCode == 404) return const [];
    rethrow;
  }
});
