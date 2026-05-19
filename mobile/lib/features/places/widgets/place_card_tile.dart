import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/place.dart';
import '../../chat/chat_providers.dart';
import '../../home/home_tab_index.dart';
import '../place_providers.dart';
import 'facility_modal_sheet.dart';

/// 챗봇 응답 / 지도 검색 결과 / 즐겨찾기 그리드 공용 카드.
///
/// - 좌측: `imageUrl` 또는 placeholder
/// - 우측 상단: ❤️ 토글 (옵티미스틱 UI, 사용자 결정 #2)
/// - 클릭: `GET /api/places/by-name` 모달 시트 (UI 디테일 #4)
class PlaceCardTile extends ConsumerWidget {
  const PlaceCardTile({super.key, required this.place, this.onNameTap});

  final PlaceCard place;

  /// 카드 본문(이미지+이름+상세) 영역 탭 시 호출. 미지정 시 시설정보 모달 오픈.
  /// 챗봇 응답 카드에서 지도 탭으로 라우팅용 (Bug #6, 2026-05-04).
  final VoidCallback? onNameTap;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favorites = ref.watch(favoriteContentIdsProvider);
    final isFavorite = favorites.contains(place.contentId);
    final image = place.imageUrl;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        children: [
          InkWell(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(10)),
            onTap: () =>
                onNameTap != null ? onNameTap!() : _openFacilityModal(context),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: SizedBox(
                      width: 80,
                      height: 80,
                      child: image == null
                          ? Container(
                              color: AppColors.peach,
                              alignment: Alignment.center,
                              child: const Icon(
                                LucideIcons.mapPin,
                                color: AppColors.brandOrange,
                              ),
                            )
                          : Image.network(
                              image,
                              fit: BoxFit.cover,
                              errorBuilder: (_, _, _) => Container(
                                color: AppColors.peach,
                                alignment: Alignment.center,
                                child: const Icon(
                                  LucideIcons.image,
                                  color: AppColors.brandOrange,
                                ),
                              ),
                            ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          place.name,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: AppColors.darkBrown,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        if (place.address.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 2),
                            child: Text(
                              place.address,
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.mutedForeground,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        if (place.reason.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              place.reason,
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.subBrown,
                                height: 1.4,
                              ),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        if (place.subCategory.isNotEmpty ||
                            place.indoor.isNotEmpty ||
                            place.outdoor.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Wrap(
                              spacing: 4,
                              runSpacing: 4,
                              children: [
                                if (place.subCategory.isNotEmpty)
                                  _Tag(text: place.subCategory),
                                if (place.indoor == 'Y')
                                  const _Tag(text: '실내 가능'),
                                if (place.outdoor == 'Y')
                                  const _Tag(text: '실외 가능'),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: isFavorite ? '즐겨찾기 해제' : '즐겨찾기 추가',
                    icon: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 180),
                      child: Icon(
                        isFavorite ? Icons.favorite : Icons.favorite_border,
                        key: ValueKey(isFavorite),
                        color: isFavorite
                            ? AppColors.brandOrange
                            : AppColors.mutedForeground,
                        size: 20,
                      ),
                    ),
                    onPressed: () => _toggleFavorite(ref, isFavorite),
                  ),
                ],
              ),
            ),
          ),
          const Divider(height: 1, color: AppColors.beige),
          InkWell(
            borderRadius: const BorderRadius.vertical(
              bottom: Radius.circular(10),
            ),
            onTap: () => _openDiaryDraft(ref),
            child: const Padding(
              padding: EdgeInsets.symmetric(vertical: 10, horizontal: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    LucideIcons.penTool,
                    size: 16,
                    color: AppColors.brandOrange,
                  ),
                  SizedBox(width: 6),
                  Text(
                    '이 장소로 일기 쓰기',
                    style: TextStyle(
                      fontSize: 13,
                      color: AppColors.brandOrange,
                      fontWeight: FontWeight.w600,
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

  void _openDiaryDraft(WidgetRef ref) {
    ref.read(pendingPlaceProvider.notifier).state = place;
    ref.read(homeTabIndexProvider.notifier).state = 4; // 챗봇 탭
  }

  Future<void> _toggleFavorite(WidgetRef ref, bool wasFavorite) async {
    if (place.contentId.isEmpty) {
      Fluttertoast.showToast(msg: '즐겨찾기 가능한 장소가 아닙니다 (content_id 없음)');
      return;
    }
    try {
      await ref
          .read(favoriteContentIdsProvider.notifier)
          .toggle(place.contentId);
      ref.invalidate(favoritePlacesProvider);
      Fluttertoast.showToast(
        msg: wasFavorite ? '즐겨찾기에서 제거됐어요' : '즐겨찾기에 추가됐어요',
      );
    } catch (e) {
      Fluttertoast.showToast(msg: '즐겨찾기 토글 실패: $e');
    }
  }

  void _openFacilityModal(BuildContext context) {
    if (place.contentId.isEmpty && place.name.isEmpty) return;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) =>
          FacilityModalSheet(name: place.name, imageUrl: place.imageUrl),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.peach,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 10,
          color: AppColors.brandOrange,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
