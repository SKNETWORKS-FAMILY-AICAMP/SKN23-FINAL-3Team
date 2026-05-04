import 'package:flutter_test/flutter_test.dart';
import 'package:withdog_app/shared/models/user.dart';
import 'package:withdog_app/shared/models/pet.dart';
import 'package:withdog_app/shared/models/enums.dart';
import 'package:withdog_app/shared/models/diary.dart';

void main() {
  group('User Model Tests', () {
    test('User.fromJson should parse correctly with primary pet', () {
      final json = {
        'id': 1,
        'email': 'test@example.com',
        'nickname': 'testuser',
        'gender': 'MALE',
        'birth_date': '1990-01-01',
        'profile_id': 10,
        'provider': 'kakao',
        'type_id': 1,
        'primary_pet_id': 100,
        'primary_pet': {
          'id': 100,
          'user_id': 1,
          'breed_id': 5,
          'name': 'Buddy',
          'birth_date': '2020-05-05',
          'gender': 'MALE',
          'is_neutered': true,
          'type_id': 1,
          'selected_tags': ['friendly'],
          'created_at': '2023-01-01T00:00:00Z',
          'updated_at': '2023-01-01T00:00:00Z',
          'age': 3,
        },
        'selected_tags': ['tag1'],
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'age': 34,
      };

      final user = User.fromJson(json);

      expect(user.id, 1);
      expect(user.email, 'test@example.com');
      expect(user.nickname, 'testuser');
      expect(user.gender, Gender.male);
      expect(user.primaryPet?.name, 'Buddy');
      expect(user.primaryPet?.gender, PetGender.male);
      expect(user.primaryPet?.isNeutered, true);
    });

    test('UserUpdate.toJson should omit null values', () {
      const update = UserUpdate(nickname: 'newname');
      final json = update.toJson();

      expect(json, {'nickname': 'newname'});
      expect(json.containsKey('gender'), isFalse);
    });
  });

  group('Pet Model Tests', () {
    test('Pet.fromJson should parse correctly', () {
      final json = {
        'id': 100,
        'user_id': 1,
        'breed_id': 5,
        'name': 'Buddy',
        'birth_date': '2020-05-05',
        'gender': 'FEMALE',
        'is_neutered': false,
        'type_id': 1,
        'selected_tags': ['active'],
        'created_at': '2023-01-01T00:00:00Z',
        'updated_at': '2023-01-01T00:00:00Z',
        'age': 3,
      };

      final pet = Pet.fromJson(json);

      expect(pet.id, 100);
      expect(pet.name, 'Buddy');
      expect(pet.gender, PetGender.female);
      expect(pet.isNeutered, false);
    });

    test('PetCreate.toJson should format dates correctly', () {
      final create = PetCreate(
        breedId: 5,
        name: 'Buddy',
        birthDate: DateTime(2020, 5, 5),
        gender: PetGender.male,
      );
      final json = create.toJson();

      expect(json['name'], 'Buddy');
      expect(json['birth_date'], '2020-05-05');
      expect(json['gender'], 'MALE');
    });
  });

  group('Diary Model Tests', () {
    test('Diary.fromJson should parse correctly', () {
      final json = {
        'id': 500,
        'user_id': 1,
        'pet_id': 100,
        'title': 'Good Day',
        'content': 'Had fun with Buddy.',
        'diary_date': '2023-05-04',
        'is_favorite': true,
        'emotion': 'happy',
        'created_at': '2023-05-04T10:00:00Z',
        'updated_at': '2023-05-04T10:00:00Z',
      };

      final diary = Diary.fromJson(json);

      expect(diary.id, 500);
      expect(diary.title, 'Good Day');
      expect(diary.isFavorite, true);
      expect(diary.diaryDate.year, 2023);
      expect(diary.diaryDate.month, 5);
      expect(diary.diaryDate.day, 4);
    });

    test('FavoriteCalendar.fromJson should parse items', () {
      final json = {
        'year': 2023,
        'month': 5,
        'items': [
          {'date': '2023-05-04', 'diary_id': 500, 'emotion': 'happy'}
        ]
      };

      final calendar = FavoriteCalendar.fromJson(json);

      expect(calendar.year, 2023);
      expect(calendar.items.length, 1);
      expect(calendar.items.first.diaryId, 500);
      expect(calendar.items.first.emotion, 'happy');
    });
  });
}
