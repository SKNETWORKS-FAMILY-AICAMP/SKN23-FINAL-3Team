import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:video_player/video_player.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import '../auth/auth_providers.dart';
import '../chat/chat_providers.dart';
import '../diary/diary_list_provider.dart';
import '../notification/notification_provider.dart';
import '../notification/notification_sheet.dart';
import '../places/map_focus_provider.dart';
import '../places/place_providers.dart';
import 'home_tab_index.dart';
import 'widgets/weekly_diary_calendar.dart';

class HomeTab extends ConsumerStatefulWidget {
  const HomeTab({super.key});

  @override
  ConsumerState<HomeTab> createState() => _HomeTabState();
}

const _diaryTabIndex = 1;
const _mapTabIndex = 2;
const _myTabIndex = 3;
const _chatTabIndex = 4;

class _HomeTabState extends ConsumerState<HomeTab> {
  static const int _initialBannerPage = 999;

  final PageController _bannerPageController = PageController(
    initialPage: _initialBannerPage,
  );

  final List<_IntroBannerData> _banners = const [
    _IntroBannerData(
      videoPath: 'assets/videos/intro_fixed.mp4',
      buttonText: '대화하기',
      target: _IntroBannerTarget.chat,
    ),
    _IntroBannerData(
      videoPath: 'assets/videos/intro2_fixed.mp4',
      buttonText: '그림 일기 보러가기',
      target: _IntroBannerTarget.diary,
    ),
    _IntroBannerData(
      videoPath: 'assets/videos/intro3_fixed.mp4',
      buttonText: '장소 추천',
      target: _IntroBannerTarget.map,
    ),
  ];

  late final List<VideoPlayerController> _videoControllers;

  int _currentBannerPage = _initialBannerPage;
  int _currentBannerIndex = 0;

  bool _videosReady = false;
  bool _videoFailed = false;
  String? _videoErrorMessage;

  @override
  void initState() {
    super.initState();

    _currentBannerIndex = _initialBannerPage % _banners.length;

    _videoControllers = _banners
        .map((banner) => VideoPlayerController.asset(banner.videoPath))
        .toList();

    _initVideos();
  }

  Future<void> _initVideos() async {
    try {
      for (int i = 0; i < _videoControllers.length; i++) {
        final controller = _videoControllers[i];
        final path = _banners[i].videoPath;

        debugPrint('홈 배너 영상 로드 시도: $path');

        await controller.initialize();
        await controller.setLooping(true);
        await controller.setVolume(0);

        debugPrint(
          '홈 배너 영상 로드 성공: $path / '
              '${controller.value.size.width}x${controller.value.size.height}',
        );
      }

      if (!mounted) return;

      setState(() {
        _videosReady = true;
        _videoFailed = false;
        _videoErrorMessage = null;
      });

      _playOnly(_currentBannerIndex);
    } catch (error, stackTrace) {
      debugPrint('홈 배너 영상 로드 실패: $error');
      debugPrintStack(stackTrace: stackTrace);

      if (!mounted) return;

      setState(() {
        _videosReady = false;
        _videoFailed = true;
        _videoErrorMessage = error.toString();
      });
    }
  }

  void _playOnly(int index) {
    for (int i = 0; i < _videoControllers.length; i++) {
      final controller = _videoControllers[i];

      if (!controller.value.isInitialized) continue;

      if (i == index) {
        controller.play();
      } else {
        controller.pause();
        controller.seekTo(Duration.zero);
      }
    }
  }

  void _switchTab(int index) {
    ref.read(homeTabIndexProvider.notifier).state = index;
  }

  void _onBannerChanged(int page) {
    final realIndex = page % _banners.length;

    setState(() {
      _currentBannerPage = page;
      _currentBannerIndex = realIndex;
    });

    _playOnly(realIndex);
  }

  void _onBannerButtonTap(_IntroBannerTarget target) {
    final auth = ref.read(authProvider);
    if (auth is! AuthAuthenticated) {
      _switchTab(_myTabIndex);
      return;
    }
    switch (target) {
      case _IntroBannerTarget.chat:
        _switchTab(_chatTabIndex);
        break;
      case _IntroBannerTarget.map:
        _switchTab(_mapTabIndex);
        break;
      case _IntroBannerTarget.diary:
        _switchTab(_diaryTabIndex);
        break;
    }
  }

  @override
  void dispose() {
    for (final controller in _videoControllers) {
      controller.dispose();
    }

    _bannerPageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final authenticated = auth is AuthAuthenticated;

    return SafeArea(
      child: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(favoritePlacesProvider);
          ref.invalidate(diaryListProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 110),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _HomeLogoHeader(),
              const SizedBox(height: 10),
              _IntroVideoCarousel(
                banners: _banners,
                controllers: _videoControllers,
                pageController: _bannerPageController,
                currentPage: _currentBannerPage,
                currentIndex: _currentBannerIndex,
                videosReady: _videosReady,
                videoFailed: _videoFailed,
                videoErrorMessage: _videoErrorMessage,
                onPageChanged: _onBannerChanged,
                onButtonTap: _onBannerButtonTap,
              ),
              const SizedBox(height: 16),
              _QuickChatBar(
                onSend: (text) {
                  // 챗봇 입력창에 텍스트 전달 후 탭 이동
                  ref.read(pendingChatTextProvider.notifier).state = text;
                  _switchTab(_chatTabIndex);
                },
              ),
              const SizedBox(height: 16),
              const WeeklyDiaryCalendar(),
              const SizedBox(height: 16),
              _QuickMenuGrid(
                authenticated: authenticated,
                onPlaceTap: authenticated
                    ? () => _switchTab(_mapTabIndex)
                    : () => _switchTab(_myTabIndex),
                onDiaryTap: authenticated
                    ? () => _switchTab(_diaryTabIndex)
                    : () => _switchTab(_myTabIndex),
                // 비로그인도 챗봇 진입 허용 — 화면 안에서 잠금 UI 표시
                onChatTap: () => _switchTab(_chatTabIndex),
                onMyTap: () => _switchTab(_myTabIndex),
              ),
              const SizedBox(height: 26),
              const _FavoritePlacesPreviewSection(),
            ],
          ),
        ),
      ),
    );
  }
}

enum _IntroBannerTarget {
  chat,
  map,
  diary,
}

class _IntroBannerData {
  const _IntroBannerData({
    required this.videoPath,
    required this.buttonText,
    required this.target,
  });

  final String videoPath;
  final String buttonText;
  final _IntroBannerTarget target;
}

class _HomeLogoHeader extends ConsumerWidget {
  const _HomeLogoHeader();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final unreadCount = ref.watch(unreadCountProvider);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: Row(
        children: [
          // 왼쪽 균형용 빈 공간
          const SizedBox(width: 88),
          // 로고 (가운데)
          Expanded(
            child: Center(
              child: Image.asset(
                'assets/logo2.png',
                height: 54,
                fit: BoxFit.contain,
                errorBuilder: (_, __, ___) {
                  return const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        LucideIcons.dog,
                        color: AppColors.brandOrange,
                        size: 30,
                      ),
                      SizedBox(width: 6),
                      Text(
                        '위드독',
                        style: TextStyle(
                          fontSize: 28,
                          color: AppColors.brandOrange,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ),
          // 구독패스 왕관 아이콘
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => const SubscriptionPassPage(),
                ),
              );
            },
            child: const SizedBox(
              width: 44,
              height: 44,
              child: Icon(
                LucideIcons.crown,
                size: 22,
                color: AppColors.darkBrown,
              ),
            ),
          ),
          // 알림 벨 아이콘
          GestureDetector(
            onTap: () {
              showModalBottomSheet<void>(
                context: context,
                isScrollControlled: true,
                backgroundColor: Colors.transparent,
                builder: (_) => const NotificationSheet(),
              );
            },
            child: SizedBox(
              width: 44,
              height: 44,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  const Icon(
                    LucideIcons.bell,
                    size: 24,
                    color: AppColors.darkBrown,
                  ),
                  // 빨간 점 (읽지 않은 알림 있을 때)
                  if (unreadCount > 0)
                    Positioned(
                      top: 8,
                      right: 8,
                      child: Container(
                        width: 9,
                        height: 9,
                        decoration: BoxDecoration(
                          color: const Color(0xFFEF4444),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 1.5),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _IntroVideoCarousel extends StatelessWidget {
  const _IntroVideoCarousel({
    required this.banners,
    required this.controllers,
    required this.pageController,
    required this.currentPage,
    required this.currentIndex,
    required this.videosReady,
    required this.videoFailed,
    required this.videoErrorMessage,
    required this.onPageChanged,
    required this.onButtonTap,
  });

  final List<_IntroBannerData> banners;
  final List<VideoPlayerController> controllers;
  final PageController pageController;
  final int currentPage;
  final int currentIndex;
  final bool videosReady;
  final bool videoFailed;
  final String? videoErrorMessage;
  final ValueChanged<int> onPageChanged;
  final ValueChanged<_IntroBannerTarget> onButtonTap;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 400,
      width: double.infinity,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(26),
        child: Stack(
          fit: StackFit.expand,
          children: [
            PageView.builder(
              controller: pageController,
              onPageChanged: onPageChanged,
              itemBuilder: (context, pageIndex) {
                final bannerIndex = pageIndex % banners.length;
                final banner = banners[bannerIndex];

                return _IntroVideoCard(
                  controller: controllers[bannerIndex],
                  assetPath: banner.videoPath,
                  videosReady: videosReady,
                  videoFailed: videoFailed,
                  videoErrorMessage: videoErrorMessage,
                  buttonText: banner.buttonText,
                  onButtonTap: () => onButtonTap(banner.target),
                );
              },
            ),
            Positioned(
              left: 10,
              top: 0,
              bottom: 0,
              child: _BannerArrowButton(
                icon: Icons.chevron_left_rounded,
                onTap: () {
                  pageController.animateToPage(
                    currentPage - 1,
                    duration: const Duration(milliseconds: 420),
                    curve: Curves.easeOutCubic,
                  );
                },
              ),
            ),
            Positioned(
              right: 10,
              top: 0,
              bottom: 0,
              child: _BannerArrowButton(
                icon: Icons.chevron_right_rounded,
                onTap: () {
                  pageController.animateToPage(
                    currentPage + 1,
                    duration: const Duration(milliseconds: 420),
                    curve: Curves.easeOutCubic,
                  );
                },
              ),
            ),
            Positioned(
              left: 0,
              right: 0,
              bottom: 14,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(
                  banners.length,
                      (index) => _BannerDot(active: index == currentIndex),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _IntroVideoCard extends StatelessWidget {
  const _IntroVideoCard({
    required this.controller,
    required this.assetPath,
    required this.videosReady,
    required this.videoFailed,
    required this.videoErrorMessage,
    required this.buttonText,
    required this.onButtonTap,
  });

  final VideoPlayerController controller;
  final String assetPath;
  final bool videosReady;
  final bool videoFailed;
  final String? videoErrorMessage;
  final String buttonText;
  final VoidCallback onButtonTap;

  @override
  Widget build(BuildContext context) {
    final canPlay =
        videosReady && !videoFailed && controller.value.isInitialized;

    return Stack(
      fit: StackFit.expand,
      children: [
        if (canPlay)
          Transform.scale(
            scale: 1.5,
            child: FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: controller.value.size.width,
                height: controller.value.size.height,
                child: VideoPlayer(controller),
              ),
            ),
          )
        else
          _IntroFallback(
            assetPath: assetPath,
            videoFailed: videoFailed,
            errorMessage: videoErrorMessage,
          ),
        Positioned.fill(
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  Colors.transparent,
                  Colors.black.withOpacity(0.10),
                ],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
        ),
        Align(
          alignment: const Alignment(0, 0.72),
          child: GestureDetector(
            onTap: onButtonTap,
            child: Container(
              padding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 12,
              ),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.96),
                borderRadius: BorderRadius.circular(999),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.13),
                    blurRadius: 14,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: Text(
                buttonText,
                style: const TextStyle(
                  fontSize: 14,
                  color: AppColors.darkBrown,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _IntroFallback extends StatelessWidget {
  const _IntroFallback({
    required this.assetPath,
    required this.videoFailed,
    required this.errorMessage,
  });

  final String assetPath;
  final bool videoFailed;
  final String? errorMessage;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFFFFF7EF),
      child: Stack(
        children: [
          Positioned(
            right: -38,
            bottom: -42,
            child: Container(
              width: 180,
              height: 180,
              decoration: BoxDecoration(
                color: AppColors.peach.withOpacity(0.75),
                shape: BoxShape.circle,
              ),
            ),
          ),
          Positioned(
            left: -40,
            top: -50,
            child: Container(
              width: 150,
              height: 150,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.8),
                shape: BoxShape.circle,
              ),
            ),
          ),
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 26),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Image.asset(
                    'assets/logo2.png',
                    width: 72,
                    height: 72,
                    fit: BoxFit.contain,
                    errorBuilder: (_, __, ___) {
                      return const Icon(
                        LucideIcons.dog,
                        color: AppColors.brandOrange,
                        size: 56,
                      );
                    },
                  ),
                  const SizedBox(height: 12),
                  Text(
                    videoFailed ? '배너 영상을 불러오지 못했어요' : '배너 영상을 준비 중이에요',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 15,
                      color: AppColors.darkBrown,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    videoFailed ? '경로 확인: $assetPath' : '잠시만 기다려주세요',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.subBrown2,
                    ),
                  ),
                  if (videoFailed && errorMessage != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      errorMessage!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 10,
                        color: AppColors.mutedForeground,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BannerArrowButton extends StatelessWidget {
  const _BannerArrowButton({
    required this.icon,
    required this.onTap,
  });

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.20),
            shape: BoxShape.circle,
          ),
          child: Icon(
            icon,
            color: Colors.white,
            size: 22,
          ),
        ),
      ),
    );
  }
}

class _BannerDot extends StatelessWidget {
  const _BannerDot({required this.active});

  final bool active;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      width: active ? 18 : 7,
      height: 7,
      margin: const EdgeInsets.symmetric(horizontal: 3),
      decoration: BoxDecoration(
        color: active ? Colors.white : Colors.white.withOpacity(0.55),
        borderRadius: BorderRadius.circular(999),
        boxShadow: active
            ? [
          BoxShadow(
            color: Colors.black.withOpacity(0.12),
            blurRadius: 4,
          ),
        ]
            : null,
      ),
    );
  }
}

class _QuickChatBar extends StatefulWidget {
  const _QuickChatBar({required this.onSend});

  final ValueChanged<String> onSend;

  @override
  State<_QuickChatBar> createState() => _QuickChatBarState();
}

class _QuickChatBarState extends State<_QuickChatBar> {
  final _ctrl = TextEditingController();

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _handleSend() {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    widget.onSend(text);
    _ctrl.clear();
  }

  @override
  Widget build(BuildContext context) {
    const border = Color(0xFFFFD2C2);
    const primary = Color(0xFFFF7A4D);

    return Row(
      children: [
        // 챗봇 아이콘 (배경 없이, 크게)
        Image.asset(
          'assets/icon/chatbot_logo.png',
          width: 44,
          height: 44,
          errorBuilder: (_, __, ___) => const Icon(
            LucideIcons.messageCircle,
            color: AppColors.brandOrange,
            size: 40,
          ),
        ),
        const SizedBox(width: 8),
        // 입력창 — 챗봇 입력창과 동일한 pill 스타일
        Expanded(
          child: TextField(
            controller: _ctrl,
            textInputAction: TextInputAction.send,
            onSubmitted: (_) => _handleSend(),
            style: const TextStyle(fontSize: 14, color: AppColors.darkBrown),
            decoration: InputDecoration(
              hintText: '멍봇에게 물어보세요!',
              hintStyle: const TextStyle(
                fontSize: 14,
                color: AppColors.mutedForeground,
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 11,
              ),
              filled: true,
              fillColor: Colors.white,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24),
                borderSide: const BorderSide(color: border),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24),
                borderSide: const BorderSide(color: border),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24),
                borderSide: const BorderSide(color: primary, width: 1.5),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        // 전송 버튼
        GestureDetector(
          onTap: _handleSend,
          child: Container(
            width: 36,
            height: 36,
            decoration: const BoxDecoration(
              color: AppColors.brandOrange,
              shape: BoxShape.circle,
            ),
            alignment: Alignment.center,
            child: const Icon(
              LucideIcons.send,
              color: Colors.white,
              size: 18,
            ),
          ),
        ),
      ],
    );
  }
}

class _QuickMenuGrid extends StatelessWidget {
  const _QuickMenuGrid({
    required this.authenticated,
    required this.onPlaceTap,
    required this.onDiaryTap,
    required this.onChatTap,
    required this.onMyTap,
  });

  final bool authenticated;
  final VoidCallback onPlaceTap;
  final VoidCallback onDiaryTap;
  final VoidCallback onChatTap;
  final VoidCallback onMyTap;

  @override
  Widget build(BuildContext context) {
    final items = [
      _QuickMenuData(
        icon: LucideIcons.mapPin,
        label: 'AI 장소 추천',
        onTap: onPlaceTap,
      ),
      _QuickMenuData(
        icon: LucideIcons.bookOpen,
        label: '일기 쓰기',
        onTap: onDiaryTap,
      ),
      _QuickMenuData(
        icon: LucideIcons.messageCircle,
        label: 'AI 멍봇',
        onTap: onChatTap,
      ),
      _QuickMenuData(
        icon: LucideIcons.user,
        label: '마이페이지',
        onTap: onMyTap,
      ),
    ];

    return Row(
      children: [
        for (int i = 0; i < items.length; i++) ...[
          Expanded(child: _QuickMenuItem(data: items[i])),
          if (i != items.length - 1) const SizedBox(width: 9),
        ],
      ],
    );
  }
}

class _QuickMenuData {
  const _QuickMenuData({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
}

class _QuickMenuItem extends StatelessWidget {
  const _QuickMenuItem({required this.data});

  final _QuickMenuData data;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: data.onTap,
      borderRadius: BorderRadius.circular(16),
      child: Column(
        children: [
          Container(
            height: 72,
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: AppColors.beige),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.03),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            alignment: Alignment.center,
            child: Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: AppColors.peach,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: Icon(
                data.icon,
                color: AppColors.brandOrange,
                size: 22,
              ),
            ),
          ),
          const SizedBox(height: 7),
          Text(
            data.label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.darkBrown,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _FavoritePlacesPreviewSection extends ConsumerWidget {
  const _FavoritePlacesPreviewSection();

  /// 장소 탭 → 지도탭 포커싱
  void _goToMapWithFocus(WidgetRef ref, PlaceFavoriteItem item) {
    ref.read(mapFocusProvider.notifier).requestFocus(
      PlaceCard(
        name: item.name,
        contentId: item.contentId,
        subCategory: item.subCategory,
      ),
    );
    ref.read(homeTabIndexProvider.notifier).state = _mapTabIndex;
  }

  /// [즐겨찾기 장소] 헤더 / [더보기] → 지도탭 즐겨찾기 뷰
  void _goToMapFavorites(WidgetRef ref) {
    ref.read(mapShowFavoritesProvider.notifier).state = true;
    ref.read(homeTabIndexProvider.notifier).state = _mapTabIndex;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(favoritePlacesProvider);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 18),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(color: AppColors.beige),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: favorites.when(
        loading: () => const SizedBox(
          height: 150,
          child: Center(child: CircularProgressIndicator()),
        ),
        error: (error, _) => SizedBox(
          height: 150,
          child: Center(
            child: Text(
              '즐겨찾기 장소 로드 실패\n$error',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.destructive,
              ),
            ),
          ),
        ),
        data: (list) {
          final previewItems = list.take(3).toList();

          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _FavoriteSectionHeader(
                count: list.length,
                onMoreTap: () => _goToMapFavorites(ref),
              ),
              const SizedBox(height: 14),
              if (previewItems.isEmpty)
                const _EmptyFavoritePlaces()
              else ...[
                Column(
                  children: [
                    for (int i = 0; i < previewItems.length; i++) ...[
                      _FavoritePlacePreviewTile(
                        item: previewItems[i],
                        onTap: () => _goToMapWithFocus(ref, previewItems[i]),
                      ),
                      if (i != previewItems.length - 1)
                        const Divider(
                          height: 18,
                          color: Color(0xFFF3E3D8),
                        ),
                    ],
                  ],
                ),
                const Divider(height: 20, color: Color(0xFFF3E3D8)),
                Center(
                  child: TextButton.icon(
                    onPressed: () => _goToMapFavorites(ref),
                    icon: const Icon(LucideIcons.mapPin, size: 14),
                    label: const Text('더보기'),
                    style: TextButton.styleFrom(
                      foregroundColor: AppColors.brandOrange,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                    ),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _FavoriteSectionHeader extends StatelessWidget {
  const _FavoriteSectionHeader({
    required this.count,
    required this.onMoreTap,
  });

  final int count;
  final VoidCallback onMoreTap;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(
          LucideIcons.heart,
          color: AppColors.brandOrange,
          size: 20,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            count > 0 ? '즐겨찾기 장소' : '즐겨찾기 장소',
            style: const TextStyle(
              fontSize: 18,
              color: AppColors.darkBrown,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        InkWell(
          onTap: onMoreTap,
          borderRadius: BorderRadius.circular(999),
          child: const Padding(
            padding: EdgeInsets.all(4),
            child: Icon(
              LucideIcons.chevronRight,
              color: AppColors.mutedForeground,
              size: 20,
            ),
          ),
        ),
      ],
    );
  }
}

class _EmptyFavoritePlaces extends StatelessWidget {
  const _EmptyFavoritePlaces();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 146,
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Opacity(
              opacity: 0.32,
              child: Image.asset(
                'assets/logo.png',
                height: 56,
                errorBuilder: (_, __, ___) {
                  return const Icon(
                    LucideIcons.heart,
                    color: AppColors.brandOrange,
                    size: 44,
                  );
                },
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '아직 즐겨찾기한 장소가 없어요.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: AppColors.mutedForeground,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              '장소 카드의 ❤️ 토글로 추가해보세요.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12,
                color: AppColors.mutedForeground,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FavoritePlacePreviewTile extends StatelessWidget {
  const _FavoritePlacePreviewTile({
    required this.item,
    required this.onTap,
  });

  final PlaceFavoriteItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final subCategory = item.subCategory.trim();

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          vertical: 8,
          horizontal: 4,
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: AppColors.peach,
                shape: BoxShape.circle,
              ),
              alignment: Alignment.center,
              child: const Icon(
                Icons.favorite,
                color: AppColors.brandOrange,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 14,
                      color: AppColors.darkBrown,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  if (subCategory.isNotEmpty) ...[
                    const SizedBox(height: 3),
                    Text(
                      subCategory,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.mutedForeground,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const Icon(
              LucideIcons.chevronRight,
              color: AppColors.mutedForeground,
              size: 18,
            ),
          ],
        ),
      ),
    );
  }
}

/// 구독패스 안내 페이지 — 홈 헤더 왕관 아이콘 탭 시 표시.
class SubscriptionPassPage extends StatelessWidget {
  const SubscriptionPassPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9F5F0),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(LucideIcons.x, color: AppColors.darkBrown),
          onPressed: () => Navigator.of(context).pop(),
        ),
        centerTitle: true,
        title: const Text(
          '구독패스',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: AppColors.darkBrown,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
        child: Column(
          children: [
            // ── 현재 구독 상태 ──
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFFFF7ED), Color(0xFFFFEDD5)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.beige),
              ),
              child: Column(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: const BoxDecoration(
                      color: Color(0xFFE8F5E9),
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: const Icon(
                      LucideIcons.leaf,
                      color: Color(0xFF43A047),
                      size: 28,
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    '현재 무료 플랜 이용 중',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: AppColors.darkBrown,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    '업그레이드하고 더 많은 기능을 즐겨보세요!',
                    style: TextStyle(
                      fontSize: 13,
                      color: AppColors.subBrown,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            // ── 티어 카드 목록 ──
            _SubscriptionCard(
              tier: '무료',
              price: '₩0 / 월',
              color: const Color(0xFF43A047),
              bgColor: const Color(0xFFE8F5E9),
              icon: LucideIcons.leaf,
              features: const [
                'AI 일기 월 5회',
                'AI 그림 월 2회',
                '기본 산책 지도',
              ],
              isActive: true,
            ),
            const SizedBox(height: 12),
            _SubscriptionCard(
              tier: '프리미엄',
              price: '₩4,900 / 월',
              color: AppColors.brandOrange,
              bgColor: const Color(0xFFFFF5EE),
              icon: LucideIcons.zap,
              features: const [
                'AI 일기 무제한',
                'AI 그림 월 30회',
                '사진 일러스트 변환',
              ],
              isActive: false,
            ),
            const SizedBox(height: 12),
            _SubscriptionCard(
              tier: '프로',
              price: '₩9,900 / 월',
              color: const Color(0xFF7B1FA2),
              bgColor: const Color(0xFFF3E5F5),
              icon: LucideIcons.gem,
              features: const [
                '모든 프리미엄 기능',
                'AI 그림 무제한',
                '우선 응답 · 광고 제거',
              ],
              isActive: false,
            ),
            const SizedBox(height: 24),
            // ── 업그레이드 버튼 ──
            SizedBox(
              width: double.infinity,
              height: 50,
              child: FilledButton(
                onPressed: () {
                  // TODO: 결제 플로우 연결
                },
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.brandOrange,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: const Text(
                  '업그레이드하기',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SubscriptionCard extends StatelessWidget {
  const _SubscriptionCard({
    required this.tier,
    required this.price,
    required this.color,
    required this.bgColor,
    required this.icon,
    required this.features,
    required this.isActive,
  });

  final String tier;
  final String price;
  final Color color;
  final Color bgColor;
  final IconData icon;
  final List<String> features;
  final bool isActive;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isActive ? color : color.withOpacity(0.3),
          width: isActive ? 2 : 1,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 아이콘
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: color.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            alignment: Alignment.center,
            child: Icon(icon, size: 20, color: color),
          ),
          const SizedBox(width: 14),
          // 내용
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      tier,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: color,
                      ),
                    ),
                    if (isActive) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: color.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          '현재 이용 중',
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                            color: color,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  price,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: color.withOpacity(0.8),
                  ),
                ),
                const SizedBox(height: 10),
                ...features.map(
                  (f) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      children: [
                        Icon(LucideIcons.check, size: 14, color: color),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            f,
                            style: TextStyle(
                              fontSize: 13,
                              color: color.withOpacity(0.9),
                              height: 1.3,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}