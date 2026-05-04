import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/location/location_service.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import 'map_focus_provider.dart';
import 'place_providers.dart';
import 'widgets/facility_modal_sheet.dart';
import 'widgets/kakao_map_view.dart';
import 'widgets/place_card_tile.dart';

/// 지도 탭 — 카카오맵 임베드 + 검색 + 마커 + 결과 카드 그리드.
///
/// Step 3 진입 (2026-05-04). React `MapView.tsx` 1:1.
/// - 상단 검색 입력 + 카테고리 칩
/// - 중앙 카카오맵 (`KakaoMapView`) + 결과 마커
/// - 하단 결과 그리드 (`PlaceCardTile`) — 카드 클릭 = 시설 모달 + 마커 위치 포커스
class MapTab extends ConsumerStatefulWidget {
  const MapTab({super.key});

  @override
  ConsumerState<MapTab> createState() => _MapTabState();
}

class _MapTabState extends ConsumerState<MapTab> {
  final _queryCtrl = TextEditingController();
  final _mapKey = GlobalKey<KakaoMapViewState>();

  List<PlaceCard> _results = const [];
  bool _searching = false;
  String? _searchError;

  @override
  void initState() {
    super.initState();
    // 사용자 요청 (2026-05-04 밤): 로그인 사용자의 즐겨찾기 contentId 집합을
    // 미리 로드 → 검색 결과에 즐겨찾기한 장소가 포함되면 ❤️ 채워진 상태로 표시.
    // 기존엔 옵티미스틱 토글 시점에만 set 갱신되어 검색 결과의 active 상태 부재.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final auth = ref.read(authProvider);
      if (auth is AuthAuthenticated) {
        ref.read(favoriteContentIdsProvider.notifier).reload().catchError((_) {
          // 백엔드 미응답·401 등 → 빈 set 유지 (graceful)
        });
      }
    });
  }

  @override
  void dispose() {
    _queryCtrl.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final q = _queryCtrl.text.trim();
    if (q.isEmpty) return;
    final auth = ref.read(authProvider);
    final petId = auth is AuthAuthenticated
        ? auth.user.primaryPetId ?? auth.user.primaryPet?.id
        : null;

    // GPS 좌표 자동 주입 (백엔드 미수신 시 무해 — Optional, FastAPI extra param 무시).
    // 백엔드 `/places/search` 가 lat/lng 받게 확장되면 (ops-todo §1 #25 후속)
    // 자동 동작. 현재는 query parameter 만 추가됨.
    final position = ref.read(currentPositionProvider).valueOrNull;

    setState(() {
      _searching = true;
      _searchError = null;
    });
    try {
      final results = await ref.read(placeApiProvider).search(
            query: q,
            petId: petId,
            lat: position?.latitude,
            lng: position?.longitude,
          );
      setState(() {
        _results = results;
        _searching = false;
      });
      _mapKey.currentState?.setMarkers(results);
    } catch (e) {
      setState(() {
        _searching = false;
        _searchError = '$e';
      });
      Fluttertoast.showToast(msg: '검색 실패: $e');
    }
  }

  /// 위치 권한 요청 + 현재 위치 적용 — 지도 진입 후 1회 + 사용자 명시 버튼.
  Future<void> _refreshLocation({bool silent = false}) async {
    final permission = await LocationService.ensurePermission();
    if (permission != LocationPermissionResult.granted) {
      if (!silent) {
        final msg = switch (permission) {
          LocationPermissionResult.serviceDisabled => '위치 서비스가 꺼져 있어요',
          LocationPermissionResult.denied => '위치 권한이 필요해요',
          LocationPermissionResult.deniedForever => '시스템 설정에서 위치 권한 허용 필요',
          _ => '위치 권한을 가져오지 못했어요',
        };
        Fluttertoast.showToast(msg: msg);
      }
      return;
    }
    // currentPositionProvider 무효화 + 새 위치 받기 (autoDispose 라 다음 read 시 재계산)
    ref.invalidate(currentPositionProvider);
    final position = await ref.read(currentPositionProvider.future);
    if (!mounted || position == null) return;
    _mapKey.currentState?.setCurrentLocationMarker(
      lat: position.latitude,
      lng: position.longitude,
    );
    _mapKey.currentState?.focusLatLng(
      lat: position.latitude,
      lng: position.longitude,
      level: 4,
    );
  }

  void _onMarkerTap(KakaoMarkerTap tap) {
    if (tap.name.isEmpty) return;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => FacilityModalSheet(name: tap.name),
    );
  }

  /// 카드/외부 요청으로 특정 장소를 지도에서 보여준다 (Bug #5/#6 권위 동작).
  /// 1) 좌표 있으면 마커 + focusLatLng — 결과 리스트 비어있으면 단건 자체를 입력
  /// 2) 시설정보 모달 오픈
  /// 3) `mapFocusProvider` 소비 (1회 처리)
  void _focusPlace(PlaceCard place) {
    final mapState = _mapKey.currentState;
    if (mapState != null && place.lat != 0.0 && place.lng != 0.0) {
      // 결과 리스트에 없으면 단건 마커, 있으면 전체 마커 갱신 + focus
      final inResults = _results
          .any((r) => r.contentId == place.contentId && place.contentId.isNotEmpty);
      mapState.setMarkers(inResults ? _results : [place]);
      mapState.focusLatLng(lat: place.lat, lng: place.lng, level: 4);
    }
    // 결과 리스트 갱신 — 카드 노출용 (검색 결과 없을 때 단건 표시)
    if (place.contentId.isNotEmpty &&
        !_results.any((r) => r.contentId == place.contentId)) {
      setState(() => _results = [place, ..._results]);
    }
    if (mounted && place.name.isNotEmpty) {
      showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        backgroundColor: Colors.white,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        builder: (_) => FacilityModalSheet(
          name: place.name,
          imageUrl: place.imageUrl,
        ),
      );
    }
  }

  void _consumePendingFocus() {
    final pending = ref.read(mapFocusProvider.notifier).consume();
    if (pending != null) _focusPlace(pending);
  }

  @override
  Widget build(BuildContext context) {
    // 외부 요청 (채팅 → 지도) 발생 시 1회 처리. 지도 미준비면 setMarkers/focus 는
    // 무시되지만 mapFocusProvider 가 그대로라 onMapReady 시 재시도 (consume).
    ref.listen<PlaceCard?>(mapFocusProvider, (_, next) {
      if (next == null) return;
      // 지도 ready 여부 확실치 않으니 한번 시도. 실패하면 onMapReady 가 cover.
      // 단, 여기선 consume 하지 않음 — onMapReady 가 권위.
      if (_mapKey.currentState != null) {
        // build 중 setState 금지 → 다음 프레임으로 미룸
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          _consumePendingFocus();
        });
      }
    });

    return SafeArea(
      child: Column(
        children: [
          _SearchBar(
            controller: _queryCtrl,
            onSubmit: _search,
            searching: _searching,
          ),
          // 사용자 정정 (2026-05-04 밤2): 결과 list 의 inner spinner 는
          // `_results.isEmpty` 일 때만 표시 → 후속 검색 시 누락. 검색창 아래에
          // LinearProgressIndicator 항상 박아 두 케이스 (초기·후속) 통합 커버.
          // chat_screen 의 `state.isSending` LinearProgress 와 동일 패턴.
          SizedBox(
            height: 2,
            child: _searching
                ? const LinearProgressIndicator(minHeight: 2)
                : const SizedBox.shrink(),
          ),
          SizedBox(
            height: 320,
            child: Stack(
              children: [
                KakaoMapView(
                  key: _mapKey,
                  onMarkerTap: _onMarkerTap,
                  onMapReady: (_) {
                    // 지도 init 후 GPS 자동 시도 — 권한 거부 시 silent
                    _refreshLocation(silent: true);
                    // 외부 focus 요청 보류 분 처리 (채팅 → 지도 진입 직후)
                    _consumePendingFocus();
                  },
                  onError: (msg) => Fluttertoast.showToast(msg: msg),
                ),
                Positioned(
                  right: 12,
                  bottom: 12,
                  child: FloatingActionButton.small(
                    heroTag: 'gps-refresh',
                    onPressed: () => _refreshLocation(),
                    backgroundColor: Colors.white,
                    foregroundColor: AppColors.brandOrange,
                    elevation: 2,
                    tooltip: '내 위치',
                    child: const Icon(LucideIcons.locate, size: 18),
                  ),
                ),
              ],
            ),
          ),
          Expanded(child: _ResultList(
            results: _results,
            searching: _searching,
            error: _searchError,
            onCardTap: _focusPlace,
          )),
        ],
      ),
    );
  }
}

class _SearchBar extends StatelessWidget {
  const _SearchBar({
    required this.controller,
    required this.onSubmit,
    required this.searching,
  });

  final TextEditingController controller;
  final VoidCallback onSubmit;
  final bool searching;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: TextField(
        controller: controller,
        textInputAction: TextInputAction.search,
        onSubmitted: (_) => onSubmit(),
        decoration: InputDecoration(
          hintText: '예: 강남 카페, 한강공원',
          prefixIcon: const Icon(LucideIcons.search, size: 18),
          // 사용자 요청 (2026-05-04 밤): 결과 영역에 이미 로딩바 있어 검색 버튼은
          // 항상 send 아이콘 유지. 검색 중 disabled 만 적용.
          suffixIcon: IconButton(
            icon: const Icon(LucideIcons.send, size: 18),
            onPressed: searching ? null : onSubmit,
          ),
        ),
      ),
    );
  }
}

class _ResultList extends StatelessWidget {
  const _ResultList({
    required this.results,
    required this.searching,
    required this.error,
    required this.onCardTap,
  });

  final List<PlaceCard> results;
  final bool searching;
  final String? error;
  final ValueChanged<PlaceCard> onCardTap;

  @override
  Widget build(BuildContext context) {
    if (searching && results.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '검색 실패: $error',
            style: const TextStyle(color: AppColors.destructive),
          ),
        ),
      );
    }
    if (results.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            '검색어를 입력하면 반려견 동반 가능 장소를 추천해드려요.\n예: "성수 카페", "한강공원"',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.mutedForeground, height: 1.5),
          ),
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      itemCount: results.length,
      // PlaceCardTile 의 inner InkWell 이 outer GestureDetector 보다 우선 → onNameTap
      // 으로 직접 hand-off (Bug #5 fix). 카드 tap = 지도 focus + 모달.
      itemBuilder: (_, i) => PlaceCardTile(
        place: results[i],
        onNameTap: () => onCardTap(results[i]),
      ),
    );
  }
}
