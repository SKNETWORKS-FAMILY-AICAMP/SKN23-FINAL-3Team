import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../intro_data.dart';

/// 앱 소개 온보딩 슬라이드 1장 — 풀스크린.
class IntroPage extends StatelessWidget {
  const IntroPage({super.key, required this.data});

  final IntroPageData data;

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 28),
      child: Column(
        children: [
          // ── 상단 일러스트 영역 (화면 45%) ──────────────
          SizedBox(
            height: screenHeight * 0.45,
            child: Center(
              child: data.assetPath != null
                  ? Image.asset(
                      data.assetPath!,
                      width: 240,
                      height: 240,
                      fit: BoxFit.contain,
                    )
                  : Icon(
                      data.placeholderIcon,
                      size: data.iconSize,
                      color: AppColors.brandOrange,
                    ),
            ),
          ),

          // ── 제목 ────────────────────────────────────────────
          Text(
            data.title,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: AppColors.darkBrown,
              height: 1.35,
            ),
          ),
          const SizedBox(height: 16),

          // ── 부제 또는 체크리스트 ────────────────────────────
          if (data.subtitle != null)
            Text(
              data.subtitle!,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                color: AppColors.subBrown,
                height: 1.5,
              ),
            ),
          if (data.checkItems.isNotEmpty)
            Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                for (final item in data.checkItems)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 5),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.check_circle,
                          size: 20,
                          color: AppColors.brandOrange,
                        ),
                        const SizedBox(width: 10),
                        Flexible(
                          child: Text(
                            item,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 14,
                              color: AppColors.subBrown,
                              height: 1.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
        ],
      ),
    );
  }
}
