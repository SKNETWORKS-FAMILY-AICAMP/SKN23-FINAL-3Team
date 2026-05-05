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

/// 인기 견종 8종 (`/breeds?top10=true`) — Step2Page 칩
final popularBreedsProvider = FutureProvider<List<Breed>>((ref) async {
  return ref.read(breedApiProvider).list(top10: true);
});

/// 전체 견종 (`/breeds`) — Pet edit modal 의 breed 변경 dropdown 용.
final allBreedsProvider = FutureProvider<List<Breed>>((ref) async {
  return ref.read(breedApiProvider).list();
});

/// 보호자 라이프스타일 (`/keywords?category=USER`) — max 5
final userKeywordsProvider = FutureProvider<List<Keyword>>((ref) async {
  return ref.read(keywordApiProvider).list(KeywordCategory.user);
});

/// 반려견 성격 (`/keywords?category=PET`) — max 5
final petKeywordsProvider = FutureProvider<List<Keyword>>((ref) async {
  return ref.read(keywordApiProvider).list(KeywordCategory.pet);
});

/// MyPage 반려견 목록 그리드 — `GET /api/pets?user_id=`. 인증 변경 시 자동 invalidate.
final userPetsProvider = FutureProvider.autoDispose<List<Pet>>((ref) async {
  final auth = ref.watch(authProvider);
  if (auth is! AuthAuthenticated) return const [];
  return ref.read(petApiProvider).listByUser(auth.user.id);
});

/// 다이어리 이미지 URL — `GET /api/images/{id}` 응답의 `file_url`.
/// `family<imageId>` 캐시 — 같은 image 가 목록·상세에서 중복 fetch 안 되도록.
/// keepAlive 미설정 (autoDispose) — 메모리 절약.
final diaryImageUrlProvider =
    FutureProvider.autoDispose.family<String?, int>((ref, imageId) async {
  if (imageId <= 0) return null;
  final meta = await ref.read(imageApiProvider).get(imageId);
  return meta.fileUrl.isEmpty ? null : meta.fileUrl;
});
