import 'package:dio/dio.dart';

/// DioException → 사용자에게 보여줄 한글 메시지로 변환.
///
/// 우선순위:
///  1) 백엔드 HTTPException `detail` (있으면) → `{prefix} (status): {detail}`
///  2) dio 자체 에러 type + message → `{prefix}: {type} {message}`
///  3) 외 예외 → `{prefix}: {error}`
///
/// 권위 = §7-3 C `_formatDioError` 패턴. 본 헬퍼는 R3 (UX 마감) 에서 catch
/// 분기 통일용으로 추출 — 각 feature 의 inline 복사 제거.
String formatDioError(Object err, String prefix) {
  if (err is DioException) {
    final data = err.response?.data;
    final detail = data is Map ? data['detail']?.toString() : null;
    final code = err.response?.statusCode;
    if (detail != null && detail.isNotEmpty) {
      return '$prefix${code != null ? ' ($code)' : ''}: $detail';
    }
    final msg = err.message ?? '';
    return '$prefix: ${err.type.name}${msg.isEmpty ? '' : ' $msg'}';
  }
  return '$prefix: $err';
}
