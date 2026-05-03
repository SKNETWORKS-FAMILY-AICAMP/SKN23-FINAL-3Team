import '../../core/api/api_client.dart';
import '../../shared/models/chat.dart';

class ChatApi {
  const ChatApi(this._client);

  final ApiClient _client;

  /// `POST /api/chat-rooms`
  Future<ChatRoom> createRoom({String? title}) async {
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/chat-rooms',
      data: {'title': title},
    );
    return ChatRoom.fromJson(response.data!);
  }

  /// `GET /api/chat-rooms?user_id={id}`
  Future<List<ChatRoom>> listRooms(int userId) async {
    final response = await _client.raw.get<List<dynamic>>(
      '/chat-rooms',
      queryParameters: {'user_id': userId},
    );
    return (response.data ?? const [])
        .cast<Map<String, dynamic>>()
        .map(ChatRoom.fromJson)
        .toList();
  }

  /// `GET /api/chat-rooms/{id}`
  Future<ChatRoom> getRoom(int roomId) async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/chat-rooms/$roomId',
    );
    return ChatRoom.fromJson(response.data!);
  }

  /// `PATCH /api/chat-rooms/{id}/title`
  Future<ChatRoom> renameRoom(int roomId, String title) async {
    final response = await _client.raw.patch<Map<String, dynamic>>(
      '/chat-rooms/$roomId/title',
      data: {'title': title},
    );
    return ChatRoom.fromJson(response.data!);
  }

  /// `DELETE /api/chat-rooms/{id}` (soft delete, 메시지는 보존)
  Future<void> deleteRoom(int roomId) async {
    await _client.raw.delete('/chat-rooms/$roomId');
  }

  /// `POST /api/chat-rooms/{id}/messages` — 의도분류 + 응답 한 턴 처리
  Future<ChatTurn> sendMessage({
    required int roomId,
    required String content,
    int? petId,
  }) async {
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/chat-rooms/$roomId/messages',
      data: {
        'role': 'user',
        'content': content,
        // ignore: use_null_aware_elements
        if (petId != null) 'pet_id': petId,
      },
    );
    return ChatTurn.fromJson(response.data!);
  }

  /// `GET /api/chat-rooms/{id}/messages` — 전체 (또는 `?last_n=`)
  Future<List<ChatMessage>> listMessages(int roomId, {int? lastN}) async {
    final response = await _client.raw.get<List<dynamic>>(
      '/chat-rooms/$roomId/messages',
      queryParameters: lastN == null ? null : {'last_n': lastN},
    );
    return (response.data ?? const [])
        .cast<Map<String, dynamic>>()
        .map(ChatMessage.fromJson)
        .toList();
  }
}
