import '../../core/api/api_client.dart';
import '../../shared/models/diary.dart';

class DiaryApi {
  const DiaryApi(this._client);

  final ApiClient _client;

  /// `POST /api/diaries`
  Future<Diary> create(DiaryCreate data) async {
    final response = await _client.raw.post<Map<String, dynamic>>(
      '/diaries',
      data: data.toJson(),
    );
    return Diary.fromJson(response.data!);
  }

  /// `GET /api/diaries?user_id={id}` (옵션 `&pet_id=`)
  Future<List<Diary>> listByUser({required int userId, int? petId}) async {
    final response = await _client.raw.get<List<dynamic>>(
      '/diaries',
      queryParameters: {
        'user_id': userId,
        // ignore: use_null_aware_elements
        if (petId != null) 'pet_id': petId,
      },
    );
    return (response.data ?? const [])
        .cast<Map<String, dynamic>>()
        .map(Diary.fromJson)
        .toList();
  }

  /// `GET /api/diaries/{id}`
  Future<Diary> get(int diaryId) async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/diaries/$diaryId',
    );
    return Diary.fromJson(response.data!);
  }

  /// `PATCH /api/diaries/{id}` — image_id 바인딩 등
  Future<Diary> update(int diaryId, DiaryUpdate data) async {
    final response = await _client.raw.patch<Map<String, dynamic>>(
      '/diaries/$diaryId',
      data: data.toJson(),
    );
    return Diary.fromJson(response.data!);
  }

  /// `PATCH /api/diaries/{id}/favorite` — atomic SWAP, 같은 날짜 기존 즐겨찾기 자동 해제
  Future<Diary> toggleFavorite(int diaryId) async {
    final response = await _client.raw.patch<Map<String, dynamic>>(
      '/diaries/$diaryId/favorite',
    );
    return Diary.fromJson(response.data!);
  }

  /// `DELETE /api/diaries/{id}` (soft delete)
  Future<void> delete(int diaryId) async {
    await _client.raw.delete('/diaries/$diaryId');
  }

  /// `GET /api/diaries/calendar?year=&month=` (5/2 신규)
  /// 즐겨찾기 일기 한 달치 셀 페이로드 (date / diary_id / emotion)
  Future<FavoriteCalendar> calendar({
    required int year,
    required int month,
  }) async {
    final response = await _client.raw.get<Map<String, dynamic>>(
      '/diaries/calendar',
      queryParameters: {'year': year, 'month': month},
    );
    return FavoriteCalendar.fromJson(response.data!);
  }
}
