import 'package:dio/dio.dart';

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
}
