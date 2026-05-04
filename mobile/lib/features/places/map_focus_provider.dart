import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/place.dart';

/// 지도 탭 외부에서 (채팅·홈 등) "이 장소를 지도에서 보여달라" 요청 시 임시 보관.
///
/// 흐름:
/// 1. 채팅 PlaceCard 이름 탭 → `MapFocusNotifier.requestFocus(place)` + 탭 인덱스 = 2
/// 2. MapTab `didChangeDependencies` 가 watch → 1회 처리 후 `consume()` 으로 비움
/// 3. 처리 = 검색결과 list 에 이미 있으면 focusLatLng + facility modal,
///    없으면 by-name 조회로 단건 카드 부착 + focus
class MapFocusNotifier extends StateNotifier<PlaceCard?> {
  MapFocusNotifier() : super(null);

  void requestFocus(PlaceCard place) {
    state = place;
  }

  /// 1회 소비 — 처리 후 호출하여 동일 요청 반복 차단.
  PlaceCard? consume() {
    final value = state;
    state = null;
    return value;
  }
}

final mapFocusProvider =
    StateNotifierProvider<MapFocusNotifier, PlaceCard?>((ref) {
  return MapFocusNotifier();
});
