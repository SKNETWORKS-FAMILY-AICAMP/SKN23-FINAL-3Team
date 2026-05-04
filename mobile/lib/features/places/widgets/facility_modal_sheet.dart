import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../../core/theme/app_colors.dart';
import '../../../shared/models/place.dart';
import '../place_providers.dart';

/// `GET /api/places/by-name?name=` 결과를 시트로 표시.
///
/// UI 디테일 #4 (사용자 결정 2026-05-03): `showModalBottomSheet isScrollControlled: true`
/// 90% 높이. 큰 일러스트(향후) + 본문 + 태그 2종 + 운영시간·주차·반려견 정보.
///
/// `imageUrl` 우선 (호출자가 PlaceCard.firstimage 등 보유 시 전달) — 없으면
/// placeholder. `/by-name` 응답의 FacilityCard 스키마는 image 필드가 없어
/// 이미지를 별도 source 로 받는 구조 (Bug #3, 2026-05-04 저녁).
class FacilityModalSheet extends ConsumerWidget {
  const FacilityModalSheet({
    super.key,
    required this.name,
    this.imageUrl,
  });

  final String name;
  final String? imageUrl;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, scrollController) {
        final future = ref.read(placeApiProvider).byName(name);
        return FutureBuilder<FacilityCard>(
          future: future,
          builder: (_, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return _ErrorView(
                message: '시설 정보를 불러오지 못했습니다.\n${snapshot.error}',
                onClose: () => Navigator.of(context).pop(),
              );
            }
            final facility = snapshot.data!;
            return _Body(
              facility: facility,
              imageUrl: imageUrl,
              scrollController: scrollController,
              onClose: () => Navigator.of(context).pop(),
            );
          },
        );
      },
    );
  }
}

class _Body extends StatelessWidget {
  const _Body({
    required this.facility,
    required this.imageUrl,
    required this.scrollController,
    required this.onClose,
  });

  final FacilityCard facility;
  final String? imageUrl;
  final ScrollController scrollController;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 12, 4),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  facility.name,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppColors.darkBrown,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(LucideIcons.x),
                onPressed: onClose,
              ),
            ],
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            controller: scrollController,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Bug #3 — 상단 장소 이미지. URL 없으면 🐾 placeholder
                _HeaderImage(imageUrl: imageUrl),
                const SizedBox(height: 12),
                if (facility.address.isNotEmpty)
                  _Row(icon: LucideIcons.mapPin, text: facility.address),
                if (facility.tel.isNotEmpty)
                  _Row(icon: LucideIcons.phone, text: facility.tel),
                if (facility.operation.isNotEmpty)
                  _Row(icon: LucideIcons.clock, text: facility.operation),
                if (facility.hasParking == 'Y')
                  const _Row(icon: LucideIcons.car, text: '주차 가능'),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    if (facility.subCategory.isNotEmpty)
                      _Chip(text: facility.subCategory),
                    if (facility.indoor == 'Y') const _Chip(text: '실내 가능'),
                    if (facility.outdoor == 'Y') const _Chip(text: '실외 가능'),
                  ],
                ),
                if (facility.conditions.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Text(
                    '반려견 이용 조건',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.subBrown2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    facility.conditions,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.darkBrown,
                      height: 1.5,
                    ),
                  ),
                ],
                if (facility.description.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Text(
                    '장소 설명',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.subBrown2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    facility.description,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.darkBrown,
                      height: 1.6,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _HeaderImage extends StatelessWidget {
  const _HeaderImage({required this.imageUrl});

  final String? imageUrl;

  @override
  Widget build(BuildContext context) {
    final has = imageUrl != null && imageUrl!.isNotEmpty;
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: SizedBox(
        height: 200,
        width: double.infinity,
        child: has
            ? Image.network(
                imageUrl!,
                fit: BoxFit.cover,
                errorBuilder: (_, _, _) => const _ImagePlaceholder(),
              )
            : const _ImagePlaceholder(),
      ),
    );
  }
}

class _ImagePlaceholder extends StatelessWidget {
  const _ImagePlaceholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.peach,
      alignment: Alignment.center,
      child: const Text('🐾', style: TextStyle(fontSize: 48)),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: AppColors.brandOrange),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 13, color: AppColors.darkBrown),
            ),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.peach,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 11,
          color: AppColors.brandOrange,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onClose});

  final String message;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(LucideIcons.alertCircle, color: AppColors.destructive),
          const SizedBox(height: 12),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.subBrown2),
          ),
          const SizedBox(height: 16),
          OutlinedButton(onPressed: onClose, child: const Text('닫기')),
        ],
      ),
    );
  }
}
