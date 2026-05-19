import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';

import '../../core/api/api_client.dart';

/// `POST /api/diary/generate` 요청 — 백엔드 `main.py:393 DiaryRequest` 1:1.
class DiaryGenerateRequest {
  const DiaryGenerateRequest({
    this.petId = 'default',
    required this.petName,
    this.breed = '강아지',
    this.breedEn,
    this.birthDate,
    this.personalities = const [],
    this.ownerName = '',
    required this.mainAnswers,
    this.additionalAnswers = const [],
    required this.diaryType,
    required this.emotionEmoji,
    this.englishPrompt,
    this.mustIncludeKeywords = const [],
  });

  final String petId;
  final String petName;
  final String breed;
  final String? breedEn;
  final String? birthDate;
  final List<String> personalities;
  final String ownerName;
  final List<String> mainAnswers;
  final List<String> additionalAnswers;
  final String diaryType;
  final String emotionEmoji;
  final String? englishPrompt;
  final List<String> mustIncludeKeywords;

  Map<String, dynamic> toJson() => {
    'pet_id': petId,
    'pet_name': petName,
    'breed': breed,
    if (breedEn != null) 'breed_en': breedEn,
    if (birthDate != null) 'birth_date': birthDate,
    'personalities': personalities,
    'owner_name': ownerName,
    'main_answers': mainAnswers,
    'additional_answers': additionalAnswers,
    'diary_type': diaryType,
    'emotion_emoji': emotionEmoji,
    if (englishPrompt != null) 'english_prompt': englishPrompt,
    if (mustIncludeKeywords.isNotEmpty)
      'must_include_keywords': mustIncludeKeywords,
  };
}

/// `POST /api/diary/generate` 응답.
class DiaryGenerateResponse {
  const DiaryGenerateResponse({
    required this.title,
    required this.content,
    required this.summary,
    required this.imagePromptBase,
    required this.imagePrompt,
    required this.sessionId,
  });

  final String title;
  final String content;
  final String summary;
  final String imagePromptBase;
  final String imagePrompt;
  final String sessionId;

  factory DiaryGenerateResponse.fromJson(Map<String, dynamic> json) {
    return DiaryGenerateResponse(
      title: json['title'] as String? ?? '',
      content: json['content'] as String? ?? '',
      summary: json['summary'] as String? ?? '',
      imagePromptBase: json['image_prompt_base'] as String? ?? '',
      imagePrompt: json['image_prompt'] as String? ?? '',
      sessionId: json['session_id'] as String? ?? '',
    );
  }
}

class DiaryAiApi {
  const DiaryAiApi(this._client);

  final ApiClient _client;

  /// `POST /api/diary/generate` — DiaryRequest → 텍스트 + image_prompt
  ///
  /// gpt-4.1-mini 호출 + 평가 로깅으로 보통 15~30s 소요 → dio 기본 receiveTimeout
  /// (30s) 가 자주 걸린다. 본 호출 전용으로 90s 로 확장.
  Future<DiaryGenerateResponse> generate(DiaryGenerateRequest req) async {
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/diary/generate',
      data: req.toJson(),
      options: Options(receiveTimeout: const Duration(seconds: 90)),
    );
    return DiaryGenerateResponse.fromJson(response.data!);
  }

  /// `POST /api/diary/generate-image` — image_prompt → base64
  ///
  /// OpenAI `gpt-image-1` 1024x1024 medium 응답이 30~60s + base64 (~1MB) 다운로드
  /// → dio 기본 receiveTimeout (30s) 가 거의 항상 timeout (Bug #3 root cause,
  /// 2026-05-04). 본 호출 전용으로 180s 로 확장.
  Future<String> generateImage({
    required String imagePrompt,
    String sessionId = '',
  }) async {
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/diary/generate-image',
      data: {'image_prompt': imagePrompt, 'session_id': sessionId},
      options: Options(receiveTimeout: const Duration(seconds: 180)),
    );
    return response.data!['image_base64'] as String;
  }

  /// `POST /api/diary/photo-style` — 사진 → 일러스트 변환.
  ///
  /// GPT-4o Vision 분석 + gpt-image-1 일러스트 생성 + S3 업로드.
  /// 응답: `{ type, content, image_url? }`.
  Future<PhotoStyleResponse> photoStyle({
    required String filePath,
    int? chatRoomId,
    int? dogId,
  }) async {
    final fileName = filePath.split('/').last.split('\\').last;
    final ext = fileName.split('.').last.toLowerCase();
    final mimeType = switch (ext) {
      'png' => 'image/png',
      'gif' => 'image/gif',
      'webp' => 'image/webp',
      _ => 'image/jpeg',
    };

    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(
        filePath,
        filename: fileName,
        contentType: MediaType.parse(mimeType),
      ),
      if (chatRoomId != null) 'chat_room_id': chatRoomId,
      if (dogId != null) 'dog_id': dogId,
    });

    final response = await _client.raw.post<Map<String, dynamic>>(
      '/diary/photo-style',
      data: formData,
      options: Options(receiveTimeout: const Duration(seconds: 180)),
    );
    return PhotoStyleResponse.fromJson(response.data!);
  }
}

/// `POST /api/diary/photo-style` 응답.
class PhotoStyleResponse {
  const PhotoStyleResponse({
    required this.type,
    required this.content,
    this.imageUrl,
  });

  final String type; // 'image_diary' | 'bot_text'
  final String content;
  final String? imageUrl;

  factory PhotoStyleResponse.fromJson(Map<String, dynamic> json) {
    return PhotoStyleResponse(
      type: json['type'] as String? ?? 'bot_text',
      content: json['content'] as String? ?? '',
      imageUrl: json['image_url'] as String?,
    );
  }
}
