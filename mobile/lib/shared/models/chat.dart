import 'place.dart';

/// 백엔드 `schemas/chat_room.py ChatRoomResponse` 와 1:1.
class ChatRoom {
  const ChatRoom({
    required this.id,
    required this.userId,
    this.title,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final int userId;
  final String? title;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory ChatRoom.fromJson(Map<String, dynamic> json) {
    return ChatRoom(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      title: json['title'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}

/// 백엔드 `schemas/chat_message.py MessageResponse` 와 1:1.
class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.roomId,
    required this.role,
    required this.content,
    required this.createdAt,
  });

  final int id;
  final int roomId;
  final String role; // 'user' | 'assistant' | 'system'
  final String content;
  final DateTime createdAt;

  bool get isUser => role == 'user';
  bool get isAssistant => role == 'assistant';

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as int,
      roomId: json['room_id'] as int,
      role: json['role'] as String,
      content: json['content'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

/// 백엔드 `IntentInfo`.
class IntentInfo {
  const IntentInfo({required this.intent, required this.confidence});

  final String intent; // '장소추천' | '시설정보' | '다이어리 작성'
  final double confidence;

  static const intentPlaces = '장소추천';
  static const intentFacility = '시설정보';
  static const intentDiary = '다이어리 작성';

  factory IntentInfo.fromJson(Map<String, dynamic> json) {
    return IntentInfo(
      intent: json['intent'] as String,
      confidence: (json['confidence'] as num).toDouble(),
    );
  }
}

/// `POST /api/chat-rooms/{id}/messages` 응답 (`ChatTurnResponse`).
class ChatTurn {
  const ChatTurn({
    required this.userMessage,
    required this.assistantMessage,
    required this.intent,
    this.facility,
    this.places,
  });

  final ChatMessage userMessage;
  final ChatMessage assistantMessage;
  final IntentInfo intent;
  final FacilityCard? facility;
  final List<PlaceCard>? places;

  factory ChatTurn.fromJson(Map<String, dynamic> json) {
    final placesJson = json['places'] as List<dynamic>?;
    return ChatTurn(
      userMessage: ChatMessage.fromJson(
        json['user_message'] as Map<String, dynamic>,
      ),
      assistantMessage: ChatMessage.fromJson(
        json['assistant_message'] as Map<String, dynamic>,
      ),
      intent: IntentInfo.fromJson(json['intent'] as Map<String, dynamic>),
      facility: json['facility'] == null
          ? null
          : FacilityCard.fromJson(json['facility'] as Map<String, dynamic>),
      places: placesJson?.cast<Map<String, dynamic>>().map(PlaceCard.fromJson).toList(),
    );
  }
}
