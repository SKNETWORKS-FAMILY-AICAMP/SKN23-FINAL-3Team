class ApiException implements Exception {
  const ApiException({
    required this.statusCode,
    required this.detail,
  });

  final int? statusCode;
  final String detail;

  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isNotFound => statusCode == 404;

  @override
  String toString() => 'ApiException($statusCode): $detail';
}
