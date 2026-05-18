import '../../shared/models/chat.dart';
import '../../shared/models/place.dart';
import '../diary/diary_draft_state.dart';
import '../diary/diary_types.dart';

/// 챗봇 상태 머신 — `useChatbot.ts` 의 8 단계 1:1.
/// 장소추천·시설정보 분기는 의도분류 결과로 갈라짐 (단계 X, 응답 카드만 다름).
enum ChatPhase {
  /// 자유 채팅 입력 가능 — 의도 분류 후 분기.
  welcome,

  /// 다이어리 작성 진입 — 일기 유형 4종 선택.
  typeSelect,

  /// 메인 질문 (3~4개) 답변 입력.
  mainQuestions,

  /// 추가 질문 진행 여부 (Y/N).
  additionalPrompt,

  /// 추가 질문 (선택, 2개) 답변 입력.
  additionalQuestions,

  /// 텍스트 일기 생성 완료 — "그림일기로 만들어줘" / "일기 다시 쓰고싶어" 선택.
  textDiaryResult,

  /// 감정 12종 선택.
  emotionSelect,

  /// `POST /api/diary/generate` 진행 중.
  diaryGenerating,

  /// 결과 표시 — 그림 생성·저장 버튼.
  diaryResult,
}

/// UI 가 그릴 메시지 — wire `ChatMessage` 위에 카드·버튼 메타 추가.
class ChatBubble {
  const ChatBubble({
    required this.role,
    required this.text,
    this.buttons = const [],
    this.places,
    this.facility,
    this.isPending = false,
  });

  final String role; // 'user' | 'assistant'
  final String text;
  final List<String> buttons; // %%BUTTONS%% 인라인 칩
  final List<PlaceCard>? places;
  final FacilityCard? facility;
  final bool isPending;

  bool get isUser => role == 'user';
  bool get isAssistant => role == 'assistant';

  ChatBubble copyWith({
    String? role,
    String? text,
    List<String>? buttons,
    List<PlaceCard>? places,
    FacilityCard? facility,
    bool? isPending,
  }) {
    return ChatBubble(
      role: role ?? this.role,
      text: text ?? this.text,
      buttons: buttons ?? this.buttons,
      places: places ?? this.places,
      facility: facility ?? this.facility,
      isPending: isPending ?? this.isPending,
    );
  }
}

class ChatState {
  const ChatState({
    this.phase = ChatPhase.welcome,
    this.chatRoomId,
    this.messages = const [],
    this.isSending = false,
    this.error,
    this.intent,
    // ── 다이어리 미니 플로우 ──────────────────────────────────
    this.selectedDiaryType,
    this.currentQuestionIndex = 0,
    this.mainAnswers = const [],
    this.additionalAnswers = const [],
    this.selectedEmotion,
    this.generatedDiary,
    this.imageBase64,
    this.imageUrl,
    this.diaryAutoSaved = false,
    this.photoStyleImageUrl,
    this.contextPlace,
  });

  final ChatPhase phase;
  final int? chatRoomId;
  final List<ChatBubble> messages;
  final bool isSending;
  final String? error;
  final IntentInfo? intent;
  // diary mini-flow
  final DiaryType? selectedDiaryType;
  final int currentQuestionIndex;
  final List<String> mainAnswers;
  final List<String> additionalAnswers;
  final DiaryEmotion? selectedEmotion;
  final DiaryDraftGenerated? generatedDiary;
  final String? imageBase64;
  /// 자유채팅 일기에서 백엔드가 반환한 이미지 URL (base64 대신).
  final String? imageUrl;
  /// 백엔드가 자동 저장했는지 여부 (자유채팅 다이어리 플로우).
  final bool diaryAutoSaved;
  /// 사진 → 일러스트 변환 결과 URL (사진 일기 플로우용).
  final String? photoStyleImageUrl;
  /// 장소 카드에서 진입 시 장소 컨텍스트.
  final PlaceCard? contextPlace;

  ChatState copyWith({
    ChatPhase? phase,
    int? chatRoomId,
    List<ChatBubble>? messages,
    bool? isSending,
    Object? error = const _Sentinel(),
    Object? intent = const _Sentinel(),
    Object? selectedDiaryType = const _Sentinel(),
    int? currentQuestionIndex,
    List<String>? mainAnswers,
    List<String>? additionalAnswers,
    Object? selectedEmotion = const _Sentinel(),
    Object? generatedDiary = const _Sentinel(),
    Object? imageBase64 = const _Sentinel(),
    Object? imageUrl = const _Sentinel(),
    bool? diaryAutoSaved,
    Object? photoStyleImageUrl = const _Sentinel(),
    Object? contextPlace = const _Sentinel(),
  }) {
    return ChatState(
      phase: phase ?? this.phase,
      chatRoomId: chatRoomId ?? this.chatRoomId,
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      error: error is _Sentinel ? this.error : error as String?,
      intent: intent is _Sentinel ? this.intent : intent as IntentInfo?,
      selectedDiaryType: selectedDiaryType is _Sentinel
          ? this.selectedDiaryType
          : selectedDiaryType as DiaryType?,
      currentQuestionIndex:
          currentQuestionIndex ?? this.currentQuestionIndex,
      mainAnswers: mainAnswers ?? this.mainAnswers,
      additionalAnswers: additionalAnswers ?? this.additionalAnswers,
      selectedEmotion: selectedEmotion is _Sentinel
          ? this.selectedEmotion
          : selectedEmotion as DiaryEmotion?,
      generatedDiary: generatedDiary is _Sentinel
          ? this.generatedDiary
          : generatedDiary as DiaryDraftGenerated?,
      imageBase64: imageBase64 is _Sentinel
          ? this.imageBase64
          : imageBase64 as String?,
      imageUrl: imageUrl is _Sentinel
          ? this.imageUrl
          : imageUrl as String?,
      diaryAutoSaved: diaryAutoSaved ?? this.diaryAutoSaved,
      photoStyleImageUrl: photoStyleImageUrl is _Sentinel
          ? this.photoStyleImageUrl
          : photoStyleImageUrl as String?,
      contextPlace: contextPlace is _Sentinel
          ? this.contextPlace
          : contextPlace as PlaceCard?,
    );
  }
}

class _Sentinel {
  const _Sentinel();
}
