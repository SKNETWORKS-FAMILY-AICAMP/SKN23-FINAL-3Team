/// 백엔드 `schemas/diary.py DiaryResponse` 와 1:1.
class Diary {
  const Diary({
    required this.id,
    required this.userId,
    required this.petId,
    this.imageId,
    this.whenText,
    this.whereText,
    this.whoText,
    this.whatText,
    this.howText,
    this.whyText,
    this.title,
    this.content,
    this.summary,
    this.emotion,
    required this.diaryDate,
    required this.isFavorite,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final int userId;
  final int petId;
  final int? imageId;
  final String? whenText;
  final String? whereText;
  final String? whoText;
  final String? whatText;
  final String? howText;
  final String? whyText;
  final String? title;
  final String? content;
  final String? summary;
  final String? emotion;
  final DateTime diaryDate;
  final bool isFavorite;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory Diary.fromJson(Map<String, dynamic> json) {
    // 배포 백엔드 (2026-05-04 기준 stale) 가 5/2 신규 필드 (`diary_date`,
    // `is_favorite`) 를 아직 미포함 → 누락 시 `created_at` 의 날짜 부분으로
    // 폴백, `is_favorite` 는 false 로 폴백. 백엔드 재배포 후 자연 동작.
    final createdAtStr = json['created_at'] as String?;
    final updatedAtStr = json['updated_at'] as String?;
    final diaryDateStr = json['diary_date'] as String?;
    final fallbackDate = createdAtStr != null
        ? DateTime.parse(createdAtStr)
        : DateTime.now();
    return Diary(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      petId: json['pet_id'] as int,
      imageId: json['image_id'] as int?,
      whenText: json['when_text'] as String?,
      whereText: json['where_text'] as String?,
      whoText: json['who_text'] as String?,
      whatText: json['what_text'] as String?,
      howText: json['how_text'] as String?,
      whyText: json['why_text'] as String?,
      title: json['title'] as String?,
      content: json['content'] as String?,
      summary: json['summary'] as String?,
      emotion: json['emotion'] as String?,
      diaryDate: diaryDateStr != null
          ? DateTime.parse(diaryDateStr)
          : fallbackDate,
      isFavorite: json['is_favorite'] as bool? ?? false,
      createdAt: fallbackDate,
      updatedAt: updatedAtStr != null
          ? DateTime.parse(updatedAtStr)
          : fallbackDate,
    );
  }
}

/// `POST /api/diaries` 페이로드 (`DiaryCreate`).
class DiaryCreate {
  const DiaryCreate({
    required this.petId,
    this.whenText,
    this.whereText,
    this.whoText,
    this.whatText,
    this.howText,
    this.whyText,
    this.title,
    this.content,
    this.summary,
    this.emotion,
    this.imageId,
    this.diaryDate,
  });

  final int petId;
  final String? whenText;
  final String? whereText;
  final String? whoText;
  final String? whatText;
  final String? howText;
  final String? whyText;
  final String? title;
  final String? content;
  final String? summary;
  final String? emotion;
  final int? imageId;
  final DateTime? diaryDate;

  Map<String, dynamic> toJson() => {
    'pet_id': petId,
    if (whenText != null) 'when_text': whenText,
    if (whereText != null) 'where_text': whereText,
    if (whoText != null) 'who_text': whoText,
    if (whatText != null) 'what_text': whatText,
    if (howText != null) 'how_text': howText,
    if (whyText != null) 'why_text': whyText,
    if (title != null) 'title': title,
    if (content != null) 'content': content,
    if (summary != null) 'summary': summary,
    if (emotion != null) 'emotion': emotion,
    if (imageId != null) 'image_id': imageId,
    if (diaryDate != null) 'diary_date': _formatDate(diaryDate!),
  };
}

/// `PATCH /api/diaries/{id}` 페이로드 (`DiaryUpdate`).
class DiaryUpdate {
  const DiaryUpdate({
    this.title,
    this.content,
    this.summary,
    this.emotion,
    this.imageId,
    this.diaryDate,
  });

  final String? title;
  final String? content;
  final String? summary;
  final String? emotion;
  final int? imageId;
  final DateTime? diaryDate;

  Map<String, dynamic> toJson() => {
    if (title != null) 'title': title,
    if (content != null) 'content': content,
    if (summary != null) 'summary': summary,
    if (emotion != null) 'emotion': emotion,
    if (imageId != null) 'image_id': imageId,
    if (diaryDate != null) 'diary_date': _formatDate(diaryDate!),
  };
}

/// `GET /api/diaries/calendar?year=&month=` 응답 (`FavoriteCalendarResponse`).
class FavoriteCalendar {
  const FavoriteCalendar({
    required this.year,
    required this.month,
    required this.items,
  });

  final int year;
  final int month;
  final List<FavoriteCalendarItem> items;

  factory FavoriteCalendar.fromJson(Map<String, dynamic> json) {
    final items =
        (json['items'] as List<dynamic>?)
            ?.cast<Map<String, dynamic>>()
            .map(FavoriteCalendarItem.fromJson)
            .toList() ??
        const [];
    return FavoriteCalendar(
      year: json['year'] as int,
      month: json['month'] as int,
      items: items,
    );
  }
}

class FavoriteCalendarItem {
  const FavoriteCalendarItem({
    required this.date,
    required this.diaryId,
    required this.emotion,
  });

  final DateTime date;
  final int diaryId;
  final String emotion;

  factory FavoriteCalendarItem.fromJson(Map<String, dynamic> json) {
    return FavoriteCalendarItem(
      date: DateTime.parse(json['date'] as String),
      diaryId: json['diary_id'] as int,
      emotion: json['emotion'] as String? ?? '',
    );
  }
}

String _formatDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
