import 'package:flutter_riverpod/flutter_riverpod.dart';

/// HomeScreen BottomNavigationBar 탭 인덱스 — 0:홈 / 1:다이어리 / 2:지도 / 3:마이.
/// HomeTab 카드 / 알림 등 외부에서 탭 전환 트리거할 때 사용.
final homeTabIndexProvider = StateProvider<int>((_) => 0);
