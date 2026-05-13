import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

/// 위치 권한 + 현재 좌표 추출 — `geolocator` 기반.
///
/// 사용처:
/// - MapTab: 진입 시 현재 위치 마커 + 검색 자동 주입
/// - 챗봇 (백엔드 lat/lng 수신 확장 후): "근처 ~" 질의 시 위치 동봉
class LocationService {
  /// 권한 요청 + 위치 서비스 활성 여부 검증.
  /// `LocationPermissionResult.granted` = 좌표 획득 가능.
  static Future<LocationPermissionResult> ensurePermission() async {
    final servicesEnabled = await Geolocator.isLocationServiceEnabled();
    if (!servicesEnabled) {
      return LocationPermissionResult.serviceDisabled;
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied) {
      return LocationPermissionResult.denied;
    }
    if (permission == LocationPermission.deniedForever) {
      return LocationPermissionResult.deniedForever;
    }
    return LocationPermissionResult.granted;
  }

  /// 현재 위치 반환 — 권한·서비스 사전 검증 + 실패 시 null.
  /// 호출자는 null 결과를 처리해야 (디폴트 좌표·안내 토스트 등).
  static Future<Position?> getCurrent() async {
    final permission = await ensurePermission();
    if (permission != LocationPermissionResult.granted) return null;
    try {
      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          // timeLimit: 시연 device 의 초기 fix 가 느릴 수 있어 longer 허용
        ),
      );
    } catch (_) {
      return null;
    }
  }
}

enum LocationPermissionResult {
  granted,
  denied, // 사용자가 1회 거부 — 재요청 가능
  deniedForever, // 사용자가 영구 거부 — 시스템 설정 안내 필요
  serviceDisabled, // 위치 서비스 OFF
}

/// 현재 위치 — `FutureProvider.autoDispose`. MapTab 진입 시 watch.
/// 권한 거부·실패 시 null. 호출자는 null = 디폴트 서울 시청 좌표 fallback.
final currentPositionProvider = FutureProvider.autoDispose<Position?>((
  _,
) async {
  return LocationService.getCurrent();
});
