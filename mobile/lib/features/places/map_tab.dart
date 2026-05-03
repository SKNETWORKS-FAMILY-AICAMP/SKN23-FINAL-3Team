import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/location/location_service.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
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

  static const _categories = <_Category>[
    _Category(id: '', label: '전체'),
    _Category(id: '카페', label: '카페'),
    _Category(id: '음식점', label: '음식점'),
    _Category(id: '공원', label: '공원'),
    _Category(id: '숙박', label: '숙박'),
  ];
  String _selectedCategory = '';

  List<PlaceCard> _results = const [];
  bool _searching = false;
  String? _searchError;

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
            category: _selectedCategory.isEmpty ? null : _selectedCategory,
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

  void _onCardTap(PlaceCard place) {
    if (place.lat != 0.0 && place.lng != 0.0) {
      _mapKey.currentState?.focusLatLng(lat: place.lat, lng: place.lng, level: 4);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          _SearchBar(
            controller: _queryCtrl,
            onSubmit: _search,
            searching: _searching,
          ),
          _CategoryChips(
            selected: _selectedCategory,
            onSelected: (id) {
              setState(() => _selectedCategory = id);
              if (_queryCtrl.text.trim().isNotEmpty) _search();
            },
            categories: _categories,
          ),
          SizedBox(
            height: 320,
            child: Stack(
              children: [
                KakaoMapView(
                  key: _mapKey,
                  onMarkerTap: _onMarkerTap,
                  onMapReady: (_) {
                    // 지도 init 후 GPS 자동 시도 — 권한 거부 시 silent (디폴트 좌표 유지)
                    _refreshLocation(silent: true);
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
            onCardTap: _onCardTap,
          )),
        ],
      ),
    );
  }
}

class _Category {
  const _Category({required this.id, required this.label});
  final String id;
  final String label;
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
          suffixIcon: searching
              ? const Padding(
                  padding: EdgeInsets.all(12),
                  child: SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              : IconButton(
                  icon: const Icon(LucideIcons.send, size: 18),
                  onPressed: onSubmit,
                ),
        ),
      ),
    );
  }
}

class _CategoryChips extends StatelessWidget {
  const _CategoryChips({
    required this.selected,
    required this.onSelected,
    required this.categories,
  });

  final String selected;
  final ValueChanged<String> onSelected;
  final List<_Category> categories;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12),
        children: [
          for (final c in categories)
            Padding(
              padding: const EdgeInsets.only(right: 6),
              child: ChoiceChip(
                label: Text(c.label),
                selected: c.id == selected,
                onSelected: (_) => onSelected(c.id),
                selectedColor: AppColors.peach,
              ),
            ),
        ],
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
      itemBuilder: (_, i) => GestureDetector(
        onTap: () => onCardTap(results[i]),
        behavior: HitTestBehavior.opaque,
        child: PlaceCardTile(place: results[i]),
      ),
    );
  }
}
