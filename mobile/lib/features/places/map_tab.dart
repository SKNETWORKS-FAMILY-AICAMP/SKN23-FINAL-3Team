import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/api/dio_error_format.dart';
import '../../core/directions/directions_api.dart';
import '../../core/directions/directions_service.dart';
import '../../core/location/location_service.dart';
import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import '../../shared/widgets/login_tab_view.dart';
import '../auth/auth_providers.dart';
import '../chat/chat_providers.dart';
import '../home/home_tab_index.dart';
import 'map_focus_provider.dart';
import 'place_providers.dart';
import 'widgets/kakao_map_view.dart';

// ── 카테고리 칩 데이터 ────────────────────────────────────────────────────────

class _Category {
  const _Category(this.label, this.emoji, this.query);
  final String label;
  final String emoji;
  final String query;
}

const _kCategories = [
  _Category('식당', '🍽️', '반려견 동반 식당'),
  _Category('카페', '☕', '반려견 동반 카페'),
  _Category('공원', '🌳', '반려견 공원'),
  _Category('동물병원', '🏥', '동물병원'),
  _Category('산책', '🐾', '반려견 산책로'),
  _Category('미술관', '🎨', '반려견 동반 미술관'),
];

// ── 거리 계산 헬퍼 ──────────────────────────────────────────────────────────

double _haversineKm(double lat1, double lng1, double lat2, double lng2) {
  const r = 6371.0;
  final dLat = _toRad(lat2 - lat1);
  final dLng = _toRad(lng2 - lng1);
  final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
      math.cos(_toRad(lat1)) *
          math.cos(_toRad(lat2)) *
          math.sin(dLng / 2) *
          math.sin(dLng / 2);
  return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
}

double _toRad(double deg) => deg * math.pi / 180;

String _formatDistance(double km) {
  if (km < 1) return '${(km * 1000).round()}m';
  return '${km.toStringAsFixed(1)}km';
}

// ── 시트 상태 ─────────────────────────────────────────────────────────────────

enum _SheetState { favorites, results, detail }

// ── MapTab ────────────────────────────────────────────────────────────────────

/// 지도 탭 — 전체화면 카카오맵 + 플로팅 검색창·카테고리 칩 + 하단 드래거블 시트.
///
/// 시트 3-state: [즐겨찾기 장소] → [검색 결과 목록] → [장소 상세].
class MapTab extends ConsumerStatefulWidget {
  const MapTab({super.key});

  @override
  ConsumerState<MapTab> createState() => _MapTabState();
}

class _MapTabState extends ConsumerState<MapTab> {
  final _queryCtrl = TextEditingController();
  final _mapKey = GlobalKey<KakaoMapViewState>();
  final _sheetController = DraggableScrollableController();

  List<PlaceCard> _results = const [];
  bool _searching = false;
  String? _searchError;
  _SheetState _sheetState = _SheetState.favorites;
  PlaceCard? _detailPlace;

  /// WebView JS 로드 완료 여부 — true 일 때만 setMarkers/focusLatLng 동작.
  bool _mapReady = false;

  /// 선택된 카테고리 칩 인덱스 (null = 없음).
  int? _selectedCategoryIndex;

  /// 경로 조회 결과 (polyline + 요약).
  DirectionsRouteResponse? _routeResult;
  bool _routeLoading = false;

  /// 내 주변 장소 모드 — [내 위치] 버튼으로 검색 시 true.
  bool _nearbyMode = false;
  double? _userLat;
  double? _userLng;

  static const double _sheetMinSize = 0.14;
  static const double _sheetInitSize = 0.36;
  static const double _sheetMaxSize = 0.88;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final auth = ref.read(authProvider);
      if (auth is AuthAuthenticated) {
        ref
            .read(favoriteContentIdsProvider.notifier)
            .reload()
            .catchError((_) {});
      }
    });
  }

  @override
  void dispose() {
    _queryCtrl.dispose();
    _sheetController.dispose();
    super.dispose();
  }

  Future<void> _search({String? overrideQuery, int? categoryIndex}) async {
    final q = (overrideQuery ?? _queryCtrl.text).trim();
    if (q.isEmpty) return;
    if (overrideQuery != null) _queryCtrl.text = overrideQuery;
    setState(() => _selectedCategoryIndex = categoryIndex);

    final auth = ref.read(authProvider);
    final petId = auth is AuthAuthenticated
        ? auth.user.primaryPetId ?? auth.user.primaryPet?.id
        : null;
    final position = ref.read(currentPositionProvider).valueOrNull;

    setState(() {
      _searching = true;
      _searchError = null;
      _sheetState = _SheetState.results;
      _nearbyMode = false;
    });

    if (_sheetController.isAttached) {
      _sheetController.animateTo(
        _sheetInitSize,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }

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
      final msg = formatDioError(e, '검색 실패');
      setState(() {
        _searching = false;
        _searchError = msg;
      });
      Fluttertoast.showToast(msg: msg);
    }
  }

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
    ref.invalidate(currentPositionProvider);
    final position = await ref.read(currentPositionProvider.future);
    if (!mounted || position == null) {
      if (!silent) Fluttertoast.showToast(msg: '현재 위치를 가져오지 못했어요');
      return;
    }

    final lat = position.latitude;
    final lng = position.longitude;

    _mapKey.currentState?.setCurrentLocationMarker(lat: lat, lng: lng);
    _mapKey.currentState?.focusLatLng(lat: lat, lng: lng, level: 4);

    // silent=true 는 앱 부팅 시 자동 호출 — 주변 검색 생략.
    if (silent) return;

    // ── 내 주변 장소 검색 ──────────────────────────────────────────────
    setState(() {
      _userLat = lat;
      _userLng = lng;
      _nearbyMode = true;
      _searching = true;
      _searchError = null;
      _sheetState = _SheetState.results;
      _selectedCategoryIndex = null;
    });

    if (_sheetController.isAttached) {
      _sheetController.animateTo(
        _sheetInitSize,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }

    try {
      final auth = ref.read(authProvider);
      final petId = auth is AuthAuthenticated
          ? auth.user.primaryPetId ?? auth.user.primaryPet?.id
          : null;

      final results = await ref.read(placeApiProvider).search(
            query: '반려견 동반 장소',
            petId: petId,
            lat: lat,
            lng: lng,
          );

      if (!mounted) return;

      // lat/lng 없는 장소 제외 + 거리순 정렬
      final nearby = results
          .where((p) => p.lat != 0.0 && p.lng != 0.0)
          .toList()
        ..sort((a, b) {
          final da = _haversineKm(lat, lng, a.lat, a.lng);
          final db = _haversineKm(lat, lng, b.lat, b.lng);
          return da.compareTo(db);
        });

      setState(() {
        _results = nearby;
        _searching = false;
      });
      _mapKey.currentState?.setMarkers(nearby);

      if (nearby.isEmpty) {
        Fluttertoast.showToast(msg: '주변에 반려견 동반 장소가 없어요');
      }
    } catch (e) {
      if (!mounted) return;
      final msg = formatDioError(e, '주변 장소 검색 실패');
      setState(() {
        _searching = false;
        _searchError = msg;
      });
      Fluttertoast.showToast(msg: msg);
    }
  }

  /// 경로 조회 — 현재 위치 → 목적지.
  Future<void> _requestRoute(PlaceCard place) async {
    if (place.lat == 0.0 || place.lng == 0.0) return;

    final permission = await LocationService.ensurePermission();
    if (permission != LocationPermissionResult.granted) {
      Fluttertoast.showToast(msg: '경로 조회에 위치 권한이 필요해요');
      return;
    }

    setState(() => _routeLoading = true);

    try {
      final position = await LocationService.getCurrent();
      if (!mounted || position == null) {
        setState(() => _routeLoading = false);
        return;
      }

      final api = ref.read(directionsApiProvider);
      final result = await api.getRoute(DirectionsRouteRequest(
        originLat: position.latitude,
        originLng: position.longitude,
        destLat: place.lat,
        destLng: place.lng,
        destName: place.name,
      ));

      if (!mounted) return;
      setState(() {
        _routeResult = result;
        _routeLoading = false;
      });

      // 지도에 polyline 그리기
      final points = result.points
          .map((p) => {'lat': p.lat, 'lng': p.lng})
          .toList();
      _mapKey.currentState?.drawRoutePolyline(points);
    } catch (e) {
      if (!mounted) return;
      setState(() => _routeLoading = false);
      final msg = formatDioError(e, '경로 조회 실패');
      Fluttertoast.showToast(msg: msg);
    }
  }

  void _clearRoute() {
    setState(() => _routeResult = null);
    _mapKey.currentState?.clearRoutePolyline();
  }

  void _onMarkerTap(KakaoMarkerTap tap) {
    if (tap.name.isEmpty) return;
    final place = _results.firstWhere(
      (r) => r.name == tap.name,
      orElse: () => PlaceCard(name: tap.name),
    );
    _showDetail(place);
  }

  void _showDetail(PlaceCard place) {
    final mapState = _mapKey.currentState;
    if (mapState != null && place.lat != 0.0 && place.lng != 0.0) {
      mapState.focusLatLng(lat: place.lat, lng: place.lng, level: 4);
    }
    setState(() {
      _detailPlace = place;
      _sheetState = _SheetState.detail;
    });
    if (_sheetController.isAttached) {
      _sheetController.animateTo(
        0.55,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  Future<void> _focusPlace(PlaceCard place) async {
    // 1) 상세 카드 즉시 전환 (로딩 상태로 먼저 보여줌)
    _showDetail(place);

    // 결과 목록에 없으면 추가 (하단 카드 표시용)
    if (place.contentId.isNotEmpty &&
        !_results.any((r) => r.contentId == place.contentId)) {
      setState(() => _results = [place, ..._results]);
    }

    final mapState = _mapKey.currentState;

    if (place.lat != 0.0 && place.lng != 0.0) {
      // lat/lng 있음 — 즉시 카메라 이동 + 마커
      if (mapState != null) {
        final inResults = _results.any(
          (r) => r.contentId == place.contentId && place.contentId.isNotEmpty,
        );
        mapState.setMarkers(inResults ? _results : [place]);
        mapState.focusLatLng(lat: place.lat, lng: place.lng, level: 4);
      }
    } else {
      // lat/lng 없음 — byName API 로 좌표 조회 후 카메라 이동
      try {
        final facility = await ref.read(placeApiProvider).byName(place.name);
        if (!mounted) return;
        if (facility.lat != 0.0 && facility.lng != 0.0) {
          final marker = PlaceCard(
            name: place.name,
            contentId: place.contentId,
            lat: facility.lat,
            lng: facility.lng,
            address: facility.address.isNotEmpty
                ? facility.address
                : place.address,
            subCategory: facility.subCategory.isNotEmpty
                ? facility.subCategory
                : place.subCategory,
          );
          _mapKey.currentState?.setMarkers([marker]);
          _mapKey.currentState?.focusLatLng(
            lat: facility.lat,
            lng: facility.lng,
            level: 4,
          );
        }
      } catch (_) {
        // 좌표 조회 실패해도 상세 카드는 이미 표시됨
      }
    }
  }

  /// WebView 가 준비된 경우에만 consume. 미준비 시 그대로 두어 onMapReady 가 처리.
  /// 즐겨찾기 "장소 보기" — 바로 상세 뷰로 이동 + 비동기로 지도 좌표 반영.
  Future<void> _viewFavorite(PlaceFavoriteItem fav) async {
    // 1) 즉시 상세 뷰 전환 (로딩 상태로 표시됨)
    _showDetail(PlaceCard(
      name: fav.name,
      contentId: fav.contentId,
      subCategory: fav.subCategory,
    ));
    // 2) byName 으로 좌표 확보 → 지도 갱신 + _detailPlace 에 lat/lng 보강
    try {
      final facility =
          await ref.read(placeApiProvider).byName(fav.name);
      if (!mounted) return;
      if (facility.lat != 0.0 && facility.lng != 0.0) {
        final enriched = PlaceCard(
          name: fav.name,
          contentId: fav.contentId,
          lat: facility.lat,
          lng: facility.lng,
          address: facility.address,
          subCategory: facility.subCategory.isNotEmpty
              ? facility.subCategory
              : fav.subCategory,
        );
        setState(() => _detailPlace = enriched);
        final mapState = _mapKey.currentState;
        mapState?.setMarkers([enriched]);
        mapState?.focusLatLng(
          lat: facility.lat,
          lng: facility.lng,
          level: 4,
        );
      }
    } catch (_) {
      // 좌표 없어도 상세 카드는 이미 표시됨
    }
  }

  /// WebView 가 준비된 경우에만 consume. 미준비 시 그대로 두어 onMapReady 가 처리.
  void _consumePendingFocus() {
    if (!_mapReady) return;
    final pending = ref.read(mapFocusProvider.notifier).consume();
    if (pending != null) _focusPlace(pending);
  }

  void _goBack() {
    _clearRoute();
    setState(() {
      if (_sheetState == _SheetState.detail) {
        _sheetState = _results.isNotEmpty
            ? _SheetState.results
            : _SheetState.favorites;
      } else if (_sheetState == _SheetState.results) {
        _sheetState = _SheetState.favorites;
        _results = const [];
        _searchError = null;
        _nearbyMode = false;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<PlaceCard?>(mapFocusProvider, (_, next) {
      if (next == null) return;
      // _mapReady 인 경우 다음 프레임에서 즉시 consume+focus.
      // 미준비라면 consume 하지 않고 onMapReady 에 맡김.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        _consumePendingFocus();
      });
    });

    // 홈·마이페이지의 [더보기] / 즐겨찾기 헤더 탭 → 즐겨찾기 목록 뷰로 리셋.
    ref.listen<bool>(mapShowFavoritesProvider, (_, show) {
      if (!show) return;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        // 소비 (중복 트리거 방지)
        ref.read(mapShowFavoritesProvider.notifier).state = false;
        setState(() {
          _sheetState = _SheetState.favorites;
          _results = const [];
          _searchError = null;
          _selectedCategoryIndex = null;
          _nearbyMode = false;
        });
        if (_sheetController.isAttached) {
          _sheetController.animateTo(
            _sheetInitSize,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    });

    final auth = ref.watch(authProvider);
    if (auth is! AuthAuthenticated) {
      return const LoginTabView(message: '로그인 후 장소를 탐색할 수 있어요');
    }

    final topPad = MediaQuery.of(context).padding.top;

    return Stack(
      children: [
        // ── 지도 전체 화면 ─────────────────────────────────────────────
        Positioned.fill(
          child: KakaoMapView(
            key: _mapKey,
            onMarkerTap: _onMarkerTap,
            onMapReady: (_) {
              _mapReady = true;
              // FAB 위치를 시트 attach 후 다시 그리도록 setState 호출
              setState(() {});
              _refreshLocation(silent: true);
              _consumePendingFocus();
            },
            onError: (msg) => Fluttertoast.showToast(msg: msg),
          ),
        ),

        // ── 검색창 + 카테고리 칩 (상단 플로팅) ───────────────────────
        Positioned(
          top: topPad + 12,
          left: 12,
          right: 12,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Material(
                elevation: 4,
                borderRadius: BorderRadius.circular(16),
                color: Colors.white,
                shadowColor: Colors.black26,
                child: TextField(
                  controller: _queryCtrl,
                  textInputAction: TextInputAction.search,
                  onChanged: (_) =>
                      setState(() => _selectedCategoryIndex = null),
                  onSubmitted: (_) => _search(),
                  decoration: InputDecoration(
                    hintText: '예: 강남 카페, 한강공원',
                    hintStyle: const TextStyle(
                      color: AppColors.mutedForeground,
                      fontSize: 14,
                    ),
                    prefixIcon: const Icon(
                      LucideIcons.search,
                      size: 18,
                      color: AppColors.mutedForeground,
                    ),
                    suffixIcon: _searching
                        ? const Padding(
                            padding: EdgeInsets.all(14),
                            child: SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: AppColors.brandOrange,
                              ),
                            ),
                          )
                        : IconButton(
                            icon: const Icon(
                              LucideIcons.send,
                              size: 18,
                              color: AppColors.brandOrange,
                            ),
                            onPressed: _search,
                          ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: BorderSide.none,
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(16),
                      borderSide: const BorderSide(
                        color: AppColors.brandOrange,
                        width: 1.5,
                      ),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 13,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              // 카테고리 칩 (가로 스크롤) — 첫 항목: [내 위치]
              SizedBox(
                height: 38,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: EdgeInsets.zero,
                  itemCount: _kCategories.length + 1,
                  separatorBuilder: (context2, i) => const SizedBox(width: 8),
                  itemBuilder: (context2, i) {
                    if (i == 0) {
                      return _LocationChip(onTap: _refreshLocation);
                    }
                    final cat = _kCategories[i - 1];
                    return _CategoryChip(
                      label: cat.label,
                      emoji: cat.emoji,
                      isSelected: _selectedCategoryIndex == i - 1,
                      onTap: () => _search(
                        overrideQuery: cat.query,
                        categoryIndex: i - 1,
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),

        // ── 현재 위치 버튼 (시트 높이 따라 상하 이동) ─────────────────
        AnimatedBuilder(
          animation: _sheetController,
          builder: (context, child) {
            final screenH = MediaQuery.of(context).size.height;
            final sheetH = _sheetController.isAttached
                ? _sheetController.size * screenH
                : _sheetInitSize * screenH;
            return Positioned(
              right: 12,
              bottom: sheetH + 12,
              child: child!,
            );
          },
          child: FloatingActionButton.small(
            heroTag: 'gps-refresh',
            onPressed: () => _refreshLocation(),
            backgroundColor: Colors.white,
            foregroundColor: AppColors.brandOrange,
            elevation: 3,
            tooltip: '내 위치',
            child: const Icon(LucideIcons.locate, size: 18),
          ),
        ),

        // ── 하단 드래거블 시트 ─────────────────────────────────────────
        Positioned.fill(
          child: DraggableScrollableSheet(
            controller: _sheetController,
            initialChildSize: _sheetInitSize,
            minChildSize: _sheetMinSize,
            maxChildSize: _sheetMaxSize,
            snap: true,
            snapSizes: const [_sheetMinSize, _sheetInitSize, _sheetMaxSize],
            builder: (_, scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius:
                      BorderRadius.vertical(top: Radius.circular(24)),
                  boxShadow: [
                    BoxShadow(
                      color: Color(0x20000000),
                      blurRadius: 20,
                      offset: Offset(0, -6),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // 드래그 핸들
                    Padding(
                      padding: const EdgeInsets.only(top: 10, bottom: 4),
                      child: Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: const Color(0xFFD0D0D0),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    // 시트 헤더
                    Padding(
                      padding: const EdgeInsets.fromLTRB(8, 2, 16, 4),
                      child: Row(
                        children: [
                          if (_sheetState != _SheetState.favorites)
                            IconButton(
                              icon: const Icon(
                                LucideIcons.arrowLeft,
                                size: 20,
                              ),
                              color: AppColors.darkBrown,
                              onPressed: _goBack,
                              padding: const EdgeInsets.all(8),
                              constraints: const BoxConstraints(),
                            ),
                          if (_sheetState != _SheetState.favorites)
                            const SizedBox(width: 4),
                          if (_sheetState == _SheetState.favorites)
                            const SizedBox(width: 16),
                          Expanded(
                            child: Text(
                              switch (_sheetState) {
                                _SheetState.favorites => '즐겨찾기 장소',
                                _SheetState.results =>
                                  _nearbyMode ? '내 주변 장소' : '검색 결과',
                                _SheetState.detail =>
                                  _detailPlace?.name ?? '장소 상세',
                              },
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: AppColors.darkBrown,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Divider(height: 1, color: Color(0xFFF0F0F0)),
                    // 시트 콘텐츠 (3-state)
                    Expanded(
                      child: switch (_sheetState) {
                        _SheetState.favorites => _FavoritesSheet(
                            scrollController: scrollController,
                            onViewFavorite: _viewFavorite,
                          ),
                        _SheetState.results => _ResultsSheet(
                            scrollController: scrollController,
                            results: _results,
                            searching: _searching,
                            error: _searchError,
                            onViewPlace: _showDetail,
                            userLat: _userLat,
                            userLng: _userLng,
                          ),
                        _SheetState.detail => _DetailSheet(
                            key: ValueKey(_detailPlace?.name),
                            scrollController: scrollController,
                            sheetController: _sheetController,
                            place: _detailPlace,
                            onRequestRoute: _requestRoute,
                            onClearRoute: _clearRoute,
                            routeResult: _routeResult,
                            routeLoading: _routeLoading,
                          ),
                      },
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

// ── 카테고리 칩 ───────────────────────────────────────────────────────────────

class _CategoryChip extends StatelessWidget {
  const _CategoryChip({
    required this.label,
    required this.emoji,
    required this.onTap,
    this.isSelected = false,
  });

  final String label;
  final String emoji;
  final VoidCallback onTap;
  final bool isSelected;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.brandOrange : Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(
                alpha: isSelected ? 0.18 : 0.10,
              ),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(emoji, style: const TextStyle(fontSize: 14)),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: isSelected ? Colors.white : AppColors.darkBrown,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 내 위치 칩 ────────────────────────────────────────────────────────────────

class _LocationChip extends StatelessWidget {
  const _LocationChip({required this.onTap});

  final Future<void> Function() onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.10),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              LucideIcons.locate,
              size: 14,
              color: AppColors.brandOrange,
            ),
            SizedBox(width: 6),
            Text(
              '내 위치',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: AppColors.darkBrown,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 즐겨찾기 시트 콘텐츠 ──────────────────────────────────────────────────────

class _FavoritesSheet extends ConsumerStatefulWidget {
  const _FavoritesSheet({
    required this.scrollController,
    required this.onViewFavorite,
  });

  final ScrollController scrollController;
  final ValueChanged<PlaceFavoriteItem> onViewFavorite;

  @override
  ConsumerState<_FavoritesSheet> createState() => _FavoritesSheetState();
}

class _FavoritesSheetState extends ConsumerState<_FavoritesSheet> {
  /// 제거 중인 항목 — 즉시 빈 하트 표시용 옵티미스틱 상태.
  final _pendingRemoval = <String>{};

  Future<void> _remove(PlaceFavoriteItem fav) async {
    if (fav.contentId.isEmpty) return;
    setState(() => _pendingRemoval.add(fav.contentId));
    Fluttertoast.showToast(msg: '즐겨찾기에서 제거되었습니다');
    try {
      await ref
          .read(favoriteContentIdsProvider.notifier)
          .toggle(fav.contentId);
      ref.invalidate(favoritePlacesProvider);
    } catch (e) {
      // 실패 시 롤백
      if (mounted) setState(() => _pendingRemoval.remove(fav.contentId));
      Fluttertoast.showToast(msg: '즐겨찾기 해제 실패: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final favAsync = ref.watch(favoritePlacesProvider);
    return favAsync.when(
      loading: () =>
          const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            '즐겨찾기를 불러오지 못했어요\n$e',
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.mutedForeground),
          ),
        ),
      ),
      data: (favorites) {
        if (favorites.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Text('🐾', style: TextStyle(fontSize: 40)),
                  SizedBox(height: 12),
                  Text(
                    '즐겨찾기한 장소가 없어요.\n검색 후 ❤️를 눌러 저장해보세요!',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: AppColors.mutedForeground,
                      height: 1.6,
                    ),
                  ),
                ],
              ),
            ),
          );
        }
        return ListView.separated(
          controller: widget.scrollController,
          padding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          itemCount: favorites.length,
          separatorBuilder: (context2, i) =>
              const Divider(height: 1, color: Color(0xFFF5F5F5)),
          itemBuilder: (_, i) {
            final fav = favorites[i];
            final isPending = _pendingRemoval.contains(fav.contentId);
            return ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 4,
                vertical: 4,
              ),
              // 하트: 채워진(주황) → 빈(회색) 즉시 전환 후 목록에서 제거
              leading: GestureDetector(
                onTap: isPending ? null : () => _remove(fav),
                child: Container(
                  width: 44,
                  height: 44,
                  alignment: Alignment.center,
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 200),
                    child: Icon(
                      isPending ? Icons.favorite_border : Icons.favorite,
                      key: ValueKey(isPending),
                      size: 24,
                      color: isPending
                          ? AppColors.mutedForeground
                          : AppColors.brandOrange,
                    ),
                  ),
                ),
              ),
              title: Text(
                fav.name,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: isPending
                      ? AppColors.mutedForeground
                      : AppColors.darkBrown,
                ),
              ),
              subtitle: fav.subCategory.isNotEmpty
                  ? Text(
                      fav.subCategory,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.mutedForeground,
                      ),
                    )
                  : null,
              trailing: isPending
                  ? null
                  : GestureDetector(
                      onTap: () => widget.onViewFavorite(fav),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.peach,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          '장소 보기',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AppColors.brandOrange,
                          ),
                        ),
                      ),
                    ),
              onTap: isPending ? null : () => widget.onViewFavorite(fav),
            );
          },
        );
      },
    );
  }
}

// ── 검색 결과 시트 콘텐츠 ─────────────────────────────────────────────────────

class _ResultsSheet extends StatelessWidget {
  const _ResultsSheet({
    required this.scrollController,
    required this.results,
    required this.searching,
    required this.error,
    required this.onViewPlace,
    this.userLat,
    this.userLng,
  });

  final ScrollController scrollController;
  final List<PlaceCard> results;
  final bool searching;
  final String? error;
  final ValueChanged<PlaceCard> onViewPlace;
  final double? userLat;
  final double? userLng;

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
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Opacity(
                opacity: 0.35,
                child: Image.asset('assets/logo.png', height: 56),
              ),
              const SizedBox(height: 12),
              const Text(
                '검색 결과가 없어요.\n다른 키워드로 검색해보세요.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.mutedForeground,
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      );
    }
    return ListView.separated(
      controller: scrollController,
      padding:
          const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: results.length,
      separatorBuilder: (context2, i) => const SizedBox(height: 12),
      itemBuilder: (_, i) => _ResultCard(
            place: results[i],
            onViewPlace: onViewPlace,
            userLat: userLat,
            userLng: userLng,
          ),
    );
  }
}

// ── 검색 결과 카드 ────────────────────────────────────────────────────────────

class _ResultCard extends ConsumerWidget {
  const _ResultCard({
    required this.place,
    required this.onViewPlace,
    this.userLat,
    this.userLng,
  });

  final PlaceCard place;
  final ValueChanged<PlaceCard> onViewPlace;
  final double? userLat;
  final double? userLng;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(favoriteContentIdsProvider);
    final isFav = favorites.contains(place.contentId);
    final image = place.imageUrl;

    // 거리 계산 (유저 위치 + 장소 좌표 모두 유효할 때)
    String? distanceText;
    if (userLat != null &&
        userLng != null &&
        place.lat != 0.0 &&
        place.lng != 0.0) {
      final km = _haversineKm(userLat!, userLng!, place.lat, place.lng);
      distanceText = _formatDistance(km);
    }

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFF0EBE5)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 이미지
                ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: SizedBox(
                    width: 72,
                    height: 72,
                    child: image == null
                        ? Container(
                            color: AppColors.peach,
                            alignment: Alignment.center,
                            child: const Icon(
                              LucideIcons.mapPin,
                              color: AppColors.brandOrange,
                            ),
                          )
                        : Image.network(
                            image,
                            fit: BoxFit.cover,
                            errorBuilder: (ctx, e, s) => Container(
                              color: AppColors.peach,
                              alignment: Alignment.center,
                              child: const Icon(
                                LucideIcons.image,
                                color: AppColors.brandOrange,
                              ),
                            ),
                          ),
                  ),
                ),
                const SizedBox(width: 12),
                // 텍스트 정보
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        place.name,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: AppColors.darkBrown,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (place.address.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          place.address,
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.mutedForeground,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                      if (place.subCategory.isNotEmpty ||
                          distanceText != null) ...[
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 6,
                          runSpacing: 4,
                          children: [
                            if (distanceText != null)
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFE8F4FD),
                                  borderRadius: BorderRadius.circular(99),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(
                                      LucideIcons.navigation,
                                      size: 10,
                                      color: Color(0xFF4285F4),
                                    ),
                                    const SizedBox(width: 3),
                                    Text(
                                      distanceText,
                                      style: const TextStyle(
                                        fontSize: 10,
                                        color: Color(0xFF4285F4),
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            if (place.subCategory.isNotEmpty)
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.peach,
                                  borderRadius: BorderRadius.circular(99),
                                ),
                                child: Text(
                                  place.subCategory,
                                  style: const TextStyle(
                                    fontSize: 10,
                                    color: AppColors.brandOrange,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
                // 즐겨찾기 하트 버튼
                GestureDetector(
                  onTap: () => _toggleFav(ref, isFav),
                  child: Padding(
                    padding: const EdgeInsets.all(4),
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 180),
                      child: Icon(
                        isFav ? Icons.favorite : Icons.favorite_border,
                        key: ValueKey(isFav),
                        size: 22,
                        color: isFav
                            ? AppColors.brandOrange
                            : AppColors.mutedForeground,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: Color(0xFFF5F0EB)),
          // 장소 보기 버튼
          InkWell(
            onTap: () => onViewPlace(place),
            borderRadius: const BorderRadius.vertical(
              bottom: Radius.circular(16),
            ),
            child: const Padding(
              padding: EdgeInsets.symmetric(vertical: 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    LucideIcons.mapPin,
                    size: 14,
                    color: AppColors.brandOrange,
                  ),
                  SizedBox(width: 6),
                  Text(
                    '장소 보기',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.brandOrange,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _toggleFav(WidgetRef ref, bool wasFav) async {
    if (place.contentId.isEmpty) {
      Fluttertoast.showToast(msg: '즐겨찾기 가능한 장소가 아닙니다 (content_id 없음)');
      return;
    }
    try {
      await ref
          .read(favoriteContentIdsProvider.notifier)
          .toggle(place.contentId);
      ref.invalidate(favoritePlacesProvider);
      Fluttertoast.showToast(
        msg: wasFav ? '즐겨찾기에서 제거됐어요' : '즐겨찾기에 추가됐어요',
      );
    } catch (e) {
      Fluttertoast.showToast(msg: '즐겨찾기 토글 실패: $e');
    }
  }
}

// ── 장소 상세 시트 콘텐츠 ─────────────────────────────────────────────────────

class _DetailSheet extends ConsumerStatefulWidget {
  const _DetailSheet({
    super.key,
    required this.scrollController,
    required this.sheetController,
    required this.place,
    required this.onRequestRoute,
    required this.onClearRoute,
    this.routeResult,
    this.routeLoading = false,
  });

  final ScrollController scrollController;
  final DraggableScrollableController sheetController;
  final PlaceCard? place;
  final ValueChanged<PlaceCard> onRequestRoute;
  final VoidCallback onClearRoute;
  final DirectionsRouteResponse? routeResult;
  final bool routeLoading;

  @override
  ConsumerState<_DetailSheet> createState() => _DetailSheetState();
}

class _DetailSheetState extends ConsumerState<_DetailSheet> {
  Future<FacilityCard>? _facilityFuture;

  @override
  void initState() {
    super.initState();
    if (widget.place != null) {
      _facilityFuture =
          ref.read(placeApiProvider).byName(widget.place!.name);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.place == null) {
      return const Center(child: Text('장소 정보가 없어요'));
    }
    return FutureBuilder<FacilityCard>(
      future: _facilityFuture,
      builder: (_, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        return _DetailBody(
          place: widget.place!,
          facility: snapshot.data,
          scrollController: widget.scrollController,
          sheetController: widget.sheetController,
          onRequestRoute: widget.onRequestRoute,
          onClearRoute: widget.onClearRoute,
          routeResult: widget.routeResult,
          routeLoading: widget.routeLoading,
        );
      },
    );
  }
}

// ── 장소 상세 본문 ────────────────────────────────────────────────────────────

class _DetailBody extends ConsumerWidget {
  const _DetailBody({
    required this.place,
    required this.facility,
    required this.scrollController,
    required this.sheetController,
    required this.onRequestRoute,
    required this.onClearRoute,
    this.routeResult,
    this.routeLoading = false,
  });

  final PlaceCard place;
  final FacilityCard? facility;
  final ScrollController scrollController;
  final DraggableScrollableController sheetController;
  final ValueChanged<PlaceCard> onRequestRoute;
  final VoidCallback onClearRoute;
  final DirectionsRouteResponse? routeResult;
  final bool routeLoading;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final imageUrl = place.imageUrl ?? facility?.imageUrl;
    final address = place.address.isNotEmpty
        ? place.address
        : (facility?.address ?? '');
    final tel =
        place.tel.isNotEmpty ? place.tel : (facility?.tel ?? '');
    final operation = place.operation.isNotEmpty
        ? place.operation
        : (facility?.operation ?? '');
    final conditions = place.conditions.isNotEmpty
        ? place.conditions
        : (facility?.conditions ?? '');
    final description = place.description.isNotEmpty
        ? place.description
        : (facility?.description ?? '');
    final hasParking =
        place.hasParking == 'Y' || facility?.hasParking == 'Y';
    final indoor = place.indoor == 'Y' || facility?.indoor == 'Y';
    final outdoor =
        place.outdoor == 'Y' || facility?.outdoor == 'Y';
    final subCat = place.subCategory.isNotEmpty
        ? place.subCategory
        : (facility?.subCategory ?? '');

    // 좌표: place 에 없으면 facility 에서 가져옴 (즐겨찾기 장소 대응)
    final lat = place.lat != 0.0 ? place.lat : (facility?.lat ?? 0.0);
    final lng = place.lng != 0.0 ? place.lng : (facility?.lng ?? 0.0);
    final hasCoords = lat != 0.0 && lng != 0.0;
    // 경로 요청용 PlaceCard (facility 좌표 반영)
    final routePlace = (place.lat != 0.0 && place.lng != 0.0)
        ? place
        : PlaceCard(
            name: place.name,
            contentId: place.contentId,
            lat: lat,
            lng: lng,
            address: address,
            subCategory: subCat,
          );

    return SingleChildScrollView(
      controller: scrollController,
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _DetailImage(imageUrl: imageUrl, sheetController: sheetController),
          const SizedBox(height: 16),
          if (address.isNotEmpty)
            _InfoRow(icon: LucideIcons.mapPin, text: address),
          if (tel.isNotEmpty)
            _InfoRow(icon: LucideIcons.phone, text: tel),
          if (operation.isNotEmpty)
            _InfoRow(icon: LucideIcons.clock, text: operation),
          if (hasParking)
            const _InfoRow(icon: LucideIcons.car, text: '주차 가능'),
          if (subCat.isNotEmpty || indoor || outdoor) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                if (subCat.isNotEmpty) _InfoChip(text: subCat),
                if (indoor) const _InfoChip(text: '실내 가능'),
                if (outdoor) const _InfoChip(text: '실외 가능'),
              ],
            ),
          ],
          if (conditions.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              '반려견 이용 조건',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: AppColors.subBrown2,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              conditions,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.darkBrown,
                height: 1.5,
              ),
            ),
          ],
          if (description.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              '장소 설명',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: AppColors.subBrown2,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              description,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.darkBrown,
                height: 1.6,
              ),
            ),
          ],
          const SizedBox(height: 20),
          // 경로 요약 배너
          if (routeResult != null)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF4ED),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.brandOrange.withValues(alpha: 0.3)),
              ),
              child: Row(
                children: [
                  const Icon(LucideIcons.navigation, size: 18, color: AppColors.brandOrange),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      '예상 ${routeResult!.durationText} · ${routeResult!.distanceText}',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: AppColors.darkBrown,
                      ),
                    ),
                  ),
                  GestureDetector(
                    onTap: onClearRoute,
                    child: const Icon(LucideIcons.x, size: 18, color: AppColors.mutedForeground),
                  ),
                ],
              ),
            ),
          // 길찾기 버튼 (경로 보기 / 카카오내비)
          if (hasCoords)
            Row(
              children: [
                // 경로 보기 (인앱 Polyline)
                Expanded(
                  child: FilledButton.icon(
                    onPressed: routeLoading
                        ? null
                        : () => onRequestRoute(routePlace),
                    icon: routeLoading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(LucideIcons.mapPin, size: 16),
                    label: Text(routeResult != null ? '경로 갱신' : '경로 보기'),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.brandOrange,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // 외부 네비 열기
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () async {
                      final permission =
                          await LocationService.ensurePermission();
                      if (permission != LocationPermissionResult.granted) {
                        // ignore: use_build_context_synchronously
                        if (!context.mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('위치 권한이 필요합니다. 설정에서 허용해 주세요.'),
                          ),
                        );
                        return;
                      }
                      final position = await LocationService.getCurrent();
                      // ignore: use_build_context_synchronously
                      if (!context.mounted) return;
                      await DirectionsService.open(
                        context: context,
                        endLat: lat,
                        endLng: lng,
                        destinationName: place.name,
                        startLat: position?.latitude,
                        startLng: position?.longitude,
                      );
                    },
                    icon: const Icon(LucideIcons.navigation, size: 16),
                    label: const Text('카카오맵 열기'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.brandOrange,
                      side: const BorderSide(color: AppColors.brandOrange),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          const SizedBox(height: 8),
          // 일기 쓰기 버튼
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () {
                  ref.read(pendingPlaceProvider.notifier).state = place;
                  ref.read(homeTabIndexProvider.notifier).state = 4;
                },
              icon: const Icon(LucideIcons.penTool, size: 16),
              label: const Text('이 장소로 일기 쓰기'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.brandOrange,
                side: const BorderSide(color: AppColors.brandOrange),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── 공용 소위젯 ───────────────────────────────────────────────────────────────

class _DetailImage extends StatelessWidget {
  const _DetailImage({
    required this.imageUrl,
    required this.sheetController,
  });

  final String? imageUrl;
  final DraggableScrollableController sheetController;

  // 시트 extent 에 따른 이미지 높이 범위
  static const double _minHeight = 140;
  static const double _maxHeight = 280;
  // 시트 사이즈 구간 (detail 진입 시 0.55 → 최대 0.88)
  static const double _extentLow = 0.36;
  static const double _extentHigh = 0.88;

  @override
  Widget build(BuildContext context) {
    final has = imageUrl != null && imageUrl!.isNotEmpty;
    return AnimatedBuilder(
      animation: sheetController,
      builder: (context, child) {
        final extent = sheetController.isAttached
            ? sheetController.size
            : _extentLow;
        // 0.36 → 140,  0.88 → 280  (선형 보간, clamp)
        final t = ((extent - _extentLow) / (_extentHigh - _extentLow))
            .clamp(0.0, 1.0);
        final height = _minHeight + (_maxHeight - _minHeight) * t;

        return ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: SizedBox(
            height: height,
            width: double.infinity,
            child: child,
          ),
        );
      },
      child: has
          ? Image.network(
              imageUrl!,
              fit: BoxFit.cover,
              errorBuilder: (ctx, e, s) => const _ImagePlaceholder(),
            )
          : const _ImagePlaceholder(),
    );
  }
}

class _ImagePlaceholder extends StatelessWidget {
  const _ImagePlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.peach,
      alignment: Alignment.center,
      child: const Text('🐾', style: TextStyle(fontSize: 48)),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 15, color: AppColors.brandOrange),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.darkBrown,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding:
          const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.peach,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 11,
          color: AppColors.brandOrange,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
