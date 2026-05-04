import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:withdog_app/features/auth/auth_api.dart';
import 'package:withdog_app/features/auth/auth_providers.dart';
import 'package:withdog_app/features/auth/oauth_provider.dart';
import 'package:withdog_app/shared/models/auth.dart';
import 'package:withdog_app/shared/models/user.dart';
import 'package:withdog_app/core/storage/secure_storage.dart';

class MockAuthApi extends Mock implements AuthApi {}
class MockSecureStorage extends Mock implements SecureStorageService {}

void main() {
  late MockAuthApi mockAuthApi;
  late MockSecureStorage mockSecureStorage;
  late ProviderContainer container;

  final testUser = User(
    id: 1,
    email: 'test@test.com',
    nickname: 'tester',
    provider: 'kakao',
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
  );

  setUp(() {
    mockAuthApi = MockAuthApi();
    mockSecureStorage = MockSecureStorage();
    
    container = ProviderContainer(
      overrides: [
        authApiProvider.overrideWith((ref) => mockAuthApi),
        secureStorageProvider.overrideWith((ref) => mockSecureStorage),
      ],
    );

    registerFallbackValue(OAuthProvider.kakao);

    // Default behaviors
    when(() => mockSecureStorage.readAccessToken()).thenAnswer((_) async => null);
    when(() => mockSecureStorage.writeAccessToken(any())).thenAnswer((_) async => {});
    when(() => mockSecureStorage.clearAccessToken()).thenAnswer((_) async => {});
  });

  tearDown(() {
    container.dispose();
  });

  group('AuthNotifier Tests', () {
    test('initial state should be AuthInitial', () {
      expect(container.read(authProvider), isA<AuthInitial>());
    });

    test('bootstrap should set unauthenticated if no token', () async {
      await container.read(authProvider.notifier).bootstrap();
      expect(container.read(authProvider), isA<AuthUnauthenticated>());
    });

    test('bootstrap should restore user if token exists', () async {
      when(() => mockSecureStorage.readAccessToken()).thenAnswer((_) async => 'valid_token');
      when(() => mockAuthApi.me()).thenAnswer((_) async => testUser);

      await container.read(authProvider.notifier).bootstrap();

      final state = container.read(authProvider);
      expect(state, isA<AuthAuthenticated>());
      expect((state as AuthAuthenticated).user.id, 1);
    });

    test('completeLogin should update state to authenticated', () async {
      when(() => mockAuthApi.exchangeCode(
        provider: any(named: 'provider'),
        code: any(named: 'code'),
        state: any(named: 'state'),
      )).thenAnswer((_) async => const AuthResponse(
        accessToken: 'new_token', 
        tokenType: 'bearer',
        isNewUser: true,
      ));
      when(() => mockAuthApi.me()).thenAnswer((_) async => testUser);

      await container.read(authProvider.notifier).completeLogin(
        provider: OAuthProvider.kakao,
        code: 'some_code',
        state: 'some_state',
      );

      final state = container.read(authProvider);
      expect(state, isA<AuthAuthenticated>());
      expect((state as AuthAuthenticated).isNewUser, true);
      verify(() => mockSecureStorage.writeAccessToken('new_token')).called(1);
    });

    test('logout should clear token and set unauthenticated', () async {
      await container.read(authProvider.notifier).logout();
      
      expect(container.read(authProvider), isA<AuthUnauthenticated>());
      verify(() => mockSecureStorage.clearAccessToken()).called(1);
    });
  });
}
