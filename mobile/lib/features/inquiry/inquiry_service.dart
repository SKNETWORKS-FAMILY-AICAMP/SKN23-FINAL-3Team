import 'dart:convert';

import 'package:http/http.dart' as http;

/// Web3Forms Access Key — SKN23-FINAL-3Team/.env 의 WEB3FORMS_ACCESS_KEY 값.
const _accessKey = '8d63636c-5914-4409-b367-d88c2b4d64bc';

Future<bool> sendInquiry({
  required String name,
  required String email,
  required String message,
}) async {
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
