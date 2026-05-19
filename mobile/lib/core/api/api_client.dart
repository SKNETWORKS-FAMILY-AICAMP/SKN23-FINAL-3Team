import 'dart:async';

import 'package:dio/dio.dart';

import '../env/env.dart';
import '../storage/secure_storage.dart';
import 'api_exception.dart';

typedef UnauthorizedHandler = FutureOr<void> Function();

class ApiClient {
  ApiClient({
    required SecureStorageService storage,
    required UnauthorizedHandler onUnauthorized,
    Dio? dio,
  }) : _storage = storage,
       _onUnauthorized = onUnauthorized,
       _dio = dio ?? Dio() {
    _dio.options
      ..baseUrl = Env.apiBaseUrl
      ..connectTimeout = const Duration(seconds: 10)
      ..receiveTimeout = const Duration(seconds: 30)
      ..headers['Content-Type'] = 'application/json';

    _dio.interceptors.add(
      InterceptorsWrapper(onRequest: _attachAuthHeader, onError: _handleError),
    );
  }

  final Dio _dio;
  final SecureStorageService _storage;
  final UnauthorizedHandler _onUnauthorized;

  Dio get raw => _dio;

  Future<void> _attachAuthHeader(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.readAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  Future<void> _handleError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      await _storage.clearAccessToken();
      await _onUnauthorized();
    }
    handler.next(err);
  }

  Future<T> get<T>(String path, {Map<String, dynamic>? query}) =>
      _request<T>(() => _dio.get<T>(path, queryParameters: query));

  Future<T> post<T>(String path, {Object? body}) =>
      _request<T>(() => _dio.post<T>(path, data: body));

  Future<T> patch<T>(String path, {Object? body}) =>
      _request<T>(() => _dio.patch<T>(path, data: body));

  Future<T> delete<T>(String path) => _request<T>(() => _dio.delete<T>(path));

  Future<T> upload<T>(String path, FormData form) =>
      _request<T>(() => _dio.post<T>(path, data: form));

  Future<T> _request<T>(Future<Response<T>> Function() send) async {
    try {
      final response = await send();
      return response.data as T;
    } on DioException catch (err) {
      throw _toApiException(err);
    }
  }

  ApiException _toApiException(DioException err) {
    final detail = _extractDetail(err);
    return ApiException(statusCode: err.response?.statusCode, detail: detail);
  }

  String _extractDetail(DioException err) {
    final data = err.response?.data;
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.isNotEmpty) {
        return detail;
      }
    }
    return err.message ?? '네트워크 오류가 발생했습니다.';
  }
}
