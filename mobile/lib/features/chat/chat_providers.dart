import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/app_notification.dart';
import '../../shared/models/chat.dart';
import '../../shared/models/diary.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import '../diary/diary_ai_api.dart';
import '../diary/diary_draft_provider.dart';
import '../diary/diary_draft_state.dart';
import '../diary/diary_list_provider.dart';
import '../diary/diary_providers.dart';
import '../diary/diary_types.dart';
import '../notification/notification_provider.dart';
import '../onboarding/onboarding_providers.dart';
import 'chat_api.dart';
import 'chat_message_parser.dart';
import 'chat_state.dart';

final chatApiProvider = Provider<ChatApi>((ref) {
  return ChatApi(ref.watch(apiClientProvider));
});

/// 채팅방 목록 — Drawer 가 watch.
/// 인증 상태 변경 시 자동 invalidate.
final chatRoomsProvider = FutureProvider.autoDispose<List<ChatRoom>>((
  ref,
) async {
  final auth = ref.watch(authProvider);
  if (auth is! AuthAuthenticated) return const [];
  return ref.read(chatApiProvider).listRooms(auth.user.id);
});

/// 챗봇 상태 머신 — ChatScreen 의 단일 source.
class ChatNotifier extends StateNotifier<ChatState> {
  ChatNotifier(this._ref) : super(const ChatState());

  final Ref _ref;

  // ── 헬퍼 ──────────────────────────────────────────────────────────────────

  static const _acks = [
    '그렇군요 😊',
    '아, 그랬군요!',
    '좋아요!',
    '기억해둘게요 🤍',
    '소중한 순간이네요.',
  ];

  static String _randomAck() =>
      _acks[DateTime.now().millisecond % _acks.length];

  /// 추가 질문 2개 — 웹 useChatbot.ts additionalQuestions 동일 구조.
  static const _additionalQuestions = [
    '{petName}가 특별히 좋아하거나 재미있어 했던 순간이 있었나요?',
    '오늘 하루 중 가장 기억에 남는 장면을 하나 꼽는다면?',
  ];

  // ── 기본 채팅방 관리 ────────────────────────────────────────────────────────

  /// 새 대화 시작 — chatRoomId 비우고 messages 초기화.
  void resetForNewRoom() {
    state = const ChatState();
  }

  /// 기존 채팅방 로드 — Drawer 에서 방 선택 시.
  Future<void> openRoom(int roomId) async {
    state = ChatState(chatRoomId: roomId, messages: const [], isSending: true);
    try {
      final messages = await _ref.read(chatApiProvider).listMessages(roomId);
      state = state.copyWith(
        messages: messages.map(_toBubble).toList(),
        isSending: false,
      );
    } catch (e) {
      state = state.copyWith(isSending: false, error: '메시지 로드 실패: $e');
    }
  }

  ChatBubble _toBubble(ChatMessage m) {
    final parsed = ChatMessageParser.parse(m.content);
    return ChatBubble(role: m.role, text: parsed.text, buttons: parsed.buttons);
  }

  // ── 자유채팅 (welcome 단계) ─────────────────────────────────────────────────

  /// user 메시지 송신 → POST chat-rooms (첫 메시지) / POST messages → ChatTurn 파싱.
  Future<ChatTurnOutcome> sendUserMessage(String text, {int? petId}) async {
    if (text.trim().isEmpty) return ChatTurnOutcome.empty;
    final api = _ref.read(chatApiProvider);

    // 1. 채팅방 보장 (첫 user 메시지면 신규 생성)
    int roomId;
    if (state.chatRoomId == null) {
      try {
        final preview = text.length > 30 ? text.substring(0, 30) : text;
        final room = await api.createRoom(title: preview);
        roomId = room.id;
        state = state.copyWith(chatRoomId: roomId);
        _ref.invalidate(chatRoomsProvider);
      } catch (e) {
        state = state.copyWith(error: '채팅방 생성 실패: $e');
        return ChatTurnOutcome.failed;
      }
    } else {
      roomId = state.chatRoomId!;
    }

    // 2. user 버블 즉시 추가
    final userBubble = ChatBubble(role: 'user', text: text);
    state = state.copyWith(
      messages: [...state.messages, userBubble],
      isSending: true,
      error: null,
    );

    // 3. 한 턴 처리
    try {
      final turn = await api.sendMessage(
        roomId: roomId,
        content: text,
        petId: petId,
      );

      // 트리거 단독 메시지 — 충분한 일기 내용 여부 판단 후 로컬 버블 처리.
      // "일기 쓰기" 버튼은 chat_screen 에서 가로채 triggerDiaryFlow() 호출.
      if (ChatMessageParser.isDiaryTrigger(turn.assistantMessage.content)) {
        final ChatBubble assistantBubble;
        if (_hasSufficientDiaryContent(state.messages)) {
          // 충분한 경험 내용 → 일기 작성 확인 버튼
          assistantBubble = const ChatBubble(
            role: 'assistant',
            text: '위 내용을 기반으로 일기를 써드릴까요?',
            buttons: ['일기 쓰기', '일기 새로 쓰기'],
          );
        } else {
          // 내용 부족 → 추가 질문만 출력
          assistantBubble = const ChatBubble(
            role: 'assistant',
            text: '오늘 어떤 일이 있었나요? '
                '장소, 있었던 일, 느꼈던 감정이나 반려견의 반응을 '
                '조금 더 이야기해주세요 😊',
          );
        }
        state = state.copyWith(
          messages: [...state.messages, assistantBubble],
          isSending: false,
          intent: turn.intent,
        );
        return ChatTurnOutcome.normal;
      }

      final parsed = ChatMessageParser.parse(turn.assistantMessage.content);
      final assistantBubble = ChatBubble(
        role: 'assistant',
        text: parsed.text,
        buttons: parsed.buttons,
        places: turn.places,
        facility: turn.facility,
      );
      state = state.copyWith(
        messages: [...state.messages, assistantBubble],
        isSending: false,
        intent: turn.intent,
      );
      return ChatTurnOutcome.normal;
    } catch (e) {
      state = state.copyWith(isSending: false, error: '응답 생성 실패: $e');
      return ChatTurnOutcome.failed;
    }
  }

  /// 챗봇이 띄운 인라인 버튼 클릭 — 같은 텍스트로 sendUserMessage 호출.
  Future<ChatTurnOutcome> tapButton(String label, {int? petId}) {
    return sendUserMessage(label, petId: petId);
  }

  // ── 채팅방 관리 ────────────────────────────────────────────────────────────

  /// 채팅방 삭제 (Drawer 에서).
  Future<void> deleteRoom(int roomId) async {
    await _ref.read(chatApiProvider).deleteRoom(roomId);
    _ref.invalidate(chatRoomsProvider);
    if (state.chatRoomId == roomId) resetForNewRoom();
  }

  /// 채팅방 이름 변경.
  Future<void> renameRoom(int roomId, String title) async {
    await _ref.read(chatApiProvider).renameRoom(roomId, title);
    _ref.invalidate(chatRoomsProvider);
  }

  // ── 다이어리 미니 플로우 ─────────────────────────────────────────────────────
  //
  // 웹 useChatbot.ts 의 START_DIARY → SELECT_DIARY_TYPE → SUBMIT_MAIN_ANSWER
  // → SELECT_EMOTION → SET_DIARY 흐름을 모바일 ChatNotifier 에 1:1 구현.
  // 백엔드 LLM / 이미지 생성 / 저장 로직은 diary_ai_api 를 직접 호출.

  /// [그림일기] 퀵칩 클릭 — 유형 선택 진입 (user 버블 포함).
  void startDiaryFlow(String petName) {
    state = state.copyWith(
      phase: ChatPhase.typeSelect,
      selectedDiaryType: null,
      currentQuestionIndex: 0,
      mainAnswers: const [],
      additionalAnswers: const [],
      selectedEmotion: null,
      generatedDiary: null,
      imageBase64: null,
      imageUrl: null,
      diaryAutoSaved: false,
      contextPlace: null,
      messages: [
        ...state.messages,
        const ChatBubble(role: 'user', text: '그림일기 쓸게요 📝'),
        ChatBubble(
          role: 'assistant',
          text: '$petName의 오늘 하루를 어떤 유형으로 기록할까요?',
        ),
      ],
    );
  }

  /// 사진 일러스트 → 일기 작성 플로우 진입 (photoStyleImageUrl 유지).
  void startPhotoDiaryFlow(String petName) {
    state = state.copyWith(
      phase: ChatPhase.typeSelect,
      selectedDiaryType: null,
      currentQuestionIndex: 0,
      mainAnswers: const [],
      additionalAnswers: const [],
      selectedEmotion: null,
      generatedDiary: null,
      imageBase64: null,
      imageUrl: null,
      diaryAutoSaved: false,
      // photoStyleImageUrl 은 copyWith 기본값으로 유지됨
      messages: [
        ...state.messages,
        const ChatBubble(role: 'user', text: '응 일기 쓸래'),
        ChatBubble(
          role: 'assistant',
          text: '$petName의 오늘 하루를 어떤 유형으로 기록할까요?',
        ),
      ],
    );
  }

  /// 장소 카드에서 진입 — 장소 컨텍스트 메시지 + 유형 선택.
  void startDiaryFlowWithPlace(String petName, PlaceCard place) {
    state = state.copyWith(
      phase: ChatPhase.typeSelect,
      selectedDiaryType: null,
      currentQuestionIndex: 0,
      mainAnswers: const [],
      additionalAnswers: const [],
      selectedEmotion: null,
      generatedDiary: null,
      imageBase64: null,
      imageUrl: null,
      diaryAutoSaved: false,
      contextPlace: place,
      messages: [
        ...state.messages,
        ChatBubble(role: 'user', text: '${place.name}에서 일기 쓸게요 📝'),
        ChatBubble(
          role: 'assistant',
          text:
              '${place.name}에서 반려견과 함께한 시간을 그림일기로 기록할까요?\n\n'
              '$petName의 오늘 하루를 어떤 유형으로 기록할까요?',
        ),
      ],
    );
  }

  /// "일기 쓰기" 버튼 (자유채팅 내용 충분) — 유형 선택 진입 (user 버블 없음).
  void triggerDiaryFlow(String petName) {
    state = state.copyWith(
      phase: ChatPhase.typeSelect,
      selectedDiaryType: null,
      currentQuestionIndex: 0,
      mainAnswers: const [],
      additionalAnswers: const [],
      selectedEmotion: null,
      generatedDiary: null,
      imageBase64: null,
      imageUrl: null,
      diaryAutoSaved: false,
      messages: [
        ...state.messages,
        ChatBubble(
          role: 'assistant',
          text: '$petName의 오늘 하루를 어떤 유형으로 기록할까요?',
        ),
      ],
    );
  }

  /// 다이어리 유형 선택.
  void selectDiaryType(DiaryType type, String petName) {
    final firstQ = type.questions[0].replaceAll('{petName}', petName);
    state = state.copyWith(
      phase: ChatPhase.mainQuestions,
      selectedDiaryType: type,
      currentQuestionIndex: 0,
      mainAnswers: List.filled(type.questions.length, ''),
      messages: [
        ...state.messages,
        ChatBubble(role: 'user', text: '${type.icon} ${type.label}'),
        ChatBubble(
          role: 'assistant',
          text: '좋아요! ${type.description}으로 기록해볼게요 😊\n\n$firstQ',
        ),
      ],
    );
  }

  /// 메인 질문 답변 제출 — 모든 질문 완료 시 감정 선택으로 이동.
  void submitMainAnswer(String answer, String petName) {
    final type = state.selectedDiaryType;
    if (type == null) return;

    final newAnswers = List<String>.from(state.mainAnswers);
    final idx = state.currentQuestionIndex;
    // 장소 컨텍스트가 있으면 첫 답변에 장소명 포함
    final enriched = (idx == 0 && state.contextPlace != null)
        ? '오늘은 ${state.contextPlace!.name}에 다녀왔어요. $answer'
        : answer;
    if (idx < newAnswers.length) newAnswers[idx] = enriched;

    final nextIdx = idx + 1;

    if (nextIdx < type.questions.length) {
      // 다음 질문
      final nextQ = type.questions[nextIdx].replaceAll('{petName}', petName);
      state = state.copyWith(
        currentQuestionIndex: nextIdx,
        mainAnswers: newAnswers,
        messages: [
          ...state.messages,
          ChatBubble(role: 'user', text: answer),
          ChatBubble(
            role: 'assistant',
            text: '${_randomAck()}\n\n$nextQ',
          ),
        ],
      );
    } else {
      // 모든 질문 완료 → 추가 질문 여부 확인
      state = state.copyWith(
        phase: ChatPhase.additionalPrompt,
        mainAnswers: newAnswers,
        messages: [
          ...state.messages,
          ChatBubble(role: 'user', text: answer),
          const ChatBubble(
            role: 'assistant',
            text: '혹시 오늘 있었던 일을 조금 더 들려줄까요?',
          ),
        ],
      );
    }
  }

  /// 추가 질문 Y/N 응답.
  void respondToAdditionalPrompt(bool accepted, String petName) {
    if (accepted) {
      // 추가 질문 시작
      final firstQ =
          _additionalQuestions[0].replaceAll('{petName}', petName);
      state = state.copyWith(
        phase: ChatPhase.additionalQuestions,
        currentQuestionIndex: 0,
        additionalAnswers:
            List.filled(_additionalQuestions.length, ''),
        messages: [
          ...state.messages,
          const ChatBubble(role: 'user', text: '네, 좋아요!'),
          ChatBubble(role: 'assistant', text: firstQ),
        ],
      );
    } else {
      // 추가 질문 건너뛰기 → 감정 선택
      state = state.copyWith(
        phase: ChatPhase.emotionSelect,
        messages: [
          ...state.messages,
          const ChatBubble(role: 'user', text: '괜찮아요'),
          ChatBubble(
            role: 'assistant',
            text:
                '좋아요! ✨\n\n오늘 $petName의 하루는 어떤 감정으로 기억하고 싶으세요?',
          ),
        ],
      );
    }
  }

  /// 추가 질문 답변 제출.
  void submitAdditionalAnswer(String answer, String petName) {
    final newAnswers = List<String>.from(state.additionalAnswers);
    final idx = state.currentQuestionIndex;
    if (idx < newAnswers.length) newAnswers[idx] = answer;

    final nextIdx = idx + 1;

    if (nextIdx < _additionalQuestions.length) {
      final nextQ =
          _additionalQuestions[nextIdx].replaceAll('{petName}', petName);
      state = state.copyWith(
        currentQuestionIndex: nextIdx,
        additionalAnswers: newAnswers,
        messages: [
          ...state.messages,
          ChatBubble(role: 'user', text: answer),
          ChatBubble(role: 'assistant', text: '${_randomAck()}\n\n$nextQ'),
        ],
      );
    } else {
      // 모든 추가 질문 완료 → 감정 선택
      state = state.copyWith(
        phase: ChatPhase.emotionSelect,
        additionalAnswers: newAnswers,
        messages: [
          ...state.messages,
          ChatBubble(role: 'user', text: answer),
          ChatBubble(
            role: 'assistant',
            text:
                '잘 기록됐어요! ✨\n\n오늘 $petName의 하루는 어떤 감정으로 기억하고 싶으세요?',
          ),
        ],
      );
    }
  }

  /// 감정 선택 → `POST /api/diary/generate` 호출 → 결과 표시.
  Future<void> selectDiaryEmotion(
    DiaryEmotion emotion,
    String petName,
  ) async {
    final type = state.selectedDiaryType;
    if (type == null) return;

    // 감정 선택 버블 + 생성 중 메시지
    state = state.copyWith(
      phase: ChatPhase.diaryGenerating,
      selectedEmotion: emotion,
      isSending: true,
      messages: [
        ...state.messages,
        ChatBubble(role: 'user', text: '${emotion.emoji} ${emotion.label}'),
        ChatBubble(
          role: 'assistant',
          text: '${emotion.emoji} 느낌으로 $petName의 일기를 쓰고 있어요... ✍️\n잠깐만 기다려주세요!',
        ),
      ],
    );

    // 반려견 정보 조회
    final auth = _ref.read(authProvider);
    if (auth is! AuthAuthenticated || auth.user.primaryPet == null) {
      state = state.copyWith(
        phase: ChatPhase.emotionSelect,
        isSending: false,
        error: '대표 반려견을 먼저 등록해주세요.',
      );
      return;
    }
    final pet = auth.user.primaryPet!;

    // API 호출 — 텍스트 일기만 생성 (그림은 별도 단계)
    try {
      final api = _ref.read(diaryAiApiProvider);
      final result = await api.generate(
        DiaryGenerateRequest(
          petId: pet.id.toString(),
          petName: pet.name,
          ownerName: auth.user.nickname,
          mainAnswers: state.mainAnswers,
          additionalAnswers: state.additionalAnswers,
          diaryType: type.id,
          emotionEmoji: emotion.emoji,
          englishPrompt: pet.englishPrompt,
          mustIncludeKeywords: pet.mustIncludeKeywords ?? const [],
        ),
      );

      final generated = DiaryDraftGenerated(
        title: result.title,
        content: result.content,
        summary: result.summary,
        imagePrompt: result.imagePrompt,
        sessionId: result.sessionId,
      );

      // textDiaryResult — 텍스트 일기만 표시, "그림일기로 만들어줘" / "일기 다시 쓰고싶어" 버튼
      state = state.copyWith(
        phase: ChatPhase.textDiaryResult,
        isSending: false,
        generatedDiary: generated,
        messages: [
          ...state.messages,
          ChatBubble(role: 'assistant', text: '$petName의 일기가 완성됐어요 📖'),
          ChatBubble(
            role: 'assistant',
            text: '📖 ${result.title}\n\n${result.content}',
          ),
        ],
      );
    } catch (e) {
      state = state.copyWith(
        phase: ChatPhase.emotionSelect,
        isSending: false,
        error: '일기 생성 중 오류가 발생했어요. 다시 시도해주세요.',
        messages: [
          ...state.messages,
          const ChatBubble(
            role: 'assistant',
            text: '일기 생성 중 오류가 발생했어요 😢 감정을 다시 선택해주세요.',
          ),
        ],
      );
    }
  }

  /// 그림 생성 — `textDiaryResult` 단계에서 호출.
  /// 그림 완성 → `diaryResult` 로 전환 (저장 버튼 표시).
  Future<void> generateDiaryImageInChat() async {
    final generated = state.generatedDiary;
    if (generated == null) return;

    state = state.copyWith(
      isSending: true,
      error: null,
      messages: [
        ...state.messages,
        const ChatBubble(role: 'user', text: '그림일기로 만들어줘'),
        const ChatBubble(
          role: 'assistant',
          text: '그림을 그리고 있어요... 🎨\n잠깐만 기다려주세요!',
        ),
      ],
    );
    try {
      final api = _ref.read(diaryAiApiProvider);
      final base64 = await api.generateImage(
        imagePrompt: generated.imagePrompt,
        sessionId: generated.sessionId,
      );
      _ref.read(notificationProvider.notifier).push(
            type: NotificationType.imageGenerated,
            title: '그림이 완성됐어요!',
            body: '그림일기 이미지가 생성됐어요 🎨',
          );

      state = state.copyWith(
        phase: ChatPhase.diaryResult,
        isSending: false,
        imageBase64: base64,
        messages: [
          ...state.messages,
          const ChatBubble(role: 'assistant', text: '그림이 완성됐어요! 🎨'),
        ],
      );
    } catch (e) {
      state = state.copyWith(
        isSending: false,
        error: '이미지 생성 실패. 다시 시도해주세요.',
      );
    }
  }

  /// 일기 저장 — `POST /api/diaries`.
  Future<bool> saveDiaryFromChat() async {
    final generated = state.generatedDiary;
    if (generated == null) return false;

    final auth = _ref.read(authProvider);
    if (auth is! AuthAuthenticated) return false;
    final pet = auth.user.primaryPet;
    if (pet == null) return false;

    state = state.copyWith(isSending: true, error: null);
    try {
      // 이미지가 있으면 먼저 업로드
      int? imageId;
      if (state.imageBase64 != null) {
        final imageApi = _ref.read(imageApiProvider);
        final uploaded = await imageApi.uploadBase64Png(
          base64Data: state.imageBase64!,
          filename: 'diary_${DateTime.now().millisecondsSinceEpoch}.png',
        );
        imageId = uploaded.id;
      } else if (state.photoStyleImageUrl != null) {
        // 사진 일러스트 URL → 다운로드 후 업로드하여 imageId 획득
        final imageApi = _ref.read(imageApiProvider);
        final uploaded = await imageApi.uploadFromUrl(
          state.photoStyleImageUrl!,
        );
        imageId = uploaded.id;
      }

      await _ref.read(diaryApiProvider).create(
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

      _ref.invalidate(favoriteCalendarProvider);
      _ref.invalidate(diaryListProvider);

      _ref.read(notificationProvider.notifier).push(
            type: NotificationType.diarySaved,
            title: '일기가 저장됐어요!',
            body: '${generated.title} — 다이어리에서 확인해보세요 📔',
          );

      state = state.copyWith(
        isSending: false,
        contextPlace: null,
        messages: [
          ...state.messages,
          const ChatBubble(
            role: 'assistant',
            text: '일기가 저장됐어요! 다이어리에서 확인해보세요 📔',
          ),
        ],
      );
      return true;
    } catch (e) {
      state = state.copyWith(
        isSending: false,
        error: '저장 실패: $e',
      );
      return false;
    }
  }

  // ── 자유채팅 → 그림일기 생성 (백엔드 자동 저장) ─────────────────────────────

  /// 자유채팅 흐름에서 "그림일기로 만들어줘" 인라인 버튼 클릭 시 호출.
  ///
  /// 1. 이전 assistant 메시지에서 일기 텍스트 파싱
  /// 2. 백엔드 sendMessage 호출 (서버가 이미지 생성 + 자동 저장)
  /// 3. 응답에서 이미지 URL 추출
  /// 4. phase → diaryResult 전환 (diaryAutoSaved = true)
  Future<void> sendDiaryImageRequest({int? petId}) async {
    final roomId = state.chatRoomId;
    if (roomId == null) return;

    // 이전 메시지에서 일기 텍스트 파싱
    final diary = _parseDiaryFromMessages();

    state = state.copyWith(
      generatedDiary: diary,
      isSending: true,
      error: null,
      messages: [
        ...state.messages,
        const ChatBubble(role: 'user', text: '그림일기로 만들어줘'),
        const ChatBubble(
          role: 'assistant',
          text: '그림을 그리고 있어요... 🎨\n잠깐만 기다려주세요!',
        ),
      ],
    );

    try {
      final api = _ref.read(chatApiProvider);
      final turn = await api.sendMessage(
        roomId: roomId,
        content: '그림일기로 만들어줘',
        petId: petId,
      );

      final imageUrl = _extractImageUrl(turn.assistantMessage.content);
      // 파싱 실패 시 응답 텍스트에서 재시도
      final finalDiary = diary ?? _parseDiaryFromText(
        turn.assistantMessage.content,
      );

      // 백엔드 자동 저장 완료 → 다이어리 목록·캘린더 갱신
      _ref.invalidate(favoriteCalendarProvider);
      _ref.invalidate(diaryListProvider);

      state = state.copyWith(
        phase: ChatPhase.diaryResult,
        isSending: false,
        generatedDiary: finalDiary,
        imageUrl: imageUrl,
        diaryAutoSaved: true,
        contextPlace: null,
        messages: [
          ...state.messages,
          const ChatBubble(role: 'assistant', text: '그림이 완성됐어요! 🎨'),
        ],
      );
    } catch (e) {
      state = state.copyWith(
        isSending: false,
        error: '이미지 생성 실패: $e',
      );
    }
  }

  /// assistant 메시지들에서 `📖 **제목**\n\n내용` 형태의 일기 텍스트를 파싱.
  DiaryDraftGenerated? _parseDiaryFromMessages() {
    // 최근 assistant 메시지 중 📖 가 포함된 것을 역순 탐색
    for (int i = state.messages.length - 1; i >= 0; i--) {
      final m = state.messages[i];
      if (!m.isAssistant) continue;
      final result = _parseDiaryFromText(m.text);
      if (result != null) return result;
    }
    return null;
  }

  /// 단일 텍스트에서 일기 제목/내용/요약 파싱.
  static DiaryDraftGenerated? _parseDiaryFromText(String text) {
    // 📖 **제목** 또는 📖 제목 패턴
    final titleRegex = RegExp(r'📖\s*\*{0,2}(.+?)\*{0,2}\s*$', multiLine: true);
    final titleMatch = titleRegex.firstMatch(text);
    if (titleMatch == null) return null;

    final title = titleMatch.group(1)!.trim();
    final afterTitle = text.substring(titleMatch.end).trim();

    // _요약_: 로 구분
    String content;
    String summary = '';
    final summaryIdx = afterTitle.indexOf('_요약_:');
    if (summaryIdx != -1) {
      content = afterTitle.substring(0, summaryIdx).trim();
      final summaryLine = afterTitle.substring(summaryIdx + '_요약_:'.length);
      summary = summaryLine.split('\n').first.trim();
    } else {
      // 요약이 없으면 마지막 안내 문구 전까지
      final guideIdx = afterTitle.indexOf('마음에 드세요?');
      content = guideIdx != -1
          ? afterTitle.substring(0, guideIdx).trim()
          : afterTitle.trim();
    }

    // image markdown 제거
    content = content.replaceAll(
      RegExp(r'!\[.*?\]\(https?://[^\)]+\)'),
      '',
    ).trim();

    if (title.isEmpty || content.isEmpty) return null;

    return DiaryDraftGenerated(
      title: title,
      content: content,
      summary: summary,
      imagePrompt: '',
      sessionId: '',
    );
  }

  /// 응답 텍스트에서 `![alt](url)` 형태의 이미지 URL 추출.
  static String? _extractImageUrl(String text) {
    final match = RegExp(r'!\[.*?\]\((https?://[^\)]+)\)').firstMatch(text);
    return match?.group(1);
  }

  // ── 사진 → 일러스트 변환 (photo-style) ──────────────────────────────────────

  /// 이미지 파일을 `POST /api/diary/photo-style` 로 전송하여 일러스트로 변환.
  /// 채팅 화면 이미지 버튼에서 호출.
  Future<void> sendPhotoStyle(String filePath) async {
    // user 버블: 촬영/선택한 이미지 로컬 경로
    final userBubble = ChatBubble(
      role: 'user',
      text: '![사진](file://$filePath)',
    );
    state = state.copyWith(
      isSending: true,
      error: null,
      messages: [
        ...state.messages,
        userBubble,
        const ChatBubble(
          role: 'assistant',
          text: '사진을 일러스트로 변환하고 있어요... 🎨\n잠깐만 기다려주세요!',
        ),
      ],
    );

    try {
      final api = _ref.read(diaryAiApiProvider);
      final auth = _ref.read(authProvider);
      final petId = auth is AuthAuthenticated
          ? auth.user.primaryPetId ?? auth.user.primaryPet?.id
          : null;

      final result = await api.photoStyle(
        filePath: filePath,
        chatRoomId: state.chatRoomId,
        dogId: petId,
      );

      // 결과 표시
      final assistantText = result.imageUrl != null
          ? '${result.content}\n\n![일러스트](${result.imageUrl})'
          : result.content;

      _ref.read(notificationProvider.notifier).push(
            type: NotificationType.photoStyleDone,
            title: '사진이 일러스트로 변환됐어요!',
            body: '채팅에서 결과를 확인해보세요 🎨',
          );

      final newMessages = <ChatBubble>[
        ChatBubble(role: 'assistant', text: assistantText),
      ];

      // 일러스트 변환 성공 시 일기 작성 제안
      if (result.imageUrl != null) {
        newMessages.add(const ChatBubble(
          role: 'assistant',
          text: '사진을 그림으로 변환했어요!\n이 그림을 토대로 일기를 쓸까요?',
          buttons: ['응 일기 쓸래'],
        ));
      }

      state = state.copyWith(
        isSending: false,
        photoStyleImageUrl: result.imageUrl,
        messages: [...state.messages, ...newMessages],
      );
    } catch (e) {
      state = state.copyWith(
        isSending: false,
        error: '사진 변환 실패: $e',
        messages: [
          ...state.messages,
          const ChatBubble(
            role: 'assistant',
            text: '사진 변환 중 오류가 발생했어요 😢 다시 시도해주세요.',
          ),
        ],
      );
    }
  }

  /// 다이어리 다시 쓰기 — 유형 선택으로 복귀.
  void restartDiaryFlow(String petName) {
    state = state.copyWith(
      phase: ChatPhase.typeSelect,
      selectedDiaryType: null,
      currentQuestionIndex: 0,
      mainAnswers: const [],
      additionalAnswers: const [],
      selectedEmotion: null,
      generatedDiary: null,
      imageBase64: null,
      imageUrl: null,
      diaryAutoSaved: false,
      contextPlace: null,
      messages: [
        ...state.messages,
        const ChatBubble(role: 'user', text: '일기 다시 쓸게요'),
        ChatBubble(
          role: 'assistant',
          text: '$petName의 오늘 하루를 어떤 유형으로 기록할까요?',
        ),
      ],
    );
  }

  // ── 일기 내용 충분 여부 판단 ─────────────────────────────────────────────────
  //
  // 기준: user 메시지에서 단순 요청·장소 조회 문장을 제외한 뒤,
  //       장소/배경·행동/활동·감정/느낌·반려견 반응 중 2개 이상 검출.
  static bool _hasSufficientDiaryContent(List<ChatBubble> messages) {
    final userTexts = messages
        .where((m) => m.isUser)
        .map((m) => m.text.trim())
        .where((t) => t.isNotEmpty)
        .toList();

    if (userTexts.isEmpty) return false;

    final simpleTrigger = RegExp(
      r'^(오늘\s*)?(그림)?일기\s*(써\s*줘?|작성|부탁|써줄래).*',
    );
    final queryRequest = RegExp(
      r'(추천해|알려줘|어디야|어디있|영업시간|몇\s*시|운영|주소|전화|예약|얼마|리뷰|평점|찾아줘|검색)',
    );

    final meaningful = userTexts.where((t) {
      if (t.length <= 5) return false;
      if (simpleTrigger.hasMatch(t)) return false;
      if (queryRequest.hasMatch(t)) return false;
      return true;
    }).toList();

    if (meaningful.isEmpty) return false;

    final combined = meaningful.join(' ');
    int score = 0;

    if (RegExp(
      r'(공원|카페|산책|마트|병원|펫샵|호텔|식당|해변|강|산|놀이터|에서\s|갔다|다녀왔|방문|도착)',
    ).hasMatch(combined)) { score++; }

    if (RegExp(
      r'(뛰었|뛰어|놀았|달렸|수영|먹었|했어|했는데|했다|했고|보냈|보내|뒹굴|앉았|누웠)',
    ).hasMatch(combined)) { score++; }

    if (RegExp(
      r'(좋았|신났|행복|즐거|재미있|슬프|무서|신기|귀여|뿌듯|기뻤|힘들|피곤|설레|걱정|기분|좋아했|싫어했)',
    ).hasMatch(combined)) { score++; }

    if (RegExp(
      r'(강아지|멍이|반려견|꼬리|짖|핥|물었|안겼|뛰어다|무서워했|신나했|졸았|냄새\s*맡|탐색|놀았)',
    ).hasMatch(combined)) { score++; }

    return score >= 2;
  }
}

enum ChatTurnOutcome {
  normal,
  triggerDiary, // 하위 호환 — 현재는 sendUserMessage 내부에서 처리
  empty,
  failed,
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  return ChatNotifier(ref);
});

/// 홈 미니 챗봇에서 입력한 텍스트를 챗봇 탭 입력창에 전달하기 위한 provider.
final pendingChatTextProvider = StateProvider<String?>((_) => null);

/// 지도탭 장소 카드 → 챗봇 일기 작성 플로우 진입을 위한 provider.
final pendingPlaceProvider = StateProvider<PlaceCard?>((_) => null);
