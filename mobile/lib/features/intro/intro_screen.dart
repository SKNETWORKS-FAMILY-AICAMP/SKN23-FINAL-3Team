import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:smooth_page_indicator/smooth_page_indicator.dart';

import '../../core/router/app_router.dart';
import '../../core/theme/app_colors.dart';
import 'intro_data.dart';

/// SharedPreferences 키 — 앱 소개 온보딩 완료 여부.
const introCompletedKey = 'intro_completed';

/// 홈 화면 위에 카드 형태로 보여줄 앱 소개 다이얼로그.
///
/// [showIntroDialog] 를 호출하여 사용.
Future<void> showIntroDialog(BuildContext context) {
  return showDialog<void>(
    context: context,
    barrierDismissible: false,
    barrierColor: Colors.black54,
    builder: (_) => const _IntroDialog(),
  );
}

class _IntroDialog extends ConsumerStatefulWidget {
  const _IntroDialog();

  @override
  ConsumerState<_IntroDialog> createState() => _IntroDialogState();
}

class _IntroDialogState extends ConsumerState<_IntroDialog> {
  final _controller = PageController();
  int _currentPage = 0;

  bool get _isLastPage => _currentPage == introImages.length - 1;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _complete() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(introCompletedKey, true);
    ref.read(introCompletedProvider.notifier).state = true;
    if (mounted) Navigator.of(context).pop();
  }

  void _next() {
    _controller.nextPage(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
    );
  }

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;

    return Center(
      child: Container(
        width: double.infinity,
        height: screenHeight * 0.82,
        margin: const EdgeInsets.symmetric(horizontal: 40),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.15),
              blurRadius: 24,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(28),
          clipBehavior: Clip.antiAlias,
          child: Column(
            children: [
              // ── 건너뛰기 ──────────────────────────
              Align(
                alignment: Alignment.centerRight,
                child: Padding(
                  padding: const EdgeInsets.only(top: 8, right: 8),
                  child: _isLastPage
                      ? const SizedBox(height: 36)
                      : TextButton(
                          onPressed: _complete,
                          child: const Text(
                            '건너뛰기',
                            style: TextStyle(
                              color: AppColors.subBrown,
                              fontSize: 13,
                            ),
                          ),
                        ),
                ),
              ),

              // ── 이미지 슬라이드 ──────────────────────────
              Expanded(
                child: PageView.builder(
                  controller: _controller,
                  itemCount: introImages.length,
                  onPageChanged: (i) => setState(() => _currentPage = i),
                  itemBuilder: (_, i) => Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Image.asset(
                      introImages[i],
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
              ),

              // ── 인디케이터 ────────────────────────
              Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: SmoothPageIndicator(
                  controller: _controller,
                  count: introImages.length,
                  effect: WormEffect(
                    dotHeight: 7,
                    dotWidth: 7,
                    spacing: 8,
                    activeDotColor: AppColors.brandOrange,
                    dotColor: AppColors.beige,
                  ),
                ),
              ),

              // ── 하단 버튼 ─────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                child: SizedBox(
                  width: double.infinity,
                  height: 46,
                  child: FilledButton(
                    onPressed: _isLastPage ? _complete : _next,
                    child: Text(
                      _isLastPage ? '시작하기' : '다음',
                      style: const TextStyle(fontSize: 15),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
