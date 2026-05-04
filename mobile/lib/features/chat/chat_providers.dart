import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/chat.dart';
import '../auth/auth_providers.dart';
import 'chat_api.dart';
import 'chat_message_parser.dart';
import 'chat_state.dart';

final chatApiProvider = Provider<ChatApi>((ref) {
  return ChatApi(ref.watch(apiClientProvider));
});

/// 채팅방 목록 — Drawer 가 watch.
/// 인증 상태 변경 시 자동 invalidate.
final chatRoomsProvider = FutureProvider.autoDispose<List<ChatRoom>>((ref) async {
  final auth = ref.watch(authProvider);
  if (auth is! AuthAuthenticated) return const [];
  return ref.read(chatApiProvider).listRooms(auth.user.id);
});

/// 챗봇 상태 머신 — ChatScreen 의 단일 source.
class ChatNotifier extends StateNotifier<ChatState> {
  ChatNotifier(this._ref) : super(const ChatState());

  final Ref _ref;

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
    return ChatBubble(
      role: m.role,
      text: parsed.text,
      buttons: parsed.buttons,
    );
  }

  /// user 메시지 송신 → POST chat-rooms (첫 메시지) / POST messages → ChatTurn 파싱.
  ///
  /// 백엔드 반환의 `assistant_message.content` 가 `%%TRIGGER:START_DIARY%%` 면
  /// 다이어리 작성 흐름 시작 트리거 (Step 2-C 에서 본격 구현). 본 메서드는
  /// 트리거 여부를 결과로 반환 — 호출자가 라우팅·UI 분기 결정.
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
        // Drawer 목록 갱신 (다음 빌드)
        _ref.invalidate(chatRoomsProvider);
      } catch (e) {
        state = state.copyWith(error: '채팅방 생성 실패: $e');
        return ChatTurnOutcome.failed;
      }
    } else {
      roomId = state.chatRoomId!;
    }

    // 2. user 버블 즉시 추가 (네트워크 응답 전 UI 반영)
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
      // 트리거 단독 메시지 — 사용자에게 텍스트 노출 X
      if (ChatMessageParser.isDiaryTrigger(turn.assistantMessage.content)) {
        state = state.copyWith(isSending: false, intent: turn.intent);
        return ChatTurnOutcome.triggerDiary;
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
      state = state.copyWith(
        isSending: false,
        error: '응답 생성 실패: $e',
      );
      return ChatTurnOutcome.failed;
    }
  }

  /// 챗봇이 띄운 인라인 버튼 클릭 — 같은 텍스트로 sendUserMessage 호출.
  Future<ChatTurnOutcome> tapButton(String label, {int? petId}) {
    return sendUserMessage(label, petId: petId);
  }

  /// 채팅방 삭제 (Drawer 에서).
  Future<void> deleteRoom(int roomId) async {
    await _ref.read(chatApiProvider).deleteRoom(roomId);
    _ref.invalidate(chatRoomsProvider);
    if (state.chatRoomId == roomId) {
      resetForNewRoom();
    }
  }

  /// 채팅방 이름 변경.
  Future<void> renameRoom(int roomId, String title) async {
    await _ref.read(chatApiProvider).renameRoom(roomId, title);
    _ref.invalidate(chatRoomsProvider);
  }
}

enum ChatTurnOutcome {
  normal,
  triggerDiary, // %%TRIGGER:START_DIARY%% — Step 2-C 다이어리 작성 진입
  empty,
  failed,
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  return ChatNotifier(ref);
});
