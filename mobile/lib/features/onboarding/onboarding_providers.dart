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
