import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/models/place.dart';
import 'diary_draft_view.dart';

/// 외부 진입 (장소 카드 "이 장소로 일기 쓰기") 풀스크린 라우트.
/// 챗봇 trigger 진입도 동일 화면으로 push 가능 (place 없이).
class DiaryDraftScreen extends ConsumerWidget {
  const DiaryDraftScreen({super.key, this.contextPlace});

  final PlaceCard? contextPlace;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('새 그림일기'),
        backgroundColor: Colors.white,
        foregroundColor: AppColors.darkBrown,
        elevation: 0,
      ),
      body: DiaryDraftView(
        contextPlace: contextPlace,
        onCompleted: () {
          if (context.canPop()) context.pop();
        },
      ),
    );
  }
}
