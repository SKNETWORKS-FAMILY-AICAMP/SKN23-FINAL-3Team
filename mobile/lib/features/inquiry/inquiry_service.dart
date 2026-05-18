import 'dart:convert';

import 'package:http/http.dart' as http;

/// Web3Forms Access Key — 빌드 시 `--dart-define=WEB3FORMS_ACCESS_KEY=...` 로 주입.
/// 로컬 개발: `flutter run --dart-define=WEB3FORMS_ACCESS_KEY=<your-key>`
const _accessKey = String.fromEnvironment('WEB3FORMS_ACCESS_KEY');

Future<bool> sendInquiry({
  required String name,
  required String email,
  required String message,
}) async {
  if (_accessKey.isEmpty) {
    throw StateError(
      'WEB3FORMS_ACCESS_KEY 가 설정되지 않음. '
      '--dart-define=WEB3FORMS_ACCESS_KEY=... 빌드 플래그를 확인하세요.',
    );
  }
  final response = await http.post(
    Uri.parse('https://api.web3forms.com/submit'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'access_key': _accessKey,
      'name': name,
      'email': email,
      'message': message,
      'subject': '[위드독] 앱 문의가 도착했습니다',
    }),
  );
  return response.statusCode == 200;
}
