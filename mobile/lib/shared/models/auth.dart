/// 백엔드 `schemas/auth.py TokenResponse`.
class AuthResponse {
  const AuthResponse({
    required this.accessToken,
    required this.tokenType,
    required this.isNewUser,
  });

  final String accessToken;
  final String tokenType;
  final bool isNewUser;

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
      isNewUser: json['is_new_user'] as bool,
    );
  }
}

/// 백엔드 `schemas/image.py ImageResponse` (POST /api/images 응답).
class ImageUploadResponse {
  const ImageUploadResponse({
    required this.id,
    required this.fileUrl,
    required this.fileName,
  });

  final int id;
  final String fileUrl;
  final String fileName;

  factory ImageUploadResponse.fromJson(Map<String, dynamic> json) {
    return ImageUploadResponse(
      id: json['id'] as int,
      fileUrl: json['file_url'] as String,
      fileName: json['file_name'] as String,
    );
  }
}
