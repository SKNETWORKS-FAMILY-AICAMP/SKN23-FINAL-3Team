import '../../shared/models/chat.dart';
import '../../shared/models/place.dart';

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

  /// 감정 6종 선택.
  emotionSelect,

  /// `POST /api/diary/generate` 진행 중.
  diaryGenerating,

  /// 결과 표시 — 이미지 생성 버튼 등.
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
  });

  final ChatPhase phase;
  final int? chatRoomId;
  final List<ChatBubble> messages;
  final bool isSending;
  final String? error;
  final IntentInfo? intent;

  ChatState copyWith({
    ChatPhase? phase,
    int? chatRoomId,
    List<ChatBubble>? messages,
    bool? isSending,
    Object? error = const _Sentinel(),
    Object? intent = const _Sentinel(),
  }) {
    return ChatState(
      phase: phase ?? this.phase,
      chatRoomId: chatRoomId ?? this.chatRoomId,
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      error: error is _Sentinel ? this.error : error as String?,
      intent: intent is _Sentinel ? this.intent : intent as IntentInfo?,
    );
  }
}

class _Sentinel {
  const _Sentinel();
}
