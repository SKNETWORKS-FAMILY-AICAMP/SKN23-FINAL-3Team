import '../../core/api/api_client.dart';

/// `POST /api/directions/route` 요청 DTO.
class DirectionsRouteRequest {
  const DirectionsRouteRequest({
    required this.originLat,
    required this.originLng,
    required this.destLat,
    required this.destLng,
    this.destName,
  });

  final double originLat;
  final double originLng;
  final double destLat;
  final double destLng;
  final String? destName;

  Map<String, dynamic> toJson() => {
        'origin_lat': originLat,
        'origin_lng': originLng,
        'dest_lat': destLat,
        'dest_lng': destLng,
        if (destName != null) 'dest_name': destName,
      };
}

/// 경로 좌표 한 점.
class RoutePoint {
  const RoutePoint({required this.lat, required this.lng});

  final double lat;
  final double lng;

  factory RoutePoint.fromJson(Map<String, dynamic> json) => RoutePoint(
        lat: (json['lat'] as num).toDouble(),
        lng: (json['lng'] as num).toDouble(),
      );
}

/// `POST /api/directions/route` 응답 DTO.
class DirectionsRouteResponse {
  const DirectionsRouteResponse({
    required this.distance,
    required this.duration,
    required this.points,
  });

  /// 총 거리 (m).
  final int distance;

  /// 총 소요 시간 (s).
  final int duration;

  /// 경로 좌표 배열.
  final List<RoutePoint> points;

  factory DirectionsRouteResponse.fromJson(Map<String, dynamic> json) {
    final rawPoints = (json['points'] as List<dynamic>?) ?? const [];
    return DirectionsRouteResponse(
      distance: json['distance'] as int? ?? 0,
      duration: json['duration'] as int? ?? 0,
      points: rawPoints
          .cast<Map<String, dynamic>>()
          .map(RoutePoint.fromJson)
          .toList(),
    );
  }

  /// 포맷된 거리 문자열 (예: "3.2km", "800m").
  String get distanceText {
    if (distance >= 1000) {
      return '${(distance / 1000).toStringAsFixed(1)}km';
    }
    return '${distance}m';
  }

  /// 포맷된 소요 시간 문자열 (예: "13분", "1시간 5분").
  String get durationText {
    final minutes = (duration / 60).ceil();
    if (minutes >= 60) {
      final h = minutes ~/ 60;
      final m = minutes % 60;
      return m > 0 ? '$h시간 $m분' : '$h시간';
    }
    return '$minutes분';
  }
}

/// 백엔드 `/api/directions/route` 호출 클라이언트.
class DirectionsApi {
  const DirectionsApi(this._client);

  final ApiClient _client;

  Future<DirectionsRouteResponse> getRoute(
      DirectionsRouteRequest req) async {
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/directions/route',
      data: req.toJson(),
    );
    return DirectionsRouteResponse.fromJson(response.data!);
  }
}
