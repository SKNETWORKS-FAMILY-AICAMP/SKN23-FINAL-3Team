import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

import '../../../core/env/env.dart';
import '../../../core/theme/app_colors.dart';
import '../../../shared/models/place.dart';

/// 카카오맵 임베드 위젯 — `flutter_inappwebview` + 카카오 JS SDK.
///
/// 사용자 결정 2026-05-03: Flutter 공식 카카오맵 SDK 부재로 WebView 임베드.
/// React `front/index.html` 과 동일한 JS SDK 자산 (`assets/kakao_map.html`)
/// 사용. JS Channel 양방향:
///
/// - Dart → JS: `setMarkers([{contentId,name,lat,lng,...}])` / `focusLatLng(lat,lng,level)`
/// - JS → Dart: `onMapReady(coord)` / `onMapMoved(coord)` / `onMarkerTap({contentId,name,lat,lng})`
///   / `onMapError({message})`
class KakaoMapView extends StatefulWidget {
  const KakaoMapView({
    super.key,
    this.onMapReady,
    this.onMarkerTap,
    this.onMapMoved,
    this.onError,
  });

  final ValueChanged<KakaoMapCoord>? onMapReady;
  final ValueChanged<KakaoMarkerTap>? onMarkerTap;
  final ValueChanged<KakaoMapCoord>? onMapMoved;
  final ValueChanged<String>? onError;

  @override
  State<KakaoMapView> createState() => KakaoMapViewState();
}

class KakaoMapViewState extends State<KakaoMapView> {
  InAppWebViewController? _controller;
  bool _ready = false;
  String? _loadError;
  late final Future<String> _htmlFuture;

  @override
  void initState() {
    super.initState();
    // Future 를 build 외부 (initState) 에서 1회만 생성 — 부모 rebuild 마다
    // 새 Future 가 생기면 FutureBuilder 가 loading 상태로 되돌아가 WebView
    // 가 사라졌다 나타나며 검정 깜빡임 발생 (Bug #6 root cause).
    _htmlFuture = _loadHtml();
  }

  Future<String> _loadHtml() async {
    final raw = await rootBundle.loadString('assets/kakao_map.html');
    final key = Env.kakaoMapsKey;
    if (key.isEmpty) {
      throw const KakaoMapMisconfigured(
        'VITE_KAKAO_JAVASCRIPT_API_KEY 환경변수가 비어있습니다. '
        '`flutter run --dart-define-from-file=../.env` 옵션 확인.',
      );
    }
    return raw.replaceAll('{{KAKAO_KEY}}', key);
  }

  /// Dart → JS: 마커 일괄 갱신.
  Future<void> setMarkers(List<PlaceCard> places) async {
    final controller = _controller;
    if (controller == null || !_ready) return;
    final payload = jsonEncode([
      for (final p in places)
        if (p.lat != 0.0 && p.lng != 0.0)
          {
            'contentId': p.contentId,
            'name': p.name,
            'lat': p.lat,
            'lng': p.lng,
            'subCategory': p.subCategory,
          },
    ]);
    await controller.evaluateJavascript(source: 'setMarkers($payload);');
  }

  /// Dart → JS: 단일 좌표 포커스.
  Future<void> focusLatLng({
    required double lat,
    required double lng,
    int? level,
  }) async {
    final controller = _controller;
    if (controller == null || !_ready) return;
    final levelArg = level == null ? '' : ', $level';
    await controller
        .evaluateJavascript(source: 'focusLatLng($lat, $lng$levelArg);');
  }

  /// Dart → JS: 현재 위치 GPS 마커 (별도 색상, setMarkers 와 독립).
  Future<void> setCurrentLocationMarker({
    required double lat,
    required double lng,
  }) async {
    final controller = _controller;
    if (controller == null || !_ready) return;
    await controller.evaluateJavascript(
      source: 'setCurrentLocationMarker($lat, $lng);',
    );
  }

  void _registerHandlers(InAppWebViewController controller) {
    controller.addJavaScriptHandler(
      handlerName: 'onMapReady',
      callback: (args) {
        setState(() => _ready = true);
        final coord = _coordFromArgs(args);
        if (coord != null) widget.onMapReady?.call(coord);
      },
    );
    controller.addJavaScriptHandler(
      handlerName: 'onMapMoved',
      callback: (args) {
        final coord = _coordFromArgs(args);
        if (coord != null) widget.onMapMoved?.call(coord);
      },
    );
    controller.addJavaScriptHandler(
      handlerName: 'onMarkerTap',
      callback: (args) {
        if (args.isEmpty) return;
        final m = (args[0] as Map).cast<String, dynamic>();
        widget.onMarkerTap?.call(
          KakaoMarkerTap(
            contentId: m['contentId'] as String? ?? '',
            name: m['name'] as String? ?? '',
            lat: (m['lat'] as num?)?.toDouble() ?? 0.0,
            lng: (m['lng'] as num?)?.toDouble() ?? 0.0,
          ),
        );
      },
    );
    controller.addJavaScriptHandler(
      handlerName: 'onMapError',
      callback: (args) {
        final msg = args.isNotEmpty
            ? ((args[0] as Map)['message'] as String? ?? 'unknown')
            : 'unknown';
        setState(() => _loadError = msg);
        widget.onError?.call(msg);
      },
    );
  }

  KakaoMapCoord? _coordFromArgs(List<dynamic> args) {
    if (args.isEmpty) return null;
    final m = (args[0] as Map).cast<String, dynamic>();
    final lat = (m['lat'] as num?)?.toDouble();
    final lng = (m['lng'] as num?)?.toDouble();
    if (lat == null || lng == null) return null;
    return KakaoMapCoord(lat: lat, lng: lng, level: (m['level'] as num?)?.toInt());
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<String>(
      future: _htmlFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return _ErrorView(message: '${snapshot.error}');
        }
        return Stack(
          children: [
            InAppWebView(
              initialData: InAppWebViewInitialData(
                data: snapshot.data!,
                mimeType: 'text/html',
                encoding: 'utf-8',
                baseUrl: WebUri('https://withdog.kro.kr/'),
              ),
              initialSettings: InAppWebViewSettings(
                javaScriptEnabled: true,
                domStorageEnabled: true,
                supportZoom: true,
                builtInZoomControls: false,
                useWideViewPort: true,
                loadWithOverviewMode: true,
                allowsInlineMediaPlayback: true,
                // Bug #6 — Android WebView surface flip 시 검정 깜빡임 방지.
                transparentBackground: false,
              ),
              onWebViewCreated: (controller) {
                _controller = controller;
                _registerHandlers(controller);
              },
              onConsoleMessage: (_, msg) {
                debugPrint('[KakaoMapView console] ${msg.messageLevel} ${msg.message}');
              },
            ),
            if (_loadError != null)
              Positioned.fill(child: _ErrorView(message: _loadError!)),
          ],
        );
      },
    );
  }
}

class KakaoMapCoord {
  const KakaoMapCoord({required this.lat, required this.lng, this.level});

  final double lat;
  final double lng;
  final int? level;
}

class KakaoMarkerTap {
  const KakaoMarkerTap({
    required this.contentId,
    required this.name,
    required this.lat,
    required this.lng,
  });

  final String contentId;
  final String name;
  final double lat;
  final double lng;
}

class KakaoMapMisconfigured implements Exception {
  const KakaoMapMisconfigured(this.message);
  final String message;
  @override
  String toString() => message;
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      alignment: Alignment.center,
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.map_outlined, size: 56, color: AppColors.brandOrange),
          const SizedBox(height: 12),
          Text(
            '지도를 불러오지 못했습니다',
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppColors.darkBrown,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.subBrown2,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
