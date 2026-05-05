/// 백엔드 `schemas/keyword.py KeywordResponse` 와 1:1.
/// `category` = "PET" | "USER".
class Keyword {
  const Keyword({
    required this.id,
    required this.category,
    required this.name,
    this.description,
  });

  final int id;
  final String category;
  final String name;
  final String? description;

  factory Keyword.fromJson(Map<String, dynamic> json) {
    return Keyword(
      id: json['id'] as int,
      category: json['category'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
    );
  }
}
