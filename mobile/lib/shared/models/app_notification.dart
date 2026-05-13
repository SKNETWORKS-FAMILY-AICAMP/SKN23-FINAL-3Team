import 'dart:convert';

enum NotificationType {
  diaryReminder,
  diarySaved,
  imageGenerated,
  favoriteAdded,
  photoStyleDone,
}

class AppNotification {
  const AppNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.createdAt,
    this.isRead = false,
  });

  final String id;
  final NotificationType type;
  final String title;
  final String body;
  final DateTime createdAt;
  final bool isRead;

  AppNotification copyWith({bool? isRead}) {
    return AppNotification(
      id: id,
      type: type,
      title: title,
      body: body,
      createdAt: createdAt,
      isRead: isRead ?? this.isRead,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type.index,
        'title': title,
        'body': body,
        'createdAt': createdAt.toIso8601String(),
        'isRead': isRead,
      };

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as String,
      type: NotificationType.values[json['type'] as int],
      title: json['title'] as String,
      body: json['body'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      isRead: json['isRead'] as bool? ?? false,
    );
  }

  static String encodeList(List<AppNotification> list) =>
      jsonEncode(list.map((n) => n.toJson()).toList());

  static List<AppNotification> decodeList(String source) {
    final decoded = jsonDecode(source) as List<dynamic>;
    return decoded
        .cast<Map<String, dynamic>>()
        .map(AppNotification.fromJson)
        .toList();
  }
}
