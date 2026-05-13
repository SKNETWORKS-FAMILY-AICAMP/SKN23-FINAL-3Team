import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../calendar/diary_tab.dart';
import '../chat/chat_screen.dart';
import '../intro/intro_screen.dart';
import '../mypage/mypage_tab.dart';
import '../places/map_tab.dart';
import 'home_tab.dart';
import 'home_tab_index.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  static const _tabs = <Widget>[
    HomeTab(),
    DiaryTab(),
    MapTab(),
    MyPageTab(),
    ChatScreen(),
  ];

  bool _introShown = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_introShown) {
      _introShown = true;
      final introCompleted = ref.read(introCompletedProvider);
      if (!introCompleted) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) showIntroDialog(context);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final index = ref.watch(homeTabIndexProvider);
    // 키보드 높이: 키보드가 올라오면 바텀 네비 전체를 같은 높이만큼 위로 이동
    final keyboardHeight = MediaQuery.of(context).viewInsets.bottom;

    return Scaffold(
      // false: 키보드 대응을 HomeScreen이 직접 처리 (이중 리사이즈 방지)
      resizeToAvoidBottomInset: false,
      body: Column(
        children: [
          Expanded(
            child: IndexedStack(
              index: index,
              children: _tabs,
            ),
          ),
          // 키보드 높이만큼 bottom padding → 네비바 전체가 키보드 위로 올라옴
          AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            curve: Curves.easeOut,
            padding: EdgeInsets.only(bottom: keyboardHeight),
            child: _WithDogBottomNav(
              selectedIndex: index,
              onSelected: (i) {
                ref.read(homeTabIndexProvider.notifier).state = i;
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ── 커스텀 바텀 네비 (챗봇 버튼 내장) ───────────────────────────────────────────

class _WithDogBottomNav extends StatelessWidget {
  const _WithDogBottomNav({
    required this.selectedIndex,
    required this.onSelected,
  });

  final int selectedIndex;
  final ValueChanged<int> onSelected;

  // 챗봇 버튼 지름 — Row 중앙 gap 과 Positioned 위치 계산에 사용
  static const double _chatBtnSize = 100;
  // 챗봇 버튼이 네비바 위로 올라오는 픽셀
  static const double _chatBtnRise = 34;

  @override
  Widget build(BuildContext context) {
    return Stack(
      // clipBehavior.none: 챗봇 버튼이 네비바 위로 삐져나와도 clip 하지 않음
      clipBehavior: Clip.none,
      children: [
        // ── 흰색 네비바 ─────────────────────────────────────────────
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.08),
                blurRadius: 14,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: SafeArea(
            top: false, // 시스템 제스처바 영역만 padding 추가
            child: SizedBox(
              height: 72,
              child: Row(
                children: [
                  Expanded(
                    child: _BottomNavItem(
                      icon: LucideIcons.home,
                      label: '홈',
                      selected: selectedIndex == 0,
                      onTap: () => onSelected(0),
                    ),
                  ),
                  Expanded(
                    child: _BottomNavItem(
                      icon: LucideIcons.bookOpen,
                      label: '일기',
                      selected: selectedIndex == 1,
                      onTap: () => onSelected(1),
                    ),
                  ),
                  // 챗봇 버튼 자리 비워두기
                  const SizedBox(width: _chatBtnSize + 16),
                  Expanded(
                    child: _BottomNavItem(
                      icon: LucideIcons.mapPin,
                      label: '지도',
                      selected: selectedIndex == 2,
                      onTap: () => onSelected(2),
                    ),
                  ),
                  Expanded(
                    child: _BottomNavItem(
                      icon: LucideIcons.user,
                      label: '마이',
                      selected: selectedIndex == 3,
                      onTap: () => onSelected(3),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        // ── 챗봇 버튼: 네비바 위로 _chatBtnRise 만큼 돌출 ────────────
        Positioned(
          top: -_chatBtnRise,
          left: 0,
          right: 0,
          child: Center(
            child: _CenterChatButton(
              active: selectedIndex == 4,
              onTap: () => onSelected(4),
            ),
          ),
        ),
      ],
    );
  }
}

// ── 챗봇 중앙 버튼 ─────────────────────────────────────────────────────────────

class _CenterChatButton extends StatefulWidget {
  const _CenterChatButton({required this.onTap, this.active = false});

  final VoidCallback onTap;
  final bool active;

  @override
  State<_CenterChatButton> createState() => _CenterChatButtonState();
}

class _CenterChatButtonState extends State<_CenterChatButton>
    with SingleTickerProviderStateMixin {
  static const double _size = 100;

  late final AnimationController _ctrl;
  late final Animation<double> _bounce;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    // 0 → 8px 아래로 → 0 (바운스)
    _bounce = TweenSequence<double>([
      TweenSequenceItem(tween: Tween(begin: 0, end: 8), weight: 40),
      TweenSequenceItem(tween: Tween(begin: 8, end: -3), weight: 30),
      TweenSequenceItem(tween: Tween(begin: -3, end: 0), weight: 30),
    ]).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _handleTap() {
    _ctrl.forward(from: 0);
    widget.onTap();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _handleTap,
      child: AnimatedBuilder(
        animation: _ctrl,
        builder: (context, child) => Transform.translate(
          offset: Offset(0, _bounce.value),
          child: child,
        ),
        child: Container(
          width: _size,
          height: _size,
          decoration: const BoxDecoration(
            color: Colors.transparent,
            shape: BoxShape.circle,
          ),
          child: Image.asset(
            'assets/icon/chatbot_logo.png',
            width: _size,
            height: _size,
            fit: BoxFit.contain,
            errorBuilder: (context2, e, s) => const Icon(
              LucideIcons.messageCircle,
              color: Colors.white,
              size: 30,
            ),
          ),
        ),
      ),
    );
  }
}

// ── 네비 아이템 ────────────────────────────────────────────────────────────────

class _BottomNavItem extends StatelessWidget {
  const _BottomNavItem({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppColors.brandOrange : const Color(0xFF737385);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            width: selected ? 44 : 34,
            height: 30,
            decoration: BoxDecoration(
              color: selected ? AppColors.brandOrange : Colors.transparent,
              borderRadius: BorderRadius.circular(99),
            ),
            alignment: Alignment.center,
            child: Icon(icon, size: 21, color: selected ? Colors.white : color),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: color,
              fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
