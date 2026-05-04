import 'dart:convert';

import 'package:dio/dio.dart';

import '../../core/api/api_client.dart';
import '../../shared/models/auth.dart';

class ImageApi {
  const ImageApi(this._client);

  final ApiClient _client;

  /// `POST /api/images` (multipart) — 로컬 파일 업로드
  Future<ImageUploadResponse> upload(String filePath) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
    });
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/images',
      data: form,
    );
    return ImageUploadResponse.fromJson(response.data!);
  }

  /// `POST /api/images` (multipart) — base64 PNG 바이트 직접 업로드.
  /// 다이어리 AI 이미지 생성 결과 (`/diary/generate-image` 응답) 를 S3 로 보낼 때.
  Future<ImageUploadResponse> uploadBase64Png({
    required String base64Data,
    String filename = 'diary.png',
  }) async {
    final bytes = base64Decode(base64Data);
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: filename),
    });
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/images',
      data: form,
    );
    return ImageUploadResponse.fromJson(response.data!);
  }

  /// `GET /api/images/{image_id}` — 이미지 메타 (S3 file_url 포함).
  Future<ImageUploadResponse> get(int imageId) async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/images/$imageId',
    );
    return ImageUploadResponse.fromJson(response.data!);
  }
}
