import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../shared/models/breed.dart';
import '../../shared/models/keyword.dart';
import '../../shared/models/pet.dart';
import '../auth/auth_providers.dart';
import 'breed_api.dart';
import 'image_api.dart';
import 'keyword_api.dart';
import 'pet_api.dart';
import 'user_api.dart';

final breedApiProvider = Provider<BreedApi>((ref) {
  return BreedApi(ref.watch(apiClientProvider));
});

final keywordApiProvider = Provider<KeywordApi>((ref) {
  return KeywordApi(ref.watch(apiClientProvider));
});

final petApiProvider = Provider<PetApi>((ref) {
  return PetApi(ref.watch(apiClientProvider));
});

final imageApiProvider = Provider<ImageApi>((ref) {
  return ImageApi(ref.watch(apiClientProvider));
});

final userApiProvider = Provider<UserApi>((ref) {
  return UserApi(ref.watch(apiClientProvider));
});

/// 인기 견종 목록 (`GET /api/breeds?top10=true`)
/// 온보딩 Step2Page의 빠른 선택 칩 용도.
final popularBreedsProvider = FutureProvider<List<Breed>>((ref) async {
  return ref.read(breedApiProvider).list(top10: true);
});

/// 전체 견종 목록 (`GET /api/breeds`)
/// 견종 선택 모달, 드롭다운, 전체 목록 화면 용도.
final allBreedsProvider = FutureProvider<List<Breed>>((ref) async {
  return ref.read(breedApiProvider).list();
});

/// 견종 검색 (`GET /api/breeds?search=검색어`)
/// 검색어가 비어 있으면 전체 견종 목록을 반환.
final breedSearchProvider = FutureProvider.autoDispose
    .family<List<Breed>, String>((ref, query) async {
      final keyword = query.trim();

      if (keyword.isEmpty) {
        return ref.read(breedApiProvider).list();
      }

      return ref.read(breedApiProvider).list(search: keyword);
    });

/// 보호자 라이프스타일 (`GET /api/keywords?category=USER`)
/// autoDispose: 실패 시 모달/화면 재진입만으로 재시도 가능.
final userKeywordsProvider = FutureProvider.autoDispose<List<Keyword>>((ref) async {
  return ref.read(keywordApiProvider).list(KeywordCategory.user);
});

/// 반려견 성격 (`GET /api/keywords?category=PET`)
/// autoDispose: 실패 시 모달/화면 재진입만으로 재시도 가능.
final petKeywordsProvider = FutureProvider.autoDispose<List<Keyword>>((ref) async {
  return ref.read(keywordApiProvider).list(KeywordCategory.pet);
});

/// MyPage 반려견 목록 그리드
/// `GET /api/pets?user_id=`
final userPetsProvider = FutureProvider.autoDispose<List<Pet>>((ref) async {
  final auth = ref.watch(authProvider);

  if (auth is! AuthAuthenticated) {
    return const [];
  }

  return ref.read(petApiProvider).listByUser(auth.user.id);
});

/// 다이어리 이미지 URL
/// `GET /api/images/{id}` 응답의 `file_url`.
final diaryImageUrlProvider = FutureProvider.autoDispose.family<String?, int>((
  ref,
  imageId,
) async {
  if (imageId <= 0) {
    return null;
  }

  final meta = await ref.read(imageApiProvider).get(imageId);

  return meta.fileUrl.isEmpty ? null : meta.fileUrl;
});
