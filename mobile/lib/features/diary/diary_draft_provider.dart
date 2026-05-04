import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/diary.dart';
import '../../shared/models/pet.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import '../onboarding/onboarding_providers.dart';
import 'diary_ai_api.dart';
import 'diary_draft_state.dart';
import 'diary_providers.dart';
import 'diary_types.dart';

/// DioException → 사람이 읽을 수 있는 에러 메시지. 백엔드 HTTPException detail
/// 우선, 없으면 dio 에러 type + message.
String _formatDioError(Object err, String prefix) {
  if (err is DioException) {
    final detail = err.response?.data is Map
        ? (err.response!.data as Map)['detail']?.toString()
        : null;
    final code = err.response?.statusCode;
    if (detail != null) return '$prefix ($code): $detail';
    return '$prefix: ${err.type.name} ${err.message ?? ''}';
  }
  return '$prefix: $err';
}

final diaryAiApiProvider = Provider<DiaryAiApi>((ref) {
  return DiaryAiApi(ref.watch(apiClientProvider));
});

class DiaryDraftNotifier extends StateNotifier<DiaryDraftState> {
  DiaryDraftNotifier(this._ref) : super(const DiaryDraftState());

  final Ref _ref;

  void start({DiaryType? type, PlaceCard? place}) {
    state = DiaryDraftState(
      phase: type == null ? DiaryDraftPhase.typeSelect : DiaryDraftPhase.mainQuestions,
      diaryType: type,
      mainAnswers: type == null ? const [] : List.filled(type.questions.length, ''),
      contextPlace: place,
    );
  }

  void selectType(DiaryType type) {
    state = state.copyWith(
      phase: DiaryDraftPhase.mainQuestions,
      diaryType: type,
      mainAnswers: List.filled(type.questions.length, ''),
    );
  }

  void setAnswer(int index, String value) {
    final updated = [...state.mainAnswers];
    if (index < 0 || index >= updated.length) return;
    updated[index] = value;
    state = state.copyWith(mainAnswers: updated);
  }

  void goEmotion() {
    if (!state.hasAnswered) return;
    state = state.copyWith(phase: DiaryDraftPhase.emotionSelect);
  }

  void selectEmotion(DiaryEmotion emotion) {
    state = state.copyWith(selectedEmotion: emotion);
  }

  /// AI 생성 (텍스트 + 이미지 base64) — `/diary/generate` → `/diary/generate-image`.
  Future<void> generate() async {
    final type = state.diaryType;
    final emotion = state.selectedEmotion;
    if (type == null || emotion == null) return;

    final auth = _ref.read(authProvider);
    Pet? pet;
    if (auth is AuthAuthenticated) {
      pet = auth.user.primaryPet;
    }
    if (pet == null) {
      state = state.copyWith(error: '대표 반려견을 먼저 등록해주세요.');
      return;
    }

    state = state.copyWith(phase: DiaryDraftPhase.generating, error: null);
    try {
      final aiApi = _ref.read(diaryAiApiProvider);
      final answers = [...state.mainAnswers];
      // 외부 진입 (장소 카드) — where 슬롯 자동 채우기
      if (state.contextPlace != null) {
        answers.add('오늘은 ${state.contextPlace!.name}에 다녀왔어요.');
      }
      final generated = await aiApi.generate(
        DiaryGenerateRequest(
          petId: pet.id.toString(),
          petName: pet.name,
          mainAnswers: answers,
          diaryType: type.id,
          emotionEmoji: emotion.emoji,
        ),
      );
      state = state.copyWith(
        generated: DiaryDraftGenerated(
          title: generated.title,
          content: generated.content,
          summary: generated.summary,
          imagePrompt: generated.imagePrompt,
          sessionId: generated.sessionId,
        ),
        phase: DiaryDraftPhase.result,
      );

      // 이미지는 별도 트리거 — 사용자가 "그림 그리기" 버튼 누를 때.
      // (React 의 generate-image 도 별도 액션)
    } catch (e) {
      state = state.copyWith(
        phase: DiaryDraftPhase.mainQuestions,
        error: _formatDioError(e, '생성 실패'),
      );
    }
  }

  /// 이미지 생성 — `result` 단계에서 호출. base64 저장.
  Future<void> generateImage() async {
    final generated = state.generated;
    if (generated == null) return;
    state = state.copyWith(phase: DiaryDraftPhase.generating, error: null);
    try {
      final aiApi = _ref.read(diaryAiApiProvider);
      final base64 = await aiApi.generateImage(
        imagePrompt: generated.imagePrompt,
        sessionId: generated.sessionId,
      );
      state = state.copyWith(
        imageBase64: base64,
        phase: DiaryDraftPhase.result,
      );
    } catch (e) {
      state = state.copyWith(
        phase: DiaryDraftPhase.result,
        error: _formatDioError(e, '이미지 생성 실패'),
      );
    }
  }

  /// 최종 저장 — POST /images (이미지 있으면) → POST /diaries (image_id 바인딩).
  Future<bool> saveDiary() async {
    final auth = _ref.read(authProvider);
    if (auth is! AuthAuthenticated) {
      state = state.copyWith(error: '로그인이 필요합니다.');
      return false;
    }
    final pet = auth.user.primaryPet;
    if (pet == null) {
      state = state.copyWith(error: '대표 반려견이 필요합니다.');
      return false;
    }
    final generated = state.generated;
    if (generated == null) return false;

    state = state.copyWith(phase: DiaryDraftPhase.saving, error: null);
    try {
      int? imageId;
      if (state.imageBase64 != null) {
        final imageApi = _ref.read(imageApiProvider);
        final uploaded = await imageApi.uploadBase64Png(
          base64Data: state.imageBase64!,
          filename: 'diary_${DateTime.now().millisecondsSinceEpoch}.png',
        );
        imageId = uploaded.id;
      }

      final diary = await _ref.read(diaryApiProvider).create(
            DiaryCreate(
              petId: pet.id,
              title: generated.title,
              content: generated.content,
              summary: generated.summary,
              emotion: state.selectedEmotion?.emoji,
              imageId: imageId,
              whereText: state.contextPlace?.name,
            ),
          );
      state = state.copyWith(
        savedDiary: diary,
        phase: DiaryDraftPhase.saved,
      );
      // 캘린더·목록 invalidate
      _ref.invalidate(favoriteCalendarProvider);
      return true;
    } catch (e) {
      state = state.copyWith(
        phase: DiaryDraftPhase.result,
        error: _formatDioError(e, '저장 실패'),
      );
      return false;
    }
  }

  void reset() {
    state = const DiaryDraftState();
  }
}

final diaryDraftProvider =
    StateNotifierProvider.autoDispose<DiaryDraftNotifier, DiaryDraftState>(
        (ref) {
  return DiaryDraftNotifier(ref);
});
