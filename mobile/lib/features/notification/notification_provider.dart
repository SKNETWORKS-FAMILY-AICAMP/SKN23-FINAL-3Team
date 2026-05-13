import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../shared/models/app_notification.dart';

const _storageKey = 'app_notifications';
const _enabledKey = 'notifications_enabled';

/// 알림 전체 ON/OFF (SharedPreferences).
final notificationEnabledProvider =
    StateNotifierProvider<_EnabledNotifier, bool>((ref) {
  return _EnabledNotifier();
});

class _EnabledNotifier extends StateNotifier<bool> {
  _EnabledNotifier() : super(true) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getBool(_enabledKey) ?? true;
  }

  Future<void> toggle() async {
    state = !state;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_enabledKey, state);
  }
}

/// 알림 목록 관리.
final notificationProvider =
    StateNotifierProvider<NotificationNotifier, List<AppNotification>>((ref) {
  return NotificationNotifier(ref);
});

/// 읽지 않은 알림 수 (빨간 점 표시용).
final unreadCountProvider = Provider<int>((ref) {
  final notifications = ref.watch(notificationProvider);
  return notifications.where((n) => !n.isRead).length;
});

class NotificationNotifier extends StateNotifier<List<AppNotification>> {
  NotificationNotifier(this._ref) : super(const []) {
    _load();
  }

  final Ref _ref;

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_storageKey);
    if (raw != null && raw.isNotEmpty) {
      try {
        final list = AppNotification.decodeList(raw);
        // 7일 지난 알림 자동 삭제
        final cutoff = DateTime.now().subtract(const Duration(days: 7));
        state = list.where((n) => n.createdAt.isAfter(cutoff)).toList();
        await _save();
      } catch (_) {
        state = const [];
      }
    }
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, AppNotification.encodeList(state));
  }

  /// 알림 추가. 알림 설정이 OFF 이면 무시.
  Future<void> add(AppNotification notification) async {
    final enabled = _ref.read(notificationEnabledProvider);
    if (!enabled) return;
    state = [notification, ...state];
    await _save();
  }

  /// 편의 메서드 — type·title·body 로 알림 생성.
  Future<void> push({
    required NotificationType type,
    required String title,
    required String body,
  }) async {
    final n = AppNotification(
      id: '${DateTime.now().millisecondsSinceEpoch}_${type.index}',
      type: type,
      title: title,
      body: body,
      createdAt: DateTime.now(),
    );
    await add(n);
  }

  /// 전체 읽음 처리.
  Future<void> markAllRead() async {
    state = state.map((n) => n.copyWith(isRead: true)).toList();
    await _save();
  }

  /// 개별 읽음 처리.
  Future<void> markRead(String id) async {
    state = state.map((n) => n.id == id ? n.copyWith(isRead: true) : n).toList();
    await _save();
  }

  /// 전체 삭제.
  Future<void> clear() async {
    state = const [];
    await _save();
  }

  /// 일기 리마인더 체크 — 오늘 날짜로 이미 리마인더가 있으면 생략.
  Future<void> checkDiaryReminder() async {
    final enabled = _ref.read(notificationEnabledProvider);
    if (!enabled) return;

    final today = DateTime.now();
    final todayKey =
        '${today.year}-${today.month.toString().padLeft(2, '0')}-${today.day.toString().padLeft(2, '0')}';

    // 오늘 이미 리마인더가 있으면 스킵
    final hasToday = state.any(
      (n) =>
          n.type == NotificationType.diaryReminder &&
          n.createdAt.year == today.year &&
          n.createdAt.month == today.month &&
          n.createdAt.day == today.day,
    );
    if (hasToday) return;

    await push(
      type: NotificationType.diaryReminder,
      title: '오늘의 일기를 작성해보세요!',
      body: '반려견과 함께한 오늘 하루를 기록해보세요 🐾',
    );
  }
}
