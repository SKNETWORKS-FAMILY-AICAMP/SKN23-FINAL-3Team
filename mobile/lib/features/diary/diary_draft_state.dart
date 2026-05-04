import '../../shared/models/diary.dart';
import '../../shared/models/place.dart';
import 'diary_types.dart';

/// 다이어리 작성 단계 — React `useChatbot.ts` 8단계의 mobile 단순화 버전.
///
/// 1차 동작 우선: 풀 챗봇 단계는 보류, 핵심 흐름만:
///   typeSelect → mainQuestions → emotionSelect → generating → result
enum DiaryDraftPhase {
  typeSelect, // 다이어리 유형 4종 선택
  mainQuestions, // 유형별 질문 답변 입력
  emotionSelect, // 감정 12종 선택
  generating, // POST /diary/generate (텍스트) + /diary/generate-image (이미지)
  result, // 생성 결과 미리보기
  saving, // POST /images + POST /diaries
  saved, // 완료 — DiaryTab 으로 회귀
}

class DiaryDraftState {
  const DiaryDraftState({
    this.phase = DiaryDraftPhase.typeSelect,
    this.diaryType,
    this.mainAnswers = const [],
    this.selectedEmotion,
    this.generated,
    this.imageBase64,
    this.savedDiary,
    this.error,
    this.contextPlace,
  });

  final DiaryDraftPhase phase;
  final DiaryType? diaryType;
  final List<String> mainAnswers;
  final DiaryEmotion? selectedEmotion;
  final DiaryDraftGenerated? generated;
  final String? imageBase64;
  final Diary? savedDiary;
  final String? error;

  /// 외부 진입 시 (장소 카드 → "이 장소로 일기 쓰기") 전달되는 컨텍스트.
  /// 챗봇 진입 시 null. PlaceCard 의 `name` 을 `where_text` 슬롯에 자동 채움.
  final PlaceCard? contextPlace;

  bool get hasAnswered =>
      mainAnswers.length == (diaryType?.questions.length ?? 0) &&
      mainAnswers.every((a) => a.trim().isNotEmpty);

  DiaryDraftState copyWith({
    DiaryDraftPhase? phase,
    DiaryType? diaryType,
    List<String>? mainAnswers,
    DiaryEmotion? selectedEmotion,
    DiaryDraftGenerated? generated,
    String? imageBase64,
    Diary? savedDiary,
    Object? error = const _Sentinel(),
    PlaceCard? contextPlace,
  }) {
    return DiaryDraftState(
      phase: phase ?? this.phase,
      diaryType: diaryType ?? this.diaryType,
      mainAnswers: mainAnswers ?? this.mainAnswers,
      selectedEmotion: selectedEmotion ?? this.selectedEmotion,
      generated: generated ?? this.generated,
      imageBase64: imageBase64 ?? this.imageBase64,
      savedDiary: savedDiary ?? this.savedDiary,
      error: error is _Sentinel ? this.error : error as String?,
      contextPlace: contextPlace ?? this.contextPlace,
    );
  }
}

/// 생성 결과 (텍스트만, 이미지는 별도 base64).
class DiaryDraftGenerated {
  const DiaryDraftGenerated({
    required this.title,
    required this.content,
    required this.summary,
    required this.imagePrompt,
    required this.sessionId,
  });

  final String title;
  final String content;
  final String summary;
  final String imagePrompt;
  final String sessionId;
}

class _Sentinel {
  const _Sentinel();
}
